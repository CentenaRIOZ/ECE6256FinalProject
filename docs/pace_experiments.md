# PACE-ICE Control Experiments

This note explains the follow-up experiments run on PACE-ICE on November 21, 2026, and what their results do and do not support. The original results in `results/runs/qwen2.5-7b`, `results/runs/llama3.1-8b`, and their `-strict` variants are unchanged.

## Summary

- **The full LADL method is consistently better for Qwen2.5-7B.** On 52 new timelines, it beats all four compacted baselines by 6.7 to 19.7 points after Holm correction.
- **The gain does not generalize cleanly to Llama-3.1-8B.** On the new timelines, LADL is confirmed better only than constraint pinning (+5.8 points).
- **Action hints are a major part of the Qwen gain.** Removing directives such as "do NOT perform" lowers Qwen by 8.6 points and leaves it level with the chronological ledger (-1.1 points, not significant).
- **The memory-budget overrun did not drive the results.** A hard cap changes each condition's accuracy by at most 1.5 points.
- **The post-hoc strict-hedging fix is not confirmed.** It gains 3.3 points for Llama on new timelines, but the corrected p-value is 0.066.

## Why these experiments were added

The first analysis left four open threats:

1. The 384-token budget was not strictly enforced because a persistent block could grow after a compaction.
2. The LADL ledger contained action directives that the chronological ledger did not, so state tracking and prompt wording were confounded.
3. The strict-hedging variant was designed after inspecting test errors, so it needed new data.
4. The proposal promised a test of compaction location, which had not been run.

## What was run

Each experiment below ran on both models with the same 11 memory conditions.

| Experiment | Data | Budget | Purpose |
|---|---|---|---|
| PACE rerun, no cap | Original test split, 664 probes | 384 | Measure cross-environment reproducibility |
| PACE rerun, hard cap | Original test split, 664 probes | 384 | Enforce the equal-budget premise |
| Budget sweep, hard cap | Original test split, 664 probes | 256, 768 | Check sensitivity to memory size |
| Fresh confirmation, hard cap | 52 new timelines, 912 probes | 384 | Test the main effects on unseen timelines |
| Compaction placement, hard cap | The same 912 fresh probes | 384 | Compare spread, early, and late compaction |

### Method details

- **Hard cap.** If summary plus persistent block exceeds the budget, the summary is shortened. The ledger is kept. Later compactions see only the shortened summary.
- **No-hint ablation (`lifecycle_nohint`).** The reducer and state are unchanged. Status lines say `ACTIVE`, `REVOKED`, `WAITING`, and so on, without instructions such as "do NOT perform" or "ask the user before acting".
- **Fresh timelines.** There are 52 timelines, 4 for each of the 13 primary families, rendered into 208 dialogues without paraphrases (seed 20261121). This also fixes an imbalance in the original split, where every timeline with `REV1` as its primary family fell in dev.
- **Compaction placement.** Dialogue text and gold labels are identical across placements. Only the compaction points move: across the whole dialogue (`spread`), within the first half (`early`), or within the second half (`late`).
- **Confirmation rule, fixed before the fresh runs.** Six comparisons per model were tested with four-way accuracy as the primary metric. Holm correction ran over all 12 tests. An effect counts as confirmed only if it has the same sign as on the original test split and its corrected p-value is below 0.05.
- **Compute.** Eight jobs used one NVIDIA H200 each, for about 84 minutes or 1.4 GPU-hours in total, including vLLM startup and smoke tests. Software was vLLM 0.34.0, PyTorch 2.14.0, and Transformers 5.22.2, at temperature 0 with seed 0. All package versions are in `scripts/pace_env_freeze.txt`.

## Results

### Accuracy under the hard cap

Four-way decision accuracy (%) with timeline-clustered 95% confidence intervals. "Test" is the original test split and "Fresh" is the new timelines.

| Condition | Qwen Test | Qwen Fresh | Llama Test | Llama Fresh |
|---|---|---|---|---|
| Full history (no compaction) | 60.8 [56.0, 65.2] | 57.2 [53.2, 61.1] | 81.3 [77.6, 84.5] | 83.4 [80.3, 86.4] |
| Ordinary compaction | 57.4 [53.5, 61.1] | 58.3 [54.6, 61.8] | 72.7 [69.4, 76.0] | 73.2 [70.0, 76.3] |
| Constraint pinning | 63.7 [59.5, 67.8] | 62.4 [59.2, 65.5] | 68.4 [65.8, 70.9] | 71.6 [69.2, 73.9] |
| Chronological event ledger | 68.2 [64.2, 71.9] | 70.6 [67.3, 73.8] | 78.3 [74.1, 82.2] | 78.4 [75.0, 81.7] |
| Typed ledger, LLM transitions | 71.1 [66.7, 75.4] | 71.4 [67.7, 74.9] | 69.0 [64.3, 73.7] | 76.2 [73.1, 79.3] |
| **LADL** | **75.5 [71.4, 79.1]** | **78.1 [74.9, 81.0]** | 70.8 [65.3, 76.1] | 77.4 [73.8, 81.1] |
| LADL without action hints | 68.8 [65.3, 72.2] | 69.5 [66.1, 72.7] | 74.8 [70.9, 78.7] | 79.2 [76.0, 82.2] |
| LADL, strict hedging (post hoc) | 75.3 [71.2, 79.0] | 78.5 [75.4, 81.4] | 77.4 [73.1, 81.4] | 80.7 [77.7, 83.8] |
| LADL, gold events | 82.8 [79.8, 85.7] | 83.8 [81.4, 86.0] | 83.3 [79.8, 86.5] | 83.8 [81.0, 86.6] |

### Confirmation tests

Paired differences in percentage points, with 95% confidence intervals on the fresh timelines. `*` marks Holm-corrected p < 0.05.

| Comparison | Qwen Test | Qwen Fresh | Confirmed | Llama Test | Llama Fresh | Confirmed |
|---|---:|---|---|---:|---|---|
| LADL - ordinary compaction | +18.1* | +19.7* [+15.2, +24.2] | Yes | -2.0 | +4.2 [+0.5, +7.7] | No |
| LADL - pinning | +11.7* | +15.7* [+11.8, +19.7] | Yes | +2.4 | +5.8* [+2.3, +9.2] | Yes |
| LADL - chronological ledger | +7.2* | +7.5* [+4.1, +10.7] | Yes | -7.5* | -1.0 [-4.6, +2.5] | No |
| LADL - LLM transitions | +4.4 | +6.7* [+3.1, +10.5] | Yes | +1.8 | +1.2 [-1.8, +4.0] | No |
| LADL - LADL without hints | +6.6* | +8.6* [+5.6, +11.5] | Yes | -4.1 | -1.8 [-5.1, +1.5] | No |
| Strict hedging - LADL | -0.2 | +0.4 [-1.4, +2.2] | No | +6.6* | +3.3 [+0.7, +6.1] | No |

### Effect of each control

**Hard cap.** No probe exceeds the budget after the fix. Compared with the uncapped PACE run, no condition moves by more than 1.5 points, so the original overrun does not explain the main result.

**Action hints.** For Qwen, the ledger without hints is no better than the chronological ledger (-1.1 [-4.6, +2.3]) or LLM-written transitions (-1.9 [-5.4, +1.5]) on fresh data. It still beats ordinary compaction (+11.2 [+7.0, +15.1]) and pinning (+7.1 [+3.3, +10.8]). For Llama, removing hints does not significantly change accuracy (+1.8 points in favor of no hints on fresh data).

**Memory budget.** On the original test split, Qwen's LADL advantage holds at all three budgets:

| LADL minus | B=256 | B=384 | B=768 |
|---|---|---|---|
| Qwen, ordinary compaction | +19.0 [+14.7, +23.0] | +18.1 [+13.6, +22.4] | +20.5 [+16.2, +25.2] |
| Qwen, chronological ledger | +10.8 [+6.4, +15.4] | +7.2 [+3.4, +11.3] | +8.0 [+3.9, +11.9] |
| Llama, ordinary compaction | -3.5 [-8.5, +1.4] | -2.0 [-7.8, +3.6] | +3.0 [-2.2, +8.2] |
| Llama, chronological ledger | -8.1 [-13.2, -2.8] | -7.5 [-13.0, -2.2] | -2.6 [-7.4, +2.6] |

**Compaction placement.** On fresh timelines, the pattern does not depend on where compaction occurs:

| LADL minus | Early | Spread | Late |
|---|---|---|---|
| Qwen, ordinary compaction | +16.9 [+13.9, +19.9] | +19.7 [+15.2, +24.2] | +22.1 [+18.1, +26.3] |
| Qwen, chronological ledger | +5.9 [+2.6, +9.8] | +7.5 [+4.1, +10.7] | +7.2 [+3.5, +11.1] |
| Llama, ordinary compaction | +2.3 [-1.6, +6.2] | +4.2 [+0.5, +7.7] | +3.9 [-0.4, +8.1] |
| Llama, chronological ledger | -1.4 [-5.3, +2.2] | -1.0 [-4.6, +2.5] | +0.9 [-3.3, +4.8] |

**RQ1: stale versus missing state.** For mutable items after at least one compaction, stale answers exceed a chance baseline under ordinary compaction: 24.7% of Qwen's wrong answers against 13.4% by chance, and 26.4% of Llama's against 15.6%. The rate is much higher with full history (55.0% and 54.6%), where nothing was compacted. Staleness is therefore a real error type, but compaction is not its main cause.

**RQ3: where errors come from.** On fresh timelines, bad extraction causes errors on 8.0% (Qwen) and 9.1% (Llama) of probes, and wrong decisions despite correct ledger state cause 13.9% and 13.5%. With gold events, 16.2% of decisions remain wrong for both models. Llama's clearest weakness is approval extraction, with F1 0.61 against 0.91 for Qwen. `python -m src.eval.error_analysis` writes the full breakdown to `results/extended/error_analysis.md`.

**Cross-environment reproducibility.** The PACE rerun differs from the original run by at most 2.7 accuracy points per condition. Individual decisions match on 73.0% to 96.7% of probes, depending on the condition. New and old probe logs should not be mixed in one paired comparison.

## How to interpret these results

**Supported**

- The complete LADL method improves action accuracy for Qwen over all compacted baselines, across budgets and compaction placements.
- LADL improves on constraint pinning for both models on fresh timelines.

**Not supported**

- LADL does not reliably improve Llama over ordinary compaction, the chronological ledger, or LLM-written transitions.
- Derived lifecycle state without action hints does not beat a chronological event log for either model.
- The strict-hedging fix remains exploratory.
- Compaction is not shown to be the primary cause of stale state.

## Limitations

- The fresh timelines reuse the held-out template pool. Of 371 distinct fresh event utterances, 164 also appear in the original test split, so this tests new combinations rather than new language.
- The fresh data has no paraphrases.
- Each model uses one prompt, and gold labels share the transition rules used by LADL.
- The budget is a cap rather than equal usage. Ordinary compaction averages 131 (Qwen) and 183 (Llama) memory tokens on the test split, against 254 and 291 for LADL.
- The execute versus do-not-execute metric reported in the result files was added after the first analysis and should be treated as a sensitivity check.

## Reproduce

Run the setup and experiment jobs from the project directory on PACE-ICE. The Slurm account, partition, and QoS in the scripts are specific to this course allocation. Jobs refuse to overwrite existing result files.

```bash
python -m src.generation.build --fresh --out data/fresh --n-per-family 4 --seed 20261121
sbatch scripts/pace_setup.sbatch
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml full
sbatch scripts/pace_experiment.sbatch configs/llama8b.yaml full
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml extended
sbatch scripts/pace_experiment.sbatch configs/llama8b.yaml extended
```

After copying `results/runs/*-pace-*` back, regenerate the reports:

```bash
python -m src.eval.control_report --budget 384 --out results/controls
python -m src.eval.extended_report --out results/extended
python -m src.eval.error_analysis --out results/extended
python -m src.eval.milestone_tables --budget 384 --out paper/tables
```

## Files

Paths under `results/` are generated locally by the commands above and are not stored in git.

| Path | Contents |
|---|---|
| `results/controls/` | Original versus PACE, hard-cap, no-hint, and RQ1 analyses |
| `results/extended/` | Fresh confirmation, budget sweep, placement, and error analyses |
| `results/runs/*-pace-nocap`, `*-pace-hardcap` | Raw probe outputs on the original test split |
| `results/runs/*-pace-fresh-*` | Raw probe outputs on the fresh timelines |
| `data/fresh/` | Fresh timelines and their three compaction placements |
| `scripts/pace_setup.sbatch`, `scripts/pace_experiment.sbatch` | PACE-ICE environment and experiment jobs |
| `src/eval/control_report.py`, `extended_report.py`, `error_analysis.py`, `robustness.py`, `milestone_tables.py` | Analysis and table generation |

## AI assistance

Claude (Anthropic) implemented these controls, ran the PACE jobs, and drafted this note from the generated result files. This note is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
