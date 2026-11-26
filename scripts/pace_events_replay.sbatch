#!/bin/bash
# PACE-ICE CPU job: check that --events-from reproduces the deterministic Confirm runs exactly.
# Each model gets its own deterministic Confirm extraction file back, is replayed from its deterministic cache with
# --cache-only, and is compared with the original run on the conditions of the follow-up experiments.
# Usage (from the project directory on PACE): sbatch scripts/pace_events_replay.sbatch
#   REPLAY_OUT=dir changes the output directory (default results/replay_followup/events_from).
#SBATCH -J ladl-evreplay
#SBATCH --account=ece --partition=ice-cpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8 --mem=32G
#SBATCH -t 01:30:00
#SBATCH -o logs/%x_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export HF_HOME=$PWD/hf_home HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=.conda-env/bin/python
OUT=${REPLAY_OUT:-results/replay_followup/events_from}
WORK=${TMPDIR:-/tmp}/evreplay_${SLURM_JOB_ID:-$$}
mkdir -p "$WORK" "$OUT" logs
trap 'rm -rf "$WORK"' EXIT
CONDS=$("$PY" -c "from src.eval.followup_settings import CONDITIONS; print(','.join(CONDITIONS))")
STATUS=0
for PAIR in "qwen2.5-7b qwen7b" "llama3.1-8b llama8b" "mistral-7b-v0.3 mistral7b"; do
  read -r RUN KEY <<< "$PAIR"
  # A copy, so the replay never writes to the stored cache.
  "$PY" -c "
import sqlite3, sys
a = sqlite3.connect(f'file:{sys.argv[1]}?mode=ro', uri=True); b = sqlite3.connect(sys.argv[2]); a.backup(b)" \
    "cache/llm_${KEY}_det1.sqlite" "$WORK/$KEY.sqlite"
  for V in v1 v2; do
    SRC=results/runs/$RUN-det1-pace-confirm-$V
    DST=$OUT/$RUN-$V
    rm -rf "$DST"
    "$PY" -m src.eval.run --config "configs/$KEY.yaml" --conditions "$CONDS" --hard-cap --data data/confirm/dialogues.jsonl \
      --cache "$WORK/$KEY.sqlite" --cache-only --events-from "$SRC/extractions.jsonl" \
      --run-name "$(realpath -m --relative-to=results/runs "$DST")"
    "$PY" -c "
import json, sys
usage = json.load(open(sys.argv[1]))['usage']
misses = int(sum(v.get('cache_miss', 0) for v in usage.values()))
print(f'{sys.argv[2]}: {misses} cache misses')
sys.exit(1 if misses else 0)" "$DST/meta_B384.json" "$RUN-$V" || STATUS=1
    "$PY" -m src.eval.determinism_check --shared-conditions "$SRC" "$DST" || STATUS=1
  done
done
echo "events-from replay status: $STATUS"
exit $STATUS
