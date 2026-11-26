#!/bin/bash
# PACE-ICE job: serve one model on one H200 and run the control experiments.
# Usage: sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml MODE[,MODE...]
#   MODE is smoke, full, hardcap, extended-smoke, extended, dev, confirm-smoke, confirm, replicate, v2-robust,
#   followup-pilot, noise, swap, or latency.
#   Several modes run in order in one job and share one LLM cache.
#   CACHE_SUFFIX=name keeps this job's cache in a separate file, for jobs that run at the same time.
#   RUN_TAG=-name appends a tag to every run folder name.
#   SKIP_EXISTING=1 skips runs that already wrote probes, to finish a job that hit its time limit.
#   LIMIT=n runs only the first n dialogues. MAX_CONCURRENCY=n overrides concurrent requests. VLLM_BATCH_INVARIANT=0 turns off deterministic serving (default 1).
#   full:     original test split at B=384, with and without the hard cap
#   hardcap:  original test split at B=384 with the hard cap only
#   extended: hard-cap budgets 256 and 768, then fresh timelines with spread, early, and late compaction
#   dev:      dev split with extraction prompts v1 and v2, used only for prompt development
#   confirm:  new-language Confirm set with extraction prompts v1 and v2
#   replicate: frozen extraction v2 and hint-parity baselines on the original Test and Fresh sets
#   v2-robust: extraction v2 at budgets 256 and 768 on Test, and with early and late compaction on Fresh
#   The follow-up modes are described in docs/followup_experiments_plan.md and run on Confirm:
#   noise:    gold events with controlled extraction errors, 15 settings
#   swap:     this model decides with the other models' deterministic extractions (v1 and v2)
#   latency:  one request at a time, each condition from its own empty cache (use with LIMIT=8)
#   followup-pilot: three noise settings and one swap cell (use with LIMIT=8)
#   The scale, retrieval, and forged-update modes are described in docs/scale_retrieval_forgery_plan.md:
#   newconds: 7B models; retrieval baselines and the speaker check on Confirm and Test, and the forged-update set
#   scale:    larger models; a batch-invariance check on 8 dialogues, Confirm v1 and v2, and the forged-update set
#   LOCAL_WEIGHTS=1 downloads the pinned model to node-local disk for this job and deletes it at the end.
#SBATCH -J ladl-exp
#SBATCH --account=ece --partition=coe-gpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8 --mem=64G
#SBATCH --gres=gpu:h200:1
#SBATCH -t 02:00:00
#SBATCH --exclude=atl1-1-03-014-16-0,atl1-1-03-014-9-0,atl1-1-03-015-9-0,atl1-1-03-017-16-0,atl1-1-03-018-2-0,atl1-1-03-017-30-0,atl1-1-03-015-23-0,atl1-1-03-015-16-0
#SBATCH --signal=B:TERM@180
#SBATCH -o logs/%x_%j.out
set -euo pipefail
CONFIG=${1:?config required}
MODES=${2:?mode required}
cd "$SLURM_SUBMIT_DIR"
ROOT=$PWD
PY=$ROOT/.conda-env/bin/python
export HF_HOME=$ROOT/hf_home HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 VLLM_USE_FLASHINFER_SAMPLER=0
# Batch-invariant kernels make outputs independent of batching, so a rerun reproduces every response exactly.
# Runs before Nov 24, 2026 used VLLM_BATCH_INVARIANT=0; set it to 0 to repeat that setting.
export VLLM_BATCH_INVARIANT=${VLLM_BATCH_INVARIANT:-1}

read -r MODEL RUN PORT CACHE REV VLLM_ARGS < <("$PY" -c "
import sys, yaml
from urllib.parse import urlparse
c = yaml.safe_load(open(sys.argv[1]))
rev = (yaml.safe_load(open('configs/model_revisions.yaml')) or {}).get(c['model'])
assert rev, 'add the model to configs/model_revisions.yaml'
print(c['model'], c['run_name'], urlparse(c['base_url']).port, c['cache'], rev, c.get('vllm_args', ''))" "$CONFIG")
[ -n "${CACHE_SUFFIX:-}" ] && CACHE=${CACHE%.sqlite}_$CACHE_SUFFIX.sqlite
# RUN_TAG=-name writes to new run folders, for example a rerun without the cache.
BASE_RUN=$RUN
RUN=$RUN${RUN_TAG:-}
CONDS=full,summary,pinning,chrono,typed_llm,lifecycle,lifecycle_gold,abl_noguard,abl_noreceipt,lifecycle_strict,lifecycle_nohint
ALL_CONDS=$CONDS,summary_hint,pinning_hint,chrono_hint
V2_CONDS=chrono,chrono_hint,typed_llm,lifecycle,lifecycle_nohint,lifecycle_strict,abl_noguard,abl_noreceipt
FU_CONDS=$("$PY" -c "from src.eval.followup_settings import CONDITIONS; print(','.join(CONDITIONS))")
LATENCY_CONDS=$("$PY" -c "from src.eval.followup_settings import LATENCY_CONDITIONS; print(' '.join(LATENCY_CONDITIONS))")
CONFIRM=data/confirm/dialogues.jsonl
FORGED=data/forged/dialogues.jsonl
NEW_CONDS=recent,retrieval,summary_retrieval,lifecycle_source
FORGED_CONDS=full,summary,summary_hint,pinning,pinning_hint,chrono,chrono_hint,typed_llm,lifecycle,lifecycle_nohint,$NEW_CONDS
mapfile -t NOISE_SETTINGS < <("$PY" -m src.eval.followup_settings noise "$BASE_RUN")
mapfile -t SWAP_CELLS < <("$PY" -m src.eval.followup_settings swap "$BASE_RUN")
# Deterministic extraction of another model's Confirm run, used by the swap cells.
swap_source() { echo "results/runs/$1-det1-pace-confirm-$2/extractions.jsonl"; }

refuse_existing() {
  if [ -e "$1" ] && [ -z "${SKIP_EXISTING:-}" ]; then echo "refusing to overwrite $1"; exit 2; fi
}
check_mode() {
case "$1" in
  full)
    refuse_existing "results/runs/$RUN-pace-nocap/probes_B384.jsonl"
    refuse_existing "results/runs/$RUN-pace-hardcap/probes_B384.jsonl" ;;
  hardcap)
    refuse_existing "results/runs/$RUN-pace-hardcap/probes_B384.jsonl" ;;
  extended)
    for B in 256 768; do refuse_existing "results/runs/$RUN-pace-hardcap/probes_B$B.jsonl"; done
    for P in spread early late; do refuse_existing "results/runs/$RUN-pace-fresh-$P/probes_B384.jsonl"; done ;;
  confirm)
    for V in v1 v2; do refuse_existing "results/runs/$RUN-pace-confirm-$V/probes_B384.jsonl"; done ;;
  replicate)
    for D in test fresh; do for K in v2 hints; do refuse_existing "results/runs/$RUN-pace-replicate-$D-$K/probes_B384.jsonl"; done; done ;;
  v2-robust)
    for B in 256 768; do refuse_existing "results/runs/$RUN-pace-replicate-test-v2/probes_B$B.jsonl"; done
    for L in early late; do refuse_existing "results/runs/$RUN-pace-replicate-fresh-$L-v2/probes_B384.jsonl"; done ;;
  noise)
    [ "${#NOISE_SETTINGS[@]}" -eq 15 ] || { echo "no noise settings for $BASE_RUN"; exit 2; }
    for S in "${NOISE_SETTINGS[@]}"; do refuse_existing "results/runs/$RUN-pace-confirm-noise-${S%% *}/probes_B384.jsonl"; done ;;
  swap)
    [ "${#SWAP_CELLS[@]}" -eq 4 ] || { echo "no swap cells for $BASE_RUN"; exit 2; }
    for S in "${SWAP_CELLS[@]}"; do
      read -r NAME OTHER V <<< "$S"
      refuse_existing "results/runs/$RUN-pace-confirm-swap-$NAME/probes_B384.jsonl"
      [ -f "$(swap_source "$OTHER" "$V")" ] || { echo "missing $(swap_source "$OTHER" "$V")"; exit 2; }
    done ;;
  latency)
    [ -n "${LIMIT:-}" ] || { echo "latency needs LIMIT"; exit 2; }
    for C in $LATENCY_CONDS; do refuse_existing "results/runs/$RUN-pace-latency-$C/probes_B384.jsonl"; done ;;
  newconds)
    for R in confirm-new-v1 confirm-new-v2 test-new forged-v2; do refuse_existing "results/runs/$RUN-pace-$R/probes_B384.jsonl"; done
    for V in v1 v2; do [ -f "$(swap_source "$BASE_RUN" "$V")" ] || { echo "missing $(swap_source "$BASE_RUN" "$V")"; exit 2; }; done
    [ -f "results/runs/$BASE_RUN-det1-pace-hardcap/extractions.jsonl" ] || { echo "missing Test extraction"; exit 2; } ;;
  scale)
    [ -n "${LOCAL_WEIGHTS:-}" ] || { echo "scale needs LOCAL_WEIGHTS=1"; exit 2; }
    for R in confirm-v1 confirm-v2 forged-v2; do refuse_existing "results/runs/$RUN-pace-$R/probes_B384.jsonl"; done ;;
  followup-pilot)
    [ -n "${LIMIT:-}" ] || { echo "followup-pilot needs LIMIT"; exit 2; }
    [ -n "${RUN_TAG:-}" ] || { echo "followup-pilot needs RUN_TAG"; exit 2; } ;;
  smoke|extended-smoke|dev|confirm-smoke) ;;
  *) echo "unknown mode $1"; exit 2 ;;
esac
}
IFS=, read -ra MODE_LIST <<< "$MODES"
for MODE in "${MODE_LIST[@]}"; do check_mode "$MODE"; done

# SQLite WAL stays on node-local storage; the cache is copied back to project scratch on exit.
LOCAL=${TMPDIR:-/tmp}/ladl_$SLURM_JOB_ID
mkdir -p "$LOCAL" "$(dirname "$CACHE")" logs
LOCAL_CACHE=$LOCAL/$(basename "$CACHE")
[ -f "$CACHE" ] && cp "$CACHE" "$LOCAL_CACHE"
VLLM_PID=
copy_sqlite() {
  "$PY" -c "
import os, sqlite3, sys
src, dst = sys.argv[1:]
tmp = dst + '.tmp'
a, b = sqlite3.connect(src), sqlite3.connect(tmp)
a.backup(b); b.close(); a.close(); os.replace(tmp, dst)" "$1" "$2"
}
save_cache() {
  [ -n "$VLLM_PID" ] && kill "$VLLM_PID" 2>/dev/null || true
  if [ -f "$LOCAL_CACHE" ]; then
    copy_sqlite "$LOCAL_CACHE" "$CACHE" && echo "cache saved to $CACHE"
  fi
  if [ -n "${LOCAL_WEIGHTS:-}" ]; then rm -rf "$LOCAL/hf_home" && echo "local weights removed"; fi
}
trap save_cache EXIT
# Bash runs a trap only after a foreground child exits, so runs go to the background and the shell waits on them.
RUN_PID=
trap 'echo "time limit signal"; [ -n "$RUN_PID" ] && kill "$RUN_PID" 2>/dev/null; exit 143' TERM

nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo "VLLM_BATCH_INVARIANT=$VLLM_BATCH_INVARIANT"
if [ -n "${LOCAL_WEIGHTS:-}" ]; then
  # Project storage cannot hold the larger models, so this job fetches the pinned revision to node-local disk.
  export HF_HOME=$LOCAL/hf_home HF_HUB_OFFLINE=0 TRANSFORMERS_OFFLINE=0
  "$PY" - "$MODEL" "$REV" <<'PY'
import sys, time
from huggingface_hub import snapshot_download
t0 = time.time()
path = snapshot_download(sys.argv[1], revision=sys.argv[2],
                         ignore_patterns=["original/*", "*.pth", "*.bin", "*.gguf", "consolidated*"])
print(f"downloaded {sys.argv[1]}@{sys.argv[2]} to {path} in {time.time() - t0:.0f}s", flush=True)
PY
  export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
fi
"$PY" -c "
import sys
from src.llm.client import TokenCounter
assert TokenCounter(sys.argv[1]).tok is not None, 'tokenizer unavailable'" "$MODEL"

# Another job on the node may already hold the config's port, so serve on a free port and point a job-local copy
# of the config at it. The cache key does not include the URL, so this does not change any result.
PORT=$("$PY" -c "import socket; s = socket.socket(); s.bind(('', 0)); print(s.getsockname()[1]); s.close()")
JOB_CONFIG=$LOCAL/config.yaml
"$PY" -c "
import sys, yaml
c = yaml.safe_load(open(sys.argv[1]))
c['base_url'] = f'http://localhost:{sys.argv[2]}/v1'
yaml.safe_dump(c, open(sys.argv[3], 'w'), sort_keys=False)" "$CONFIG" "$PORT" "$JOB_CONFIG"
echo "serving on port $PORT"
"$ROOT/.conda-env/bin/vllm" serve "$MODEL" --revision "$REV" --tokenizer-revision "$REV" --port "$PORT" --max-model-len 16384 \
  --gpu-memory-utilization 0.85 --seed 0 $VLLM_ARGS > "logs/vllm_${SLURM_JOB_ID}.log" 2>&1 &
VLLM_PID=$!
for _ in $(seq 1 180); do
  curl -sf "localhost:$PORT/v1/models" | grep -qF "\"$MODEL\"" && break
  kill -0 "$VLLM_PID" 2>/dev/null || { echo "vLLM exited"; tail -30 "logs/vllm_${SLURM_JOB_ID}.log"; exit 3; }
  sleep 5
done
curl -sf "localhost:$PORT/v1/models" | grep -qF "\"$MODEL\"" || { echo "vLLM did not start"; exit 3; }
kill -0 "$VLLM_PID" 2>/dev/null || { echo "the server on port $PORT is not ours"; exit 3; }

run() {
  local name=$1; shift
  local budget=384 prev=
  for a in "$@"; do [ "$prev" = --budget ] && budget=$a; prev=$a; done
  if [ -n "${SKIP_EXISTING:-}" ] && [ -e "results/runs/$name/probes_B$budget.jsonl" ]; then
    echo "skipping $name (B=$budget exists)"; return 0
  fi
  "$PY" -m src.eval.run --config "$JOB_CONFIG" --conditions "$CONDS" --cache "${RUN_CACHE:-$LOCAL_CACHE}" --run-name "$name" \
    ${LIMIT:+--limit "$LIMIT"} ${MAX_CONCURRENCY:+--max-concurrency "$MAX_CONCURRENCY"} "$@" &
  RUN_PID=$!
  wait "$RUN_PID"
  RUN_PID=
}

START=$(date +%s)
for MODE in "${MODE_LIST[@]}"; do
echo "mode $MODE started at minute $(( ($(date +%s) - START) / 60 ))"
case "$MODE" in
  smoke)
    run "$RUN-pace-smoke-nocap" --limit 2
    run "$RUN-pace-smoke-hardcap" --hard-cap --limit 2 ;;
  full)
    run "$RUN-pace-nocap"
    run "$RUN-pace-hardcap" --hard-cap ;;
  hardcap)
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
  dev)
    CONDS=$ALL_CONDS run "$RUN-pace-dev-v1" --hard-cap --split dev --extract-version 1
    CONDS=$V2_CONDS run "$RUN-pace-dev-v2" --hard-cap --split dev --extract-version 2 ;;
  confirm-smoke)
    CONDS=$ALL_CONDS run "$RUN-pace-smoke-confirm-v1" --hard-cap --data data/confirm/dialogues.jsonl --extract-version 1 --limit 2
    CONDS=$V2_CONDS run "$RUN-pace-smoke-confirm-v2" --hard-cap --data data/confirm/dialogues.jsonl --extract-version 2 --limit 2 ;;
  confirm)
    CONDS=$ALL_CONDS run "$RUN-pace-confirm-v1" --hard-cap --data data/confirm/dialogues.jsonl --extract-version 1
    CONDS=$V2_CONDS run "$RUN-pace-confirm-v2" --hard-cap --data data/confirm/dialogues.jsonl --extract-version 2 ;;
  replicate)
    HINTS=summary_hint,pinning_hint,chrono_hint
    CONDS=$V2_CONDS run "$RUN-pace-replicate-test-v2" --hard-cap --extract-version 2
    CONDS=$HINTS run "$RUN-pace-replicate-test-hints" --hard-cap --extract-version 1
    CONDS=$V2_CONDS run "$RUN-pace-replicate-fresh-v2" --hard-cap --data data/fresh/dialogues_spread.jsonl --extract-version 2
    CONDS=$HINTS run "$RUN-pace-replicate-fresh-hints" --hard-cap --data data/fresh/dialogues_spread.jsonl --extract-version 1 ;;
  v2-robust)
    for B in 256 768; do
      CONDS=$V2_CONDS run "$RUN-pace-replicate-test-v2" --hard-cap --budget "$B" --extract-version 2
    done
    for L in early late; do
      CONDS=$V2_CONDS run "$RUN-pace-replicate-fresh-$L-v2" --hard-cap --data "data/fresh/dialogues_$L.jsonl" --extract-version 2
    done ;;
  noise)
    for S in "${NOISE_SETTINGS[@]}"; do
      read -r SUFFIX SPEC <<< "$S"
      CONDS=$FU_CONDS run "$RUN-pace-confirm-noise-$SUFFIX" --hard-cap --data "$CONFIRM" --gold-noise "$SPEC"
    done ;;
  swap)
    for S in "${SWAP_CELLS[@]}"; do
      read -r NAME OTHER V <<< "$S"
      CONDS=$FU_CONDS run "$RUN-pace-confirm-swap-$NAME" --hard-cap --data "$CONFIRM" --events-from "$(swap_source "$OTHER" "$V")"
    done ;;
  latency)
    # Each condition starts from an empty cache, so every call reaches the server; the caches are kept for replay.
    mkdir -p "$(dirname "$CACHE")/latency"
    for C in $LATENCY_CONDS; do
      CONDS=$C RUN_CACHE=$LOCAL/latency_$C.sqlite MAX_CONCURRENCY=1 \
        run "$RUN-pace-latency-$C" --hard-cap --data "$CONFIRM" --extract-version 1
      copy_sqlite "$LOCAL/latency_$C.sqlite" "$(dirname "$CACHE")/latency/$(basename "${CACHE%.sqlite}")_latency_$C.sqlite"
    done ;;
  newconds)
    CONDS=$NEW_CONDS run "$RUN-pace-confirm-new-v1" --hard-cap --data "$CONFIRM" --events-from "$(swap_source "$BASE_RUN" v1)"
    CONDS=lifecycle_source run "$RUN-pace-confirm-new-v2" --hard-cap --data "$CONFIRM" --events-from "$(swap_source "$BASE_RUN" v2)"
    CONDS=$NEW_CONDS run "$RUN-pace-test-new" --hard-cap --events-from "results/runs/$BASE_RUN-det1-pace-hardcap/extractions.jsonl"
    CONDS=$FORGED_CONDS run "$RUN-pace-forged-v2" --hard-cap --data "$FORGED" --extract-version 2 ;;
  scale)
    # Batch invariance for this model: two runs on the same server with different batching must match exactly.
    for X in a:384 b:64; do
      CONDS=$ALL_CONDS,$NEW_CONDS RUN_CACHE=$LOCAL/check_${X%%:*}.sqlite MAX_CONCURRENCY=${X##*:} LIMIT=8 \
        run "$RUN-pace-scalecheck-${X%%:*}" --hard-cap --data "$CONFIRM" --extract-version 1
      [ -f "$LOCAL/check_${X%%:*}.sqlite" ] && copy_sqlite "$LOCAL/check_${X%%:*}.sqlite" "${CACHE%.sqlite}_check_${X%%:*}.sqlite"
    done
    "$PY" -m src.eval.determinism_check "results/runs/$RUN-pace-scalecheck-a" "results/runs/$RUN-pace-scalecheck-b" \
      || { echo "batch invariance check failed; stopping"; exit 4; }
    CONDS=$ALL_CONDS,$NEW_CONDS run "$RUN-pace-confirm-v1" --hard-cap --data "$CONFIRM" --extract-version 1
    CONDS=$V2_CONDS,lifecycle_source run "$RUN-pace-confirm-v2" --hard-cap --data "$CONFIRM" --extract-version 2
    CONDS=$FORGED_CONDS run "$RUN-pace-forged-v2" --hard-cap --data "$FORGED" --extract-version 2 ;;
  followup-pilot)
    CONDS=$FU_CONDS run "$RUN-pace-confirm-noise-p1000-r1000-s0" --hard-cap --data "$CONFIRM" --gold-noise precision=1.0,recall=1.0,seed=0
    CONDS=$FU_CONDS run "$RUN-pace-confirm-noise-p500-r1000-s0" --hard-cap --data "$CONFIRM" --gold-noise precision=0.5,recall=1.0,seed=0
    CONDS=$FU_CONDS run "$RUN-pace-confirm-noise-p1000-r700-s0" --hard-cap --data "$CONFIRM" --gold-noise precision=1.0,recall=0.7,seed=0
    CONDS=$FU_CONDS run "$RUN-pace-confirm-swap-mistral-7b-v0.3-v1" --hard-cap --data "$CONFIRM" \
      --events-from "$(swap_source mistral-7b-v0.3 v1)" ;;
esac
done
echo "elapsed minutes: $(( ($(date +%s) - START) / 60 ))"
