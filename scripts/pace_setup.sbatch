#!/bin/bash
# PACE-ICE setup: create the Python environment and download both models into project scratch.
# Usage (from the project directory on PACE): sbatch scripts/pace_setup.sbatch
#SBATCH -J ladl-setup
#SBATCH --account=ece --partition=ice-cpu --qos=coe-ice
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8 --mem=32G
#SBATCH -t 01:30:00
#SBATCH -o logs/%x_%j.out
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
ROOT=$PWD
ENV_DIR=$ROOT/.conda-env
export HF_HOME=$ROOT/hf_home
export HF_TOKEN_PATH=$HOME/.cache/huggingface/token
export PIP_CACHE_DIR=$ROOT/.pip-cache
export CONDA_PKGS_DIRS=$ROOT/.conda-pkgs

source "$HOME/miniconda3/etc/profile.d/conda.sh"
[ -x "$ENV_DIR/bin/python" ] || conda create -y -p "$ENV_DIR" --override-channels -c conda-forge python=3.12 pip
# Install the exact environment used for all runs. scripts/requirements-pace.txt is the original top-level list.
"$ENV_DIR/bin/python" -m pip install -r scripts/pace_env_freeze.txt
mkdir -p logs
"$ENV_DIR/bin/python" -m pip list --format=freeze > "logs/pace_env_freeze_${SLURM_JOB_ID}.txt"
diff -q scripts/pace_env_freeze.txt "logs/pace_env_freeze_${SLURM_JOB_ID}.txt" || echo "WARNING: installed environment differs from scripts/pace_env_freeze.txt"

"$ENV_DIR/bin/python" - <<'PY'
import yaml
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer
revisions = yaml.safe_load(open("configs/model_revisions.yaml"))
for repo in ("Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.1-8B-Instruct"):
    path = snapshot_download(repo, revision=revisions[repo], ignore_patterns=["original/*", "*.pth", "*.bin", "*.gguf"])
    AutoTokenizer.from_pretrained(repo, revision=revisions[repo])
    print("ready:", repo, path, flush=True)
PY
echo "setup complete"
