# Third-Model Plan

Fixed on November 23, 2026, before any Mistral output was generated. The hashes in `results/confirm/freeze_mistral.json` record the files at that point.

## Purpose

Qwen2.5-7B and Llama-3.1-8B were used while LADL, the baselines, and extraction v2 were developed. A third model that played no part in any design decision tests whether the main results depend on those two models.

## Model

`mistralai/Mistral-7B-Instruct-v0.3`, served with vLLM 0.34.0 on one H200 at temperature 0 and seed 0.

It was chosen because it comes from a third model family, is from the same 2024 generation as the other two models, needs no license approval, supports a 32K context, and has a chat template that accepts system prompts. vLLM uses the Hugging Face chat template (`--tokenizer-mode hf`), as for the other two models.

## Frozen

- Extraction prompts v1 and v2, policy prompt, memory conditions, reducer, and budgets are unchanged.
- No run uses the dev split with this model, and no prompt is changed for it.
- Smoke runs on 2 dialogues only check that outputs are valid. Their accuracy is not used for any decision.

## Runs

The same settings as the other two models, all with the hard memory cap:

| Data | Settings |
|---|---|
| Test, 664 probes | B=384, 256, and 768 |
| Fresh, 912 probes | Compaction spread, early, and late |
| Confirm, 916 probes | Extraction v1 and v2 |
| Test and Fresh replication | Hint-parity baselines and extraction v2 |

## Tests on Confirm

All tests use paired timeline-cluster bootstrap with 2,000 resamples, and four-way decision accuracy. These families are separate from the two-model families in `post_milestone_confirmation_plan.md`, which are not re-corrected.

**Primary family, Holm over 4 tests:** LADL v1 minus `summary_hint`, `pinning_hint`, `chrono_hint`, and `typed_llm`. This repeats the planned two-model test.

**v2 family, Holm over 7 tests:** LADL v2 minus every compacted baseline: `summary`, `summary_hint`, `pinning`, `pinning_hint`, `chrono` (v2 extraction), `chrono_hint` (v2 extraction), and `typed_llm` (v2 extraction). This family tests the method recommended for the final paper against every baseline, without choosing a strongest baseline after seeing results.

**Secondary family, Holm over 6 tests:** LADL v1 minus `summary`, `pinning`, `chrono`, and `lifecycle_nohint`; LADL v2 minus LADL v1; strict hedging minus LADL v1.

An effect is confirmed only if the difference is positive and its corrected p-value is below 0.05. LADL counts as beating every baseline on this model only if all seven v2 tests are confirmed.

Results on Test and Fresh, budgets, compaction placements, and strongest-baseline comparisons are exploratory.

## Stopping rule

Each run is done once. If a run fails for a technical reason, such as a crash or time limit, it is rerun unchanged. Negative and null results are reported.
