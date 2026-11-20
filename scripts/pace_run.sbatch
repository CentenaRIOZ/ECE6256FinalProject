#!/bin/bash
# PACE-ICE job: serve one model with vLLM on a single GPU and run all conditions.
# Usage: sbatch scripts/pace_run.sbatch configs/qwen7b.yaml Qwen/Qwen2.5-7B-Instruct
#SBATCH -J lcledger
#SBATCH -N1 --ntasks-per-node=1 --cpus-per-task=8
#SBATCH --gres=gpu:1 -C "A100-40GB|H100|L40S|RTX6000"
#SBATCH --mem=64G
#SBATCH -t 04:00:00
#SBATCH -o logs/pace_%j.out
set -euo pipefail
CONFIG=${1:-configs/qwen7b.yaml}; MODEL=${2:-Qwen/Qwen2.5-7B-Instruct}; PORT=8000
module load anaconda3 2>/dev/null || true
source activate lcledger 2>/dev/null || conda activate lcledger
cd "$SLURM_SUBMIT_DIR"
mkdir -p logs
export HF_HOME=${HF_HOME:-$HOME/scratch/hf}   # keep weights out of the home quota
nvidia-smi --query-gpu=name,memory.total --format=csv | tee logs/pace_${SLURM_JOB_ID}_gpu.txt
VLLM_USE_FLASHINFER_SAMPLER=0 vllm serve "$MODEL" --port $PORT --max-model-len 16384 \
  --gpu-memory-utilization 0.85 --seed 0 > logs/pace_${SLURM_JOB_ID}_vllm.log 2>&1 &
until curl -s localhost:$PORT/v1/models >/dev/null; do sleep 5; done
START=$(date +%s)
python -m src.eval.run --config "$CONFIG"
echo "GPU-hours: $(echo "($(date +%s)-$START)/3600" | bc -l)" | tee -a logs/pace_${SLURM_JOB_ID}_gpu.txt
