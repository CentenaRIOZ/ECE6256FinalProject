# Follow-Up Experiment Results

These experiments follow [`followup_experiments_plan.md`](followup_experiments_plan.md), which was fixed on November 26, 2026 before any of their outputs existed and before any dialogue-level number was computed. All runs use deterministic serving on PACE-ICE H200 GPUs, the Confirm set (208 dialogues, 52 timelines, 916 probes), budget 384, and the hard memory cap. Result files are kept locally under `results/followup/` and are not stored in git; the commands at the end regenerate them.

## Summary

- **Dialogue-level scores confirm the probe-level pattern.** On Confirm, LADL v1 gets every decision right in more dialogues than each hint-parity baseline for Qwen (+14.9 to +27.9 points), and than ordinary compaction and pinning with hints for Llama. For full correctness, all 12 planned dialogue tests reach the same conclusion as the corresponding planned probe-level tests. Even with gold events, only 46% to 54% of dialogues are fully correct.
- **LADL uses 5 to 6 times the prompt tokens of ordinary compaction per dialogue.** Nearly all of the extra is one extraction call per user turn. In one-request-at-a-time runs, a dialogue takes 1.4 to 1.8 times as long as with ordinary compaction, and 0.3 to 0.8 times as long as with constraint pinning.
- **Extraction precision causes the LADL gap.** Injecting false events into gold events lowers LADL accuracy steadily. At the error rates of each model's real extractor, the synthetic noise reproduces real LADL accuracy within 1.2 points for all six model-prompt pairs. LADL with hints falls below ordinary compaction at a precision of about 0.52 for Mistral and 0.66 for Llama; Qwen stays above it down to 0.4.
- **Action hints are what make false events costly.** At precision 0.5, hints change from a help to a harm by 11.6 to 14.0 points, confirmed for all three models. LADL without hints loses only 4 to 7 points at that precision.
- **A better extractor fixes the weaker model.** With Llama's or Qwen's v2 extraction, Mistral's LADL reaches 83.0% to 84.3%, 15 to 16 points above Mistral's ordinary compaction. With Mistral's extraction, Qwen and Llama lose 11 to 19 points. All 12 planned swap tests are confirmed. In the 3 × 6 table of LADL accuracy, the extraction source accounts for 99% of the spread and the decision model for almost none.

## Validation

- The six deterministic Confirm runs, replayed with the new code, gave zero cache misses and identical outputs. Giving each model its own extraction file through `--events-from` reproduced the deterministic outputs exactly.
- **Pilot:** Qwen on the first 8 dialogues, run twice with 384 and 64 concurrent requests on different nodes, each from an empty cache. All four runs matched exactly, and the replay had zero misses.
- **Full runs:** all 57 runs, plus the 4 pilot runs, replayed from their caches with zero misses and identical outputs (209,360 probe records). The events stored by every noise run equal those regenerated from the noise generator.
- **Latency runs:** their decisions equal those of the deterministic Confirm runs on the same dialogues for all 18 runs.
- All 83 new runs carry the source hash recorded at the start of the pilot (`results/confirm/freeze_followup.json`) and vLLM 0.34.0.
- **Deviation:** the Llama job reached its 90-minute limit after all 15 noise settings, during the first swap cell, because its node was heavily shared. The time-limit handler saved the cache, and a second job with `SKIP_EXISTING=1` ran the 4 swap cells. Its outputs are covered by the replay check above.
- **Compute:** 9 GPU jobs used 4.6 H200 GPU-hours (plan: about 4). Replays used 11 CPU jobs. One more replay job was submitted with the wrong cache file and cancelled before it started. All LADL PACE jobs so far total 18.6 GPU-hours.

## A. Dialogue-level metrics and cost

### Planned tests on Confirm

Differences in percentage points of dialogues, LADL v1 minus the baseline, with 95% confidence intervals. Families A1 and A3 predict a positive difference; A2 and A4 (Mistral) are two-sided.

| Metric | Baseline | Qwen | Llama | Mistral |
|---|---|---|---|---|
| All decisions correct | Compaction + hints | **+25.0** [16.8, 33.7] | **+18.8** [11.5, 25.5] | +0.5 [-6.2, 7.7] |
| | Pinning + hints | **+27.9** [20.2, 35.6] | **+11.5** [4.3, 18.7] | +1.0 [-5.8, 7.2] |
| | Chronological + hints | **+14.9** [5.8, 24.0] | +8.7 [0.5, 16.8] | **+9.6** [4.8, 14.4] |
| | LLM transitions | **+21.2** [12.5, 30.3] | +1.0 [-4.3, 6.2] | **+10.1** [5.3, 15.4] |
| No unsafe action | Compaction + hints | **+17.3** [10.1, 24.5] | **+36.5** [28.4, 44.2] | +5.3 [-2.9, 13.5] |
| | Pinning + hints | **+19.2** [12.0, 26.0] | **+27.9** [20.7, 35.1] | +2.4 [-5.8, 10.6] |
| | Chronological + hints | **+15.9** [10.1, 22.6] | **+12.5** [4.8, 20.7] | **+12.0** [5.3, 19.2] |
| | LLM transitions | **+11.5** [5.3, 17.8] | +1.4 [-1.4, 4.3] | **+23.6** [15.4, 31.7] |

Bold marks a confirmed or significant test after Holm correction. 17 of 24 tests are confirmed or significant. The Llama comparison with the chronological ledger and hints just misses for full correctness (Holm p = 0.080). For full correctness, the pattern matches the planned probe-level tests exactly: Qwen beats all four baselines; Llama beats compaction and pinning with hints but not the event log or LLM transitions; Mistral beats only the baselines that share its extracted events.

### Share of dialogues on Confirm (%)

| Condition | Qwen: all correct | Qwen: no unsafe act | Llama: all correct | Llama: no unsafe act | Mistral: all correct | Mistral: no unsafe act |
|---|---:|---:|---:|---:|---:|---:|
| Full history (reference) | 19.7 | 86.5 | 42.3 | 72.6 | 24.0 | 66.8 |
| Ordinary compaction | 11.1 | 72.6 | 31.2 | 68.8 | 18.8 | 64.4 |
| Compaction + hints | 14.9 | 70.7 | 14.4 | 43.8 | 18.3 | 70.7 |
| Constraint pinning | 15.4 | 82.7 | 29.3 | 77.4 | 15.9 | 68.8 |
| Pinning + hints | 12.0 | 68.8 | 21.6 | 52.4 | 17.8 | 73.6 |
| Chronological ledger | 26.4 | 79.3 | 38.5 | 64.4 | 8.2 | 57.7 |
| Chronological + hints | 25.0 | 72.1 | 24.5 | 67.8 | 9.1 | 63.9 |
| LLM transitions | 18.8 | 76.4 | 32.2 | 78.8 | 8.7 | 52.4 |
| LADL v1 | 39.9 | 88.0 | 33.2 | 80.3 | 18.8 | 76.0 |
| LADL v2 | 41.3 | 90.9 | 47.1 | 81.2 | 13.0 | 74.5 |
| LADL, gold events | 53.8 | 96.6 | 52.9 | 87.0 | 45.7 | 87.0 |

Dialogue success is much lower than probe accuracy, because a Confirm dialogue has 3 to 6 decisions and one mistake fails it. On Test, Fresh, and Confirm, a LADL variant has the most fully correct dialogues of any compacted condition for every model: extraction v2 for Qwen on Confirm and Fresh and for Llama on Confirm and Test, v1 for Qwen on Test, and the version without hints for Llama on Fresh and for Mistral on all three datasets (27.4% with v2 extraction on Confirm). Gold events still leave about half of all dialogues with at least one wrong decision, which is the remaining policy error.

For Qwen, errors also come much later with LADL. After four decisions, 43.9% of Qwen's LADL v1 dialogues are still error-free, against 14.3% with ordinary compaction (Llama: 38.8% against 34.2%; Mistral: 19.9% against 22.4%).

### Tokens and calls per dialogue

From cache replays of the deterministic Confirm v1 runs, with usage counted per condition. State-recall questions are a diagnostic and are excluded.

| Condition | Calls | Prompt tokens | Upkeep tokens | Memory tokens at decision | Decision prompt tokens |
|---|---:|---:|---:|---:|---:|
| Full history (reference) | 4.4 | 4.7k–5.3k | 0 | 0 | 1,059–1,199 |
| Ordinary compaction | 7.2 | 4.5k–5.1k | 1.1k–1.4k | 111–165 | 815–931 |
| Constraint pinning | 23.3 | 7.9k–11.5k | 5.0k–9.8k | 167–335 | 870–1,127 |
| Chronological ledger | 23.3 | 26.0k–30.2k | 22.3k–26.0k | 262–325 | 961–1,115 |
| LLM transitions | 29.5–33.5 | 28.4k–35.8k | 25.4k–33.2k | 229–307 | 931–1,098 |
| LADL | 23.3 | 25.9k–30.2k | 22.3k–26.0k | 235–307 | 936–1,098 |
| LADL, gold events | 7.2 | 5.0k–5.7k | 1.1k–1.3k | 245–285 | 946–1,076 |

Ranges span the three models. Upkeep tokens are prompt plus completion tokens of the summary, pinning, extraction, and transition calls. LADL makes 16.1 extraction calls per dialogue, one per user or tool turn, each with a prompt of 1,300 to 1,500 tokens, most of it the fixed extraction instructions. Its upkeep is therefore 16 to 21 times that of ordinary compaction, and its total prompt tokens 5 to 6 times. Confirm dialogues are short: a decision prompt with the full history has only 1,060 to 1,200 tokens, so full history is the cheapest condition here. Compaction pays off only in longer conversations.

### Latency, one request at a time

First 8 Confirm dialogues, each condition from an empty cache, all three models on the same H200 node.

| Condition | Seconds per dialogue (Qwen / Llama / Mistral) | Seconds per decision | Upkeep seconds per user turn |
|---|---|---|---|
| Full history | 3.3 / 2.0 / 2.2 | 0.82 / 0.51 / 0.54 | 0 |
| Ordinary compaction | 7.1 / 4.1 / 4.2 | 0.66 / 0.32 / 0.41 | 0.27 / 0.18 / 0.16 |
| Constraint pinning | 16.2 / 13.8 / 21.2 | 0.72 / 0.35 / 0.38 | 0.82 / 0.76 / 1.21 |
| Chronological ledger | 14.0 / 6.7 / 7.0 | 1.29 / 0.60 / 0.60 | 0.55 / 0.27 / 0.28 |
| LLM transitions | 20.6 / 9.4 / 13.9 | 0.78 / 0.50 / 0.41 | 1.08 / 0.46 / 0.75 |
| LADL | 12.4 / 6.2 / 6.1 | 0.87 / 0.51 / 0.42 | 0.55 / 0.25 / 0.27 |

LADL takes 1.4 to 1.8 times as long per dialogue as ordinary compaction and 0.3 to 0.8 times as long as pinning. Extraction does not have to delay a decision: it can run after each turn while the user is reading. These are single measurements on a shared node with batch-invariant kernels, so absolute times are only indicative; Qwen's per-decision times vary across conditions more than their prompt lengths explain.

## B. Extraction-noise dose-response

### Accuracy (%) as extraction gets worse

Each cell gives LADL / LADL without hints / chronological ledger with hints. Event-free references from the same deterministic runs: ordinary compaction 63.1, 75.5, and 68.1; pinning 68.8, 74.2, and 69.8 (Qwen, Llama, Mistral).

| Precision (recall 1.0) | Qwen | Llama | Mistral |
|---|---|---|---|
| 1.0 (perfect) | 87.3 / 81.2 / 78.4 | 85.9 / 82.8 / 81.7 | 87.8 / 82.1 / 77.7 |
| 0.9 | 85.2 / 82.0 / 75.3 | 83.4 / 81.7 / 78.1 | 83.5 / 81.9 / 76.4 |
| 0.8 | 83.4 / 81.1 / 71.7 | 80.3 / 81.8 / 74.6 | 80.0 / 79.7 / 73.1 |
| 0.7 | 78.4 / 81.1 / 71.3 | 77.2 / 82.1 / 72.6 | 77.4 / 78.7 / 69.0 |
| 0.6 | 75.9 / 79.7 / 70.3 | 73.3 / 80.1 / 68.7 | 72.7 / 76.4 / 65.8 |
| 0.5 | 71.2 / 76.7 / 65.0 | 70.1 / 78.5 / 66.2 | 67.1 / 75.4 / 63.4 |
| 0.4 | 68.2 / 75.9 / 62.6 | 65.3 / 76.6 / 62.6 | 59.6 / 70.9 / 60.2 |

| Recall (precision 1.0) | Qwen | Llama | Mistral |
|---|---|---|---|
| 0.9 | 84.1 / 78.3 / 78.4 | 83.1 / 80.8 / 80.7 | 83.5 / 78.9 / 74.7 |
| 0.8 | 80.8 / 75.3 / 77.1 | 81.7 / 79.4 / 80.3 | 79.9 / 76.7 / 74.0 |
| 0.7 | 77.9 / 74.6 / 75.8 | 79.7 / 79.9 / 79.1 | 77.2 / 74.2 / 73.4 |
| 0.6 | 76.0 / 72.9 / 73.9 | 79.1 / 79.1 / 76.7 | 74.1 / 72.9 / 71.6 |
| 0.5 | 73.4 / 72.3 / 72.9 | 77.4 / 77.6 / 75.0 | 71.8 / 71.6 / 71.0 |

The realized precision and recall of every setting are within 0.011 of the target. The plot of these curves, with the event-free references and the real extractors, is `results/followup/fig_noise.pdf`.

### Planned tests (family B, Holm over 9 tests)

Each test is a difference in differences, in points: the effect at the noisy setting minus the effect with perfect extraction.

| Test | Qwen | Llama | Mistral |
|---|---|---|---|
| B1: hint effect at precision 0.5 (predicted negative) | **-11.7** [-15.9, -7.8] | **-11.6** [-15.5, -7.4] | **-14.0** [-17.6, -10.2] |
| B2: LADL minus chronological + hints, precision 0.5 | -2.7 [-7.0, 1.3] | -0.3 [-4.7, 3.9] | -6.3 [-11.3, -1.4] |
| B3: LADL minus chronological + hints, recall 0.7 | **-6.8** [-9.7, -3.7] | -3.7 [-7.3, -0.3] | **-6.2** [-10.4, -2.1] |

B1 is confirmed for all three models. With perfect extraction, hints add 3.1 to 6.1 points; at precision 0.5, they cost 5.5 to 8.4. B2 is not significant for any model after correction (Mistral, Holm p = 0.052), so false events do not hurt the reducer clearly more than the event log. B3 is significant for Qwen and Mistral: missed events shrink LADL's lead over the event log, because a missed creation or status change leaves the ledger wrong until a later event repairs it.

### Break-even, matched noise, and seed check

| | Qwen | Llama | Mistral |
|---|---|---|---|
| Precision where LADL equals ordinary compaction | ≤ 0.40 (below the grid) | 0.66 [0.54, 0.76] | 0.52 [0.45, 0.61] |
| Precision where LADL equals pinning | 0.42 [0.40, 0.53] | 0.63 [0.52, 0.72] | 0.55 [0.48, 0.63] |
| Real extractor precision, v1 / v2 | 0.884 / 0.905 | 0.857 / 0.912 | 0.519 / 0.426 |
| LADL, real minus matched noise, v1 | +0.8 [-2.4, 3.9] | -0.4 [-4.2, 3.4] | +1.0 [-2.3, 4.3] |
| LADL, real minus matched noise, v2 | -0.8 [-3.9, 2.4] | +1.2 [-1.0, 3.3] | -0.3 [-3.7, 3.3] |
| LADL, seed 1 minus seed 0 at precision 0.5 | -2.0 [-5.9, 1.7] | -1.9 [-5.5, 2.1] | -1.1 [-4.4, 2.1] |

- **Prediction for Qwen and Llama holds:** their real precision is well above their break-even points.
- **Prediction for Mistral is not supported as stated:** the plan predicted a break-even above Mistral's real v1 precision of 0.519. The estimate, 0.518, is essentially equal to it, which matches the real tie between Mistral's LADL v1 and ordinary compaction (-0.3 points). Mistral's v2 precision (0.426) is below the break-even, matching the real loss of LADL v2.
- **Matched noise reproduces real LADL accuracy** for all six model-prompt pairs, within 1.2 points and with every interval covering zero. The error rates of the real extractors explain their effect on LADL. For other conditions the structure of real errors matters somewhat: Mistral's real v1 errors are more harmful than random ones for the chronological ledger with hints and for LADL without hints (-4.9 and -3.5 points), while Llama's real v1 errors are less harmful for the chronological ledger without hints and for LADL without hints (+4.8 and +2.8).
- **Seed variation:** a second noise draw changes LADL by 1.1 to 2.0 points, inside the intervals.

**Exploratory, added after results were seen:** with perfect extraction, the ledger shows item IDs `I1`, `I2`, ... instead of the gold IDs such as `F0P`; nothing else in the prompt changes. This makes no difference for Qwen (-0.1) or Llama (-0.4), but raises Mistral by 3.2 [1.3, 5.0] points, from 84.6% to 87.8%. Mistral's decisions depend on surface details of the ledger.

## C. Swapping extractor and decision model

LADL accuracy (%) by decision model (rows) and extraction source (columns). Diagonal cells use the model's own extraction and come from the deterministic runs.

| Decision model | Qwen v1 | Qwen v2 | Llama v1 | Llama v2 | Mistral v1 | Mistral v2 |
|---|---:|---:|---:|---:|---:|---:|
| Qwen | 81.3 | 81.0 | 78.9 | 83.2 | 69.1 | 64.7 |
| Llama | 79.8 | 82.5 | 78.1 | 84.2 | 66.7 | 65.2 |
| Mistral | 80.6 | 83.0 | 79.5 | 84.3 | 67.8 | 63.1 |
| Extraction precision / recall | 0.884 / 0.843 | 0.905 / 0.871 | 0.857 / 0.870 | 0.912 / 0.935 | 0.519 / 0.814 | 0.426 / 0.826 |

### Planned tests (family C, Holm over 12 tests, all confirmed)

| Comparison | Difference |
|---|---|
| Mistral deciding, Qwen v1 minus own v1 extraction | +12.8 [9.4, 16.1] |
| Mistral deciding, Qwen v2 minus own v2 extraction | +19.9 [16.7, 23.1] |
| Mistral deciding, Llama v1 minus own v1 extraction | +11.7 [8.0, 15.2] |
| Mistral deciding, Llama v2 minus own v2 extraction | +21.2 [17.7, 24.9] |
| Mistral deciding, LADL with Qwen v2 minus Mistral's ordinary compaction | +14.9 [11.3, 18.5] |
| Mistral deciding, LADL with Qwen v2 minus Mistral's pinning | +13.2 [9.4, 17.1] |
| Mistral deciding, LADL with Llama v2 minus Mistral's ordinary compaction | +16.2 [12.5, 20.1] |
| Mistral deciding, LADL with Llama v2 minus Mistral's pinning | +14.5 [11.0, 18.1] |
| Qwen deciding, Mistral v1 minus own v1 extraction | -12.2 [-16.2, -8.7] |
| Qwen deciding, Mistral v2 minus own v2 extraction | -16.3 [-21.0, -11.9] |
| Llama deciding, Mistral v1 minus own v1 extraction | -11.4 [-14.9, -7.7] |
| Llama deciding, Mistral v2 minus own v2 extraction | -19.0 [-22.9, -15.3] |

Every Holm-adjusted p is 0.012, the smallest value 2,000 resamples can give across 12 tests.

**Exploratory.** In an additive decomposition of the 3 × 6 LADL table, the extraction source accounts for 99% of the spread and the decision model for 0%; each decision model averages 76.1% to 76.4% across the six sources. Averaged over extraction versions, Mistral's extraction lowers LADL by 14 to 16 points against Qwen's and Llama's extraction, the chronological ledger by 12 to 18 points, and LADL without hints by only 4.5 to 7 points.

## Implications

- The case for LADL holds once extraction is good enough. The break-even precision against ordinary compaction is at most 0.4 to 0.66 depending on the decision model, and Qwen's and Llama's extractors are at 0.86 to 0.91.
- The practical recipe is to run extraction with the most precise extractor available, which need not be the model that makes decisions. A 7B model with Llama's extraction matched Llama's own LADL accuracy.
- When extraction precision is unknown or low, LADL without action hints is the safer choice: it degrades far less under false events.
- LADL's cost is the per-turn extraction call. It can run off the critical path, and prefix caching of the fixed instructions would reduce it further, but neither was measured here.

## Limitations

- All data are synthetic Confirm dialogues. Noise was injected into gold events with a fixed type mix taken from the Test split; real extractors make errors with other structure, such as wrong attributes on a correct event.
- The break-even points interpolate between a 0.1-wide grid with one noise draw per level. The seed check suggests about 2 points of draw-to-draw variation.
- Latency was measured once per condition on 8 dialogues on a shared node; it is a rough comparison only.
- The dialogue-level tests use the same decisions as the probe-level tests, so they are not independent confirmation.
- The ID-naming effect for Mistral was found after seeing results and needs its own test before it is claimed.

## Reproduce

Run from the project directory on PACE-ICE. Repeat the GPU jobs with `configs/llama8b.yaml` and `configs/mistral7b.yaml`.

```bash
sbatch scripts/pace_replay.sbatch qwen2.5-7b-det1-pace-confirm cache/llm_qwen7b_det1.sqlite   # replay with the new code
sbatch scripts/pace_events_replay.sbatch                                                     # --events-from check
LIMIT=8 RUN_TAG=-fupA CACHE_SUFFIX=fupA sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml followup-pilot
LIMIT=8 RUN_TAG=-fupB CACHE_SUFFIX=fupB MAX_CONCURRENCY=64 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml followup-pilot
CACHE_SUFFIX=followup sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml noise,swap
LIMIT=8 CACHE_SUFFIX=latency sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml latency
sbatch scripts/pace_replay.sbatch qwen2.5-7b-pace-confirm-noise cache/llm_qwen7b_followup.sqlite
```

A job stopped by its time limit is finished by resubmitting it with `SKIP_EXISTING=1` and the same `CACHE_SUFFIX`.
The three latency jobs were pinned to one node with `-w atl1-1-03-014-23-0`, so their times are comparable.

After copying the run directories and the replay metadata back:

```bash
python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det
python -m src.eval.dialogue_report --runs results/runs_det --replays results/replay_followup/det_confirm --out results/followup/dialogue
python -m src.eval.followup_report --runs results/runs_det --out results/followup
```

## AI assistance

Claude (Anthropic) designed these experiments with the team's direction, implemented the code, ran the PACE jobs, and drafted this note from the generated result files. This is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
