#!/bin/bash
# PACE-ICE CPU job: replay every PACE run from the LLM caches with the current code and compare with stored outputs.
# Usage (from the project directory on PACE): sbatch scripts/pace_replay.sbatch [name-filter [cache-file ...]]
#   REPLAY_OUT=dir changes the output directory (default results/replay).
#SBATCH -J ladl-replay
#SBATCH --account=ece --partition=ice-cpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8 --mem=48G
#SBATCH -t 04:00:00
#SBATCH -o logs/%x_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export HF_HOME=$PWD/hf_home HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
mkdir -p logs
CACHE_ARGS=()
for c in "${@:2}"; do CACHE_ARGS+=(--cache-file "$c"); done
.conda-env/bin/python -m src.eval.replay_check --out "${REPLAY_OUT:-results/replay}" ${1:+--only "$1"} "${CACHE_ARGS[@]}"
