#!/usr/bin/env bash
# Full local pipeline (2 GPUs). Servers: scripts/serve_vllm.sh Qwen/Qwen2.5-7B-Instruct 0 8000
#                                         scripts/serve_vllm.sh meta-llama/Llama-3.1-8B-Instruct 1 8001
set -euo pipefail
python -m src.generation.build --out data --n-timelines 48 --seed 0
python -m src.generation.paraphrase            # needs both servers (paraphraser=Llama, judge=Qwen)
python -m pytest -q tests
python -m src.eval.run --config configs/qwen7b.yaml  & python -m src.eval.run --config configs/llama8b.yaml & wait
for B in 256 768; do                           # memory-budget sweep (main conditions)
  python -m src.eval.run --config configs/qwen7b.yaml  --budget $B --conditions summary,pinning,chrono,typed_llm,lifecycle &
  python -m src.eval.run --config configs/llama8b.yaml --budget $B --conditions summary,pinning,chrono,typed_llm,lifecycle &
  wait
done
python -m src.eval.analyze --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b --budget 384 --out results
python -m src.eval.budget_sweep --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b --out results
