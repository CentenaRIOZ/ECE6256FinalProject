# Follow-Up Experiments Plan

Fixed on November 26, 2026, before any output of these experiments existed and before any dialogue-level number was computed. The hashes in `results/confirm/freeze_followup.json` (kept locally, not in git) record the code, data, and this plan at the time the pilot started.

## Purpose

Three gaps remain after the deterministic reruns:

1. **Only probe-level scores and no cost.** Every result scores single decisions. The proposal also promised token, latency, and cost figures, which are not yet reported.
2. **The extraction explanation is correlational.** Mistral's LADL loses to ordinary compaction, and its extractor has low precision, but nothing yet shows that low precision causes the loss.
3. **The practical advice is untested.** If extraction is the weak part, a stronger extractor should rescue a weaker decision model. No run has tried this.

Experiment A addresses gap 1, B addresses gap 2, and C addresses gap 3.

## Common settings

- **Serving:** the deterministic setup of [`deterministic_rerun_plan.md`](deterministic_rerun_plan.md): vLLM 0.34.0 with `VLLM_BATCH_INVARIANT=1`, temperature 0, seed 0, the model revisions in `configs/model_revisions.yaml`, and shared in-flight requests.
- **Models:** Qwen2.5-7B-Instruct, Llama-3.1-8B-Instruct, and Mistral-7B-Instruct-v0.3.
- **Data for B and C:** the Confirm set (208 dialogues, 52 timelines, 916 probes), budget 384, hard memory cap. Confirm is used because the planned tests and the extraction precision figures are reported on it.
- **Frozen:** the policy prompt, extraction prompts, summary and pinning prompts, reducer, rendering, and budgets are unchanged. The only new code supplies events from a file or from noisy gold labels, and counts usage per condition.
- **Statistics:** paired timeline-cluster bootstrap with 2,000 resamples and seed 0, as in the earlier plans. Two-sided p-values have a floor of 2/2001. Holm correction runs within each family below. A test with a predicted direction is confirmed when its Holm-adjusted p is below 0.05 and the estimate has the predicted sign. A two-sided test is significant when its Holm-adjusted p is below 0.05, in either direction.

## Experiment A: dialogue-level metrics and cost

### Dialogue-level metrics

No new model outputs are needed. The metrics are computed from the deterministic runs already reported.

- **Dialogue success:** every probe in the dialogue gets the correct four-way decision.
- **Safe dialogue:** no probe in the dialogue gets `act` when the correct decision is not `act`. This counts executing a prohibited, cancelled, already completed, or not-yet-allowed action, and acting where the user asked to be consulted.
- **First error:** the position of the first wrong probe, in probe order. It is reported as the share of dialogues still error-free after k probes, for k = 1 to 4. Every Confirm dialogue has at least 3 probes, and 196 of 208 have at least 4.

These are reported for every condition on Test (B=384, extraction v1 and v2), Fresh with spread compaction (v1 and v2), and Confirm (v1 and v2), for all three models.

**Planned tests on Confirm.** The comparisons repeat the primary probe-level families: LADL v1 minus `summary_hint`, `pinning_hint`, `chrono_hint`, and `typed_llm`.

| Family | Metric | Tests | Prediction |
|---|---|---|---|
| A1 | Dialogue success | Qwen and Llama, 8 tests | LADL higher |
| A2 | Dialogue success | Mistral, 4 tests | none (two-sided) |
| A3 | Safe dialogue | Qwen and Llama, 8 tests | LADL higher |
| A4 | Safe dialogue | Mistral, 4 tests | none (two-sided) |

The probe-level results are already known, and dialogue-level scores are built from the same decisions, so these tests are not independent confirmation. The plan fixes the metrics and comparisons before any dialogue-level number is seen. Mistral is two-sided because its probe-level results were mixed.

### Cost

- **Tokens and calls:** each deterministic Confirm run (three models, extraction v1 and v2) is replayed from its cache with `--cache-only`, with usage now counted per condition. The replay also checks that the new code leaves every output unchanged; it must give zero cache misses and identical outputs. For each condition the report gives LLM calls per dialogue by call type, prompt and completion tokens per dialogue, memory tokens at decision time, and decision prompt tokens. Extraction is counted in full for every condition that uses it.
- **State queries are excluded from cost.** The state-recall question is a diagnostic for RQ1 and is not part of the agent's work. Its cost is reported separately.
- **Latency:** one job per model on an H200 sends one request at a time. It runs the first 8 Confirm dialogues for `full`, `summary`, `pinning`, `chrono`, `typed_llm`, and `lifecycle` (extraction v1), each from its own empty cache so no call is skipped. The report gives seconds per dialogue, per decision, and per user turn for memory upkeep. Batch-invariant kernels stay on, so absolute times are slower than with default kernels. The comparison between conditions is the result of interest. Timing jobs avoid node `atl1-1-03-013-26-0`. Because serving is deterministic, the decisions of these runs must equal those of the deterministic Confirm runs on the same dialogues.

## Experiment B: extraction-noise dose-response

### Events

Each condition that normally uses extracted events instead receives gold events with controlled errors:

- **Perfect extraction:** gold events with tool and target filled in and items renamed `I1`, `I2`, ... in order of first appearance, as the extractor's registry names them. This removes the gold item IDs, which encode item type.
- **Missed events, recall r:** each gold event is dropped independently with probability 1 − r. Later events about an item whose creation was dropped are kept, as they would be if only that one event were missed.
- **False events, precision p:** a dialogue with n gold events receives n · r · (1 − p) / p false events, rounded stochastically, so the expected precision is p. False events go on user turns without gold events, spread over distinct turns first. Their type follows the false events made by the three extractors on the Test split, extraction v1 and v2 pooled (2,541 events; Confirm was not used): commit 0.36, ambiguous 0.34, approve 0.11, tool result 0.07, prohibit 0.06, revoke 0.05, cancel 0.01. A false commit or prohibition uses a tool of the dialogue's gold items with probability 0.63, and a false commit has a condition with probability 0.21. A false approval is explicit with probability 0.74 and satisfies the condition with probability 0.42. A false tool result reports success with probability 0.26. These rates are also taken from the Test split. A false event that needs an existing item of a type the dialogue does not yet have becomes a false commit.
- **Nested levels:** every random choice depends only on the dialogue, the noise seed, and the event, so the false events at precision 0.6 include those at 0.7, and the events dropped at recall 0.7 include those dropped at 0.8.

The realized precision and recall of each setting are measured with the same evaluation code as for real extractors.

### Settings and conditions

15 settings per model, all with noise seed 0 except where noted:

| Setting | Precision | Recall |
|---|---|---|
| Perfect | 1.0 | 1.0 |
| False events | 0.9, 0.8, 0.7, 0.6, 0.5, 0.4 | 1.0 |
| Missed events | 1.0 | 0.9, 0.8, 0.7, 0.6, 0.5 |
| Matched to the model's own extractor | its Confirm precision and recall, v1 and v2 | |
| Seed check | 0.5, with seed 1 | 1.0 |

The matched settings use the rates in [`post_milestone_results.md`](post_milestone_results.md): Qwen v1 0.884/0.843 and v2 0.905/0.871, Llama v1 0.857/0.870 and v2 0.912/0.935, and Mistral v1 0.519/0.814 and v2 0.426/0.826.

Conditions: `lifecycle` (LADL), `lifecycle_nohint`, `chrono`, and `chrono_hint`. Ordinary compaction and pinning, with and without hints, do not use events. Their deterministic Confirm results are the reference lines.

### Planned tests, family B, Holm over 9 tests

For each model, on the same probes:

- **B1, hints under false events:** the hint effect (`lifecycle` − `lifecycle_nohint`) at precision 0.5 minus the hint effect with perfect extraction. Predicted negative: hints turn false ambiguity flags into wrong `clarify` answers.
- **B2, reducer versus event log under false events:** (`lifecycle` − `chrono_hint`) at precision 0.5 minus the same difference with perfect extraction. Two-sided.
- **B3, reducer versus event log under missed events:** (`lifecycle` − `chrono_hint`) at recall 0.7 minus the same difference with perfect extraction. Two-sided.

### Reported without a test

- Accuracy against realized precision and recall for every condition, with confidence intervals.
- **Break-even precision:** the precision at which LADL equals ordinary compaction, found by linear interpolation with a bootstrap interval. The prediction is that Mistral's break-even lies above its real v1 precision of 0.52, and that Qwen's and Llama's real precision lies above their break-even points.
- **Matched check:** real LADL accuracy minus LADL accuracy under matched noise. Near zero means the error rates explain the real loss. A clearly lower real accuracy means the real errors are more harmful than random errors at the same rates.
- **Seed check:** the difference between seeds 0 and 1 at precision 0.5.
- The share of wrong decisions on probes whose item received a false event.

## Experiment C: swapping extractor and decision model

Each model's deterministic Confirm extractions (v1 and v2) are given to each decision model, which also writes the summaries and makes the decisions. The six cells where a model uses its own extractions already exist. The 12 new cells use the same four conditions as experiment B.

### Planned tests, family C, Holm over 12 tests

| Tests | Comparison | Prediction |
|---|---|---|
| 4 | Mistral deciding: LADL with Qwen's, and with Llama's, extraction minus LADL with Mistral's own, for v1 and v2 | positive |
| 4 | Mistral deciding: LADL with Qwen's, and with Llama's, v2 extraction minus Mistral's ordinary compaction, and minus Mistral's pinning | positive |
| 4 | Qwen and Llama deciding: LADL with Mistral's extraction minus LADL with their own, for v1 and v2 | negative |

Exploratory: the swaps between Qwen and Llama, the other three conditions, and how much of the accuracy spread across the 3 × 6 table follows the extractor rather than the decision model.

## Validation before the full runs

1. **Unit tests:** noise generation is deterministic across processes, nested across levels, and reaches the target rates on Confirm. Events from a file must cover every dialogue and turn.
2. **Replay checks on a CPU node:** (a) the six deterministic Confirm runs, replayed with the new code, give zero cache misses and identical outputs; (b) giving each model its own extraction file with `--events-from`, and replaying from its cache, reproduces the deterministic outputs of the four conditions exactly.
3. **GPU pilot, Qwen only, first 8 Confirm dialogues:** perfect extraction, precision 0.5, recall 0.7, and Mistral's v1 events. Two independent runs, one with 384 concurrent requests and one with 64, each from an empty cache, must match exactly. A replay of the first run must give zero cache misses. Pilot accuracy is not used for any decision.

The full runs start only after all three checks pass. Afterwards every full run is replayed from its cache and must give zero misses and identical outputs.

## Reporting rule

- Every planned test and every listed setting is reported, whatever it shows.
- Any setting, condition, or analysis added after results are seen is labeled exploratory.
- A failed or repeated job is reported with its reason.

## Expected cost

About 4 H200 GPU-hours: 0.3 for the pilot, about 2.5 for the full runs of B and C (one job per model), and about 1.2 for the latency jobs. Replays run on CPU nodes.
