#!/bin/bash
# PACE-ICE job: serve one model on one H200 and run the control experiments.
# Usage: sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml smoke|full|extended-smoke|extended
#   full:     original test split at B=384, with and without the hard cap
#   extended: hard-cap budgets 256 and 768, then fresh timelines with spread, early, and late compaction
#SBATCH -J ladl-exp
#SBATCH --account=ece --partition=coe-gpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8 --mem=64G
#SBATCH --gres=gpu:h200:1
#SBATCH -t 02:00:00
#SBATCH --exclude=atl1-1-03-014-16-0,atl1-1-03-014-9-0,atl1-1-03-015-9-0,atl1-1-03-017-16-0,atl1-1-03-018-2-0,atl1-1-03-017-30-0,atl1-1-03-015-23-0
#SBATCH --signal=B:TERM@180
#SBATCH -o logs/%x_%j.out
set -euo pipefail
CONFIG=${1:?config required}
MODE=${2:?mode must be smoke, full, extended-smoke, or extended}
cd "$SLURM_SUBMIT_DIR"
ROOT=$PWD
PY=$ROOT/.conda-env/bin/python
export HF_HOME=$ROOT/hf_home HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_USE_FLASHINFER_SAMPLER=0

read -r MODEL RUN PORT CACHE < <("$PY" -c "
import sys, yaml
from urllib.parse import urlparse
c = yaml.safe_load(open(sys.argv[1]))
print(c['model'], c['run_name'], urlparse(c['base_url']).port, c['cache'])" "$CONFIG")
CONDS=full,summary,pinning,chrono,typed_llm,lifecycle,lifecycle_gold,abl_noguard,abl_noreceipt,lifecycle_strict,lifecycle_nohint

refuse_existing() {
  if [ -e "$1" ]; then echo "refusing to overwrite $1"; exit 2; fi
}
case "$MODE" in
  full)
    refuse_existing "results/runs/$RUN-pace-nocap/probes_B384.jsonl"
    refuse_existing "results/runs/$RUN-pace-hardcap/probes_B384.jsonl" ;;
  extended)
    for B in 256 768; do refuse_existing "results/runs/$RUN-pace-hardcap/probes_B$B.jsonl"; done
    for P in spread early late; do refuse_existing "results/runs/$RUN-pace-fresh-$P/probes_B384.jsonl"; done ;;
  smoke|extended-smoke) ;;
  *) echo "unknown mode $MODE"; exit 2 ;;
esac

# SQLite WAL stays on node-local storage; the cache is copied back to project scratch on exit.
LOCAL=${TMPDIR:-/tmp}/ladl_$SLURM_JOB_ID
mkdir -p "$LOCAL" "$(dirname "$CACHE")" logs
LOCAL_CACHE=$LOCAL/$(basename "$CACHE")
[ -f "$CACHE" ] && cp "$CACHE" "$LOCAL_CACHE"
VLLM_PID=
save_cache() {
  [ -n "$VLLM_PID" ] && kill "$VLLM_PID" 2>/dev/null || true
  if [ -f "$LOCAL_CACHE" ]; then
    "$PY" -c "
import os, sqlite3, sys
src, dst = sys.argv[1:]
tmp = dst + '.tmp'
a, b = sqlite3.connect(src), sqlite3.connect(tmp)
a.backup(b); b.close(); a.close(); os.replace(tmp, dst)" "$LOCAL_CACHE" "$CACHE" && echo "cache saved to $CACHE"
  fi
}
trap save_cache EXIT
trap 'echo "time limit signal"; exit 143' TERM

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
"$PY" -c "
import sys
from src.llm.client import TokenCounter
assert TokenCounter(sys.argv[1]).tok is not None, 'tokenizer unavailable'" "$MODEL"

"$ROOT/.conda-env/bin/vllm" serve "$MODEL" --port "$PORT" --max-model-len 16384 \
  --gpu-memory-utilization 0.85 --seed 0 > "logs/vllm_${SLURM_JOB_ID}.log" 2>&1 &
VLLM_PID=$!
for _ in $(seq 1 180); do
  curl -sf "localhost:$PORT/v1/models" >/dev/null && break
  kill -0 "$VLLM_PID" 2>/dev/null || { echo "vLLM exited"; tail -30 "logs/vllm_${SLURM_JOB_ID}.log"; exit 3; }
  sleep 5
done
curl -sf "localhost:$PORT/v1/models" >/dev/null || { echo "vLLM did not start"; exit 3; }

run() {
  local name=$1; shift
  "$PY" -m src.eval.run --config "$CONFIG" --conditions "$CONDS" --cache "$LOCAL_CACHE" --run-name "$name" "$@"
}

START=$(date +%s)
case "$MODE" in
  smoke)
    run "$RUN-pace-smoke-nocap" --limit 2
    run "$RUN-pace-smoke-hardcap" --hard-cap --limit 2 ;;
  full)
    run "$RUN-pace-nocap"
    run "$RUN-pace-hardcap" --hard-cap ;;
  extended-smoke)
    run "$RUN-pace-smoke-ext-budget" --hard-cap --budget 256 --limit 2
    for P in spread early late; do
      run "$RUN-pace-smoke-ext-$P" --hard-cap --data "data/fresh/dialogues_$P.jsonl" --limit 2
    done ;;
  extended)
    for B in 256 768; do run "$RUN-pace-hardcap" --hard-cap --budget "$B"; done
    for P in spread early late; do
      run "$RUN-pace-fresh-$P" --hard-cap --data "data/fresh/dialogues_$P.jsonl"
    done ;;
esac
echo "elapsed minutes: $(( ($(date +%s) - START) / 60 ))"
