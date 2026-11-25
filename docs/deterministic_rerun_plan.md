# Deterministic Rerun Plan

Fixed on November 24, 2026, before any pilot output existed. File hashes at that point are recorded locally in `results/confirm/freeze_deterministic.json`.

## Why

The runs reported so far used vLLM without batch-invariant kernels. A rerun from scratch changes 6% to 15% of decisions and 3 of 51 planned Confirm conclusions ([`reproducibility.md`](reproducibility.md)). Deterministic serving gave identical outputs in a small test on 52 Confirm dialogues with one model. Before rerunning all experiments, a larger pilot checks that this holds for all three models and under different load.

## Stage 1: pilot

- **Data:** the full Confirm set, 208 dialogues, with extraction v1 (14 conditions) and v2 (8 conditions).
- **Models:** Qwen2.5-7B, Llama-3.1-8B, and Mistral-7B, at the revisions in `configs/model_revisions.yaml`.
- **Two independent runs per model:** run 1 with the configured 384 concurrent requests, and run 2 with 64, so the batches differ. Each run starts from its own empty cache.
- **Settings:** `VLLM_BATCH_INVARIANT=1`, shared in-flight requests, and the same code for every run, identified by the source hash in each run's metadata.

The pilot passes only if, for every model and extraction version:

1. Run 1 and run 2 match in every probe field except latency, and their extractions are identical.
2. Replaying run 1 from its own cache with `--cache-only` gives zero cache misses and outputs identical to run 1.

If any check fails, the cause is investigated and nothing is extended.

## Stage 2: extension, only after the pilot passes

- Every existing PACE experiment is rerun once in deterministic mode with its original settings: Test with and without the hard cap and at budgets 256 and 768, Fresh with three compaction placements, the dev split, the replication runs, and the v2 robustness runs.
- Pilot run 1 is the deterministic Confirm run.
- No prompt, method, data, or analysis code changes between the pilot and stage 2.

## Reporting rule

- The deterministic runs replace the earlier runs as the reported results, whatever they show.
- The planned tests in [`post_milestone_confirmation_plan.md`](post_milestone_confirmation_plan.md) and [`third_model_plan.md`](third_model_plan.md) are applied unchanged to the deterministic Confirm runs.
- The original runs and the cache-free rerun are reported as run-to-run variability, including every planned conclusion that differs between runs.
