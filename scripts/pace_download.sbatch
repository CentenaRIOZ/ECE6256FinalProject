#!/bin/bash
# PACE-ICE: download extra models into project scratch without changing the Python environment.
# Usage (from the project directory on PACE): sbatch scripts/pace_download.sbatch mistralai/Mistral-7B-Instruct-v0.3
#SBATCH -J ladl-download
#SBATCH --account=ece --partition=ice-cpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=4 --mem=16G
#SBATCH -t 00:45:00
#SBATCH -o logs/%x_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
export HF_HOME=$PWD/hf_home
export HF_TOKEN_PATH=$HOME/.cache/huggingface/token
.conda-env/bin/python - "$@" <<'PY'
import sys
import yaml
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
revisions = yaml.safe_load(open("configs/model_revisions.yaml")) or {}
for repo in sys.argv[1:]:
    rev = revisions.get(repo)  # pinned snapshot; a new model is fetched at its latest revision, then pinned
    # consolidated.safetensors duplicates the sharded weights in Mistral repositories.
    path = snapshot_download(repo, revision=rev, ignore_patterns=["original/*", "*.pth", "*.bin", "*.gguf", "consolidated*"])
    AutoTokenizer.from_pretrained(repo, revision=rev)
    print("ready:", repo, path, flush=True)
PY
echo "download complete"
