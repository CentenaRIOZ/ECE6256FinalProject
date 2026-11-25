# PACE-ICE Control Experiments

This note explains the control experiments first run on PACE-ICE on November 21, 2026, and what their results do and do not support. The numbers below come from deterministic reruns of the same experiments on November 24-25 (run tag `-det1`), which reproduce exactly. The first runs were not deterministic; [`reproducibility.md`](reproducibility.md) lists what changed. The original local results in `results/runs/qwen2.5-7b`, `results/runs/llama3.1-8b`, and their `-strict` variants are unchanged.

## Summary

- **The full LADL method is consistently better for Qwen2.5-7B.** On 52 new timelines, it beats all four compacted baselines by 5.3 to 17.4 points after Holm correction.
- **The gain does not generalize cleanly to Llama-3.1-8B.** On the new timelines, LADL is confirmed better only than LLM-written transitions (+3.6 points). Its lead over pinning (+4.5) misses the corrected threshold, and it trails the chronological ledger (-3.7, not significant after correction).
- **Action hints help Qwen and hurt Llama.** Removing directives such as "do NOT perform" lowers Qwen by 4.1 points and leaves it level with the chronological ledger (+1.3, not significant). For Llama, removing them raises accuracy by 5.6 points.
- **The memory-budget overrun did not drive the results.** A hard cap changes each condition's accuracy by at most 0.6 points.
- **The post-hoc strict-hedging fix is confirmed for Llama.** It gains 3.3 points on new timelines after Holm correction, and does not change Qwen.

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
- **Compute.** One NVIDIA H200 per job, vLLM 0.34.0 with batch-invariant kernels, PyTorch 2.14.0, and Transformers 5.22.2, at temperature 0 with seed 0. Model revisions are pinned in `configs/model_revisions.yaml`, and all package versions are in `scripts/pace_env_freeze.txt`.

## Results

### Accuracy under the hard cap

Four-way decision accuracy (%) with timeline-clustered 95% confidence intervals. "Test" is the original test split and "Fresh" is the new timelines.

| Condition | Qwen Test | Qwen Fresh | Llama Test | Llama Fresh |
|---|---|---|---|---|
| Full history (no compaction) | 60.1 [54.9, 64.7] | 57.7 [53.2, 61.9] | 81.9 [78.3, 85.1] | 84.5 [81.5, 87.4] |
| Ordinary compaction | 60.1 [55.9, 64.0] | 59.2 [55.7, 62.8] | 72.0 [69.3, 74.7] | 73.9 [70.4, 77.3] |
| Constraint pinning | 62.5 [58.1, 66.7] | 63.8 [59.9, 67.8] | 68.8 [65.1, 72.6] | 72.6 [70.1, 74.9] |
| Chronological event ledger | 70.0 [66.6, 73.3] | 71.3 [67.4, 74.9] | 78.6 [74.6, 82.2] | 80.8 [77.5, 83.9] |
| Typed ledger, LLM transitions | 70.0 [65.9, 74.0] | 71.4 [68.2, 74.7] | 69.0 [64.2, 73.8] | 73.5 [70.4, 76.6] |
| **LADL** | **74.1 [70.3, 77.7]** | **76.6 [73.9, 79.3]** | 72.4 [66.9, 77.8] | 77.1 [73.7, 80.4] |
| LADL without action hints | 69.3 [65.1, 73.2] | 72.6 [69.0, 76.2] | 75.9 [71.7, 80.1] | 82.7 [79.6, 85.6] |
| LADL, strict hedging (post hoc) | 74.1 [70.3, 77.7] | 76.8 [73.9, 79.4] | 78.0 [73.4, 82.6] | 80.4 [77.8, 83.0] |
| LADL, gold events | 82.2 [79.1, 85.2] | 83.7 [81.2, 85.9] | 83.4 [79.9, 86.7] | 83.3 [80.5, 86.1] |

### Confirmation tests

Paired differences in percentage points. The Test column gives the sign each effect needs; Fresh differences have 95% confidence intervals, and `*` marks Holm-corrected p < 0.05.

| Comparison | Qwen Test | Qwen Fresh | Confirmed | Llama Test | Llama Fresh | Confirmed |
|---|---:|---|---|---:|---|---|
| LADL - ordinary compaction | +14.0 | +17.4* [+13.1, +21.7] | Yes | +0.5 | +3.2 [-0.5, +6.9] | No |
| LADL - pinning | +11.6 | +12.8* [+8.7, +17.0] | Yes | +3.6 | +4.5 [+0.7, +8.4] | No |
| LADL - chronological ledger | +4.1 | +5.4* [+2.2, +8.6] | Yes | -6.2 | -3.7 [-7.5, -0.1] | No |
| LADL - LLM transitions | +4.1 | +5.3* [+2.4, +8.0] | Yes | +3.5 | +3.6* [+1.5, +5.7] | Yes |
| LADL - LADL without hints | +4.8 | +4.1* [+1.2, +6.7] | Yes | -3.5 | -5.6* [-9.0, -2.3] | Yes (hints hurt) |
| Strict hedging - LADL | 0.0 | +0.1 [0.0, +0.3] | No | +5.6 | +3.3* [+1.6, +5.3] | Yes |

For Llama, the LADL-minus-no-hints effect is negative on both splits, so the confirmed effect is that hints lower accuracy.

### Effect of each control

**Hard cap.** No probe exceeds the budget after the fix. Compared with the uncapped PACE run, no condition moves by more than 0.6 points, so the original overrun does not explain the main result.

**Action hints.** For Qwen, the ledger without hints is no better than the chronological ledger (+1.3 [-1.9, +4.7]) or LLM-written transitions (+1.2 [-1.6, +4.0]) on fresh data. It still beats ordinary compaction (+13.4 [+9.7, +17.0]) and pinning (+8.8 [+5.2, +12.8]). For Llama, removing hints raises accuracy by 5.6 points on fresh data. The no-hint ledger beats ordinary compaction (+8.8), pinning (+10.1), and LLM-written transitions (+9.2), but not the chronological ledger (+1.9 [-1.5, +5.1]).

**Memory budget.** On the original test split, Qwen's LADL advantage holds at all three budgets, while Llama trails the chronological ledger at all three:

| LADL minus | B=256 | B=384 | B=768 |
|---|---|---|---|
| Qwen, ordinary compaction | +20.8 [+16.7, +25.1] | +14.0 [+10.0, +17.7] | +18.4 [+14.2, +22.7] |
| Qwen, chronological ledger | +11.1 [+7.8, +14.8] | +4.1 [+0.4, +7.3] | +6.3 [+2.4, +10.2] |
| Llama, ordinary compaction | -0.9 [-7.1, +4.5] | +0.5 [-4.9, +5.6] | +1.7 [-5.7, +8.1] |
| Llama, chronological ledger | -6.5 [-11.5, -1.4] | -6.2 [-12.2, -0.3] | -8.9 [-14.2, -3.8] |

**Compaction placement.** On fresh timelines, Qwen's pattern does not depend on where compaction occurs:

| LADL minus | Early | Spread | Late |
|---|---|---|---|
| Qwen, ordinary compaction | +16.9 [+12.6, +21.0] | +17.4 [+13.1, +21.7] | +23.5 [+19.0, +28.1] |
| Qwen, chronological ledger | +4.3 [+1.5, +7.1] | +5.4 [+2.2, +8.6] | +8.1 [+4.3, +12.0] |
| Llama, ordinary compaction | +0.9 [-2.6, +4.7] | +3.2 [-0.5, +6.9] | +3.8 [-0.9, +8.5] |
| Llama, chronological ledger | -1.9 [-5.6, +2.1] | -3.7 [-7.5, -0.1] | +2.1 [-2.5, +6.6] |

**RQ1: stale versus missing state.** For mutable items after at least one compaction on the test split, stale answers exceed a chance baseline under ordinary compaction: 30.3% of Qwen's wrong answers against 13.2% by chance, and 32.1% of Llama's against 15.8%. The rate is much higher with full history (54.5% and 55.7%), where nothing was compacted. Staleness is therefore a real error type, but compaction is not its main cause.

**RQ3: where errors come from.** On fresh timelines, bad extraction causes errors on 7.8% (Qwen) and 9.1% (Llama) of probes, and wrong decisions despite correct ledger state cause 15.6% and 13.8%. With gold events, 16.3% and 16.7% of decisions remain wrong. Llama's clearest weakness is approval extraction, with F1 0.62 against 0.92 for Qwen. `python -m src.eval.error_analysis` writes the full breakdown to `results/extended/error_analysis.md`.

**Cross-environment reproducibility.** The PACE no-cap rerun differs from the original local run by at most 2.7 accuracy points per condition. Individual decisions match on 69.1% to 95.6% of probes, depending on the condition. New and old probe logs should not be mixed in one paired comparison.

## How to interpret these results

**Supported**

- The complete LADL method improves action accuracy for Qwen over all compacted baselines, across budgets and compaction placements.
- LADL improves on LLM-written transitions for both models on fresh timelines.
- Strict hedging improves Llama on fresh timelines.

**Not supported**

- LADL does not reliably improve Llama over ordinary compaction or pinning, and Llama's LADL trails the chronological ledger on the test split at every budget.
- Derived lifecycle state without action hints does not beat a chronological event log for either model.
- Compaction is not shown to be the primary cause of stale state.

**Changed from the first, nondeterministic runs.** Qwen's five confirmed effects are unchanged. For Llama, the first run confirmed only LADL over pinning; the deterministic run confirms LADL over LLM-written transitions, the harm from hints, and strict hedging instead. These Llama effects sit near the threshold, so none of them should carry a main claim.

## Limitations

- The fresh timelines reuse the held-out template pool. Of 371 distinct fresh event utterances, 164 also appear in the original test split, so this tests new combinations rather than new language.
- The fresh data has no paraphrases.
- Each model uses one prompt, and gold labels share the transition rules used by LADL.
- The budget is a cap rather than equal usage. Ordinary compaction averages 128 (Qwen) and 183 (Llama) memory tokens on the test split, against 254 and 292 for LADL.
- The execute versus do-not-execute metric reported in the result files was added after the first analysis and should be treated as a sensitivity check.
- The confirmation rule was fixed before the first runs, whose results had been seen before the deterministic reruns. The reporting rule in [`deterministic_rerun_plan.md`](deterministic_rerun_plan.md) was fixed before the deterministic runs.

## Reproduce

Run the setup and experiment jobs from the project directory on PACE-ICE. The Slurm account, partition, and QoS in the scripts are specific to this course allocation. Jobs serve deterministically and refuse to overwrite existing result files.

```bash
python -m src.generation.build --fresh --out data/fresh --n-per-family 4 --seed 20261121
sbatch scripts/pace_setup.sbatch
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml full,extended
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/llama8b.yaml full,extended
```

After copying `results/runs/*-det1-pace-*` back, regenerate the reports:

```bash
python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det
python -m src.eval.control_report --budget 384 --runs results/runs_det --out results/det/controls
python -m src.eval.extended_report --runs results/runs_det --out results/det/extended
python -m src.eval.error_analysis --runs results/runs_det --out results/det/extended
```

## Files

Paths under `results/` are generated locally by the commands above and are not stored in git.

| Path | Contents |
|---|---|
| `results/det/controls/` | Original versus PACE, hard-cap, no-hint, and RQ1 analyses |
| `results/det/extended/` | Fresh confirmation, budget sweep, placement, and error analyses |
| `results/runs/*-det1-pace-nocap`, `*-det1-pace-hardcap` | Raw probe outputs on the original test split |
| `results/runs/*-det1-pace-fresh-*` | Raw probe outputs on the fresh timelines |
| `data/fresh/` | Fresh timelines and their three compaction placements |
| `scripts/pace_setup.sbatch`, `scripts/pace_experiment.sbatch` | PACE-ICE environment and experiment jobs |
| `src/eval/control_report.py`, `extended_report.py`, `error_analysis.py`, `robustness.py`, `tagged_runs.py` | Analysis and table generation |

## AI assistance

Claude (Anthropic) implemented these controls, ran the PACE jobs, and drafted this note from the generated result files. This note is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
