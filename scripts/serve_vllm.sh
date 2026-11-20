#!/usr/bin/env bash
# Usage: scripts/serve_vllm.sh <hf_model> <gpu_id> <port>
# e.g.   scripts/serve_vllm.sh Qwen/Qwen2.5-7B-Instruct 0 8000
set -euo pipefail
MODEL=${1:-Qwen/Qwen2.5-7B-Instruct}; GPU=${2:-0}; PORT=${3:-8000}
mkdir -p logs
CUDA_VISIBLE_DEVICES=$GPU HF_HUB_OFFLINE=1 VLLM_USE_FLASHINFER_SAMPLER=0 exec vllm serve "$MODEL" \
  --port "$PORT" --max-model-len 16384 --gpu-memory-utilization 0.85 \
  --seed 0 --no-enable-log-requests 2>&1 | tee "logs/vllm_$(basename "$MODEL")_$PORT.log"
