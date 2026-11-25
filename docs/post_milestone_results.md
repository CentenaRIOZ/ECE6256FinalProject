# Post-Milestone Experiment Results

These experiments test the open questions from the milestone. The confirmation rule in [`post_milestone_confirmation_plan.md`](post_milestone_confirmation_plan.md) was fixed before the Confirm set was run. The third-model rule in [`third_model_plan.md`](third_model_plan.md) was fixed before any Mistral run.

All numbers below are copied from result files. Those files, the raw run records, and the freeze hashes are kept locally under `results/` and are not stored in git. The commands at the end regenerate them from the raw runs.

## Summary

- **LADL holds up on new wording for Qwen and Llama.** On 52 new timelines with separate actions and text, LADL beats 7 of 8 hint-parity baselines after Holm correction. The one exception is Llama against LLM-written transitions (0.0 points).
- **It does not hold for a third model with weak extraction.** On Mistral-7B, which played no part in development, LADL beats the event log and LLM-written transitions but not ordinary compaction or pinning. Mistral's extractor adds many events that did not happen. With gold events, Mistral's LADL reaches 86.7%, its best condition.
- **Extraction v2 fixes the main Llama failure but hurts Mistral.** For Llama, approval F1 rises from 0.60 to 0.89, and LADL accuracy rises by 5.0 points on Confirm. Qwen does not change meaningfully. For Mistral, v2 adds more false events and lowers LADL by 4.7 points.
- **LADL is not uniformly better than an event log.** With v2, Qwen leads the strongest baseline by 7.4 points on Confirm and 6.4 on Fresh, but only 0.9 on Test. Llama ranges from -0.6 to +4.3.
- **The milestone's action-hint conclusion needs revising.** Without hints, Qwen's ledger was level with the chronological log on Test and Fresh, but leads it by 5.0 points on Confirm.
- **The largest remaining error source depends on the model.** For Qwen and Llama it is the policy: even with gold events, about 14% of Confirm decisions are wrong. For Mistral it is extraction.

## What was run

All runs use PACE-ICE H200 GPUs, temperature 0, and the hard memory cap. Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct were used throughout. Mistral-7B-Instruct-v0.3 was added afterwards as a held-out model.

| Experiment | Data | Purpose |
|---|---|---|
| Extraction v1 versus v2 | Dev split, 208 probes | Develop and freeze the approval-extraction prompt (Qwen and Llama only) |
| Confirmation | New Confirm set, 916 probes | Run the planned tests on separate actions and text |
| Replication | Test (664) and Fresh (912) | Check v2 and hint-parity baselines on earlier data |
| v2 robustness | Test budgets 256, 384, 768; Fresh early, spread, late | Check sensitivity to budget and compaction location |
| Third model | All of the above except dev | Check whether the results depend on the development models |

Across the project, all PACE GPU jobs have used about 4.4 H200 GPU-hours, including startup and smoke tests. The Mistral runs took about 1.5 of them.

## Planned confirmation results

Four-way accuracy differences in percentage points on the Confirm set, with 95% confidence intervals. `Yes` means positive after Holm correction.

**Primary family: LADL v1 minus hint-parity baselines**

| Baseline | Qwen | Confirmed | Llama | Confirmed |
|---|---|---|---|---|
| Ordinary compaction + hints | +16.5 [12.9, 20.5] | Yes | +15.3 [11.0, 19.4] | Yes |
| Pinning + hints | +16.9 [13.6, 20.3] | Yes | +9.0 [5.5, 12.3] | Yes |
| Chronological ledger + hints | +6.8 [3.7, 9.8] | Yes | +5.0 [1.5, 8.8] | Yes |
| LLM-written transitions | +9.9 [5.9, 14.2] | Yes | 0.0 [-2.2, 2.2] | No |

Adding hints did not always strengthen a baseline. For Llama, ordinary compaction fell from 75.4% to 63.9%, pinning from 73.9% to 70.2%, and the chronological ledger from 80.2% to 74.1%. These tests therefore should not be read alone, so the unhinted comparisons below matter.

**Secondary family**

| Comparison | Qwen | Confirmed | Llama | Confirmed |
|---|---|---|---|---|
| LADL v1 - ordinary compaction | +18.4 [14.4, 22.5] | Yes | +3.7 [-0.1, 7.6] | No |
| LADL v1 - pinning | +13.8 [10.0, 17.6] | Yes | +5.2 [1.4, 9.3] | Yes |
| LADL v1 - chronological ledger | +8.3 [5.5, 11.2] | Yes | -1.1 [-5.1, 3.0] | No |
| LADL v1 - LADL without hints | +3.3 [0.9, 5.6] | Yes | -1.2 [-4.7, 2.3] | No |
| LADL v2 - LADL v1 | -0.2 [-2.4, 1.9] | No | +5.0 [2.2, 7.8] | Yes |
| Strict hedging - LADL v1 | -0.3 [-1.9, 1.3] | No | +4.7 [2.4, 7.1] | Yes |

## Third model: Mistral-7B-Instruct-v0.3

Mistral played no part in developing LADL, the baselines, or extraction v2. Its tests were fixed in [`third_model_plan.md`](third_model_plan.md) before any Mistral output existed. They use separate Holm families, so the two-model results above are unchanged.

**Planned tests on Confirm**

| Comparison | Difference | Confirmed |
|---|---|---|
| LADL v1 - ordinary compaction + hints | -1.1 [-5.1, 2.9] | No |
| LADL v1 - pinning + hints | +0.8 [-3.2, 4.5] | No |
| LADL v1 - chronological ledger + hints | +8.1 [4.4, 12.2] | Yes |
| LADL v1 - LLM-written transitions | +10.2 [6.8, 13.7] | Yes |
| LADL v2 - ordinary compaction | -2.3 [-7.5, 2.4] | No |
| LADL v2 - ordinary compaction + hints | -5.8 [-10.0, -1.6] | No |
| LADL v2 - pinning | -5.5 [-10.9, -0.1] | No |
| LADL v2 - pinning + hints | -3.9 [-8.5, 0.1] | No |
| LADL v2 - chronological ledger | +7.1 [3.6, 10.7] | Yes |
| LADL v2 - chronological ledger + hints | +3.4 [0.0, 6.6] | No |
| LADL v2 - LLM-written transitions | +14.1 [10.4, 17.8] | Yes |
| LADL v2 - LADL v1 | -4.7 [-8.5, -1.2] | No |
| LADL v1 - ordinary compaction | +2.4 [-1.7, 6.6] | No |
| LADL v1 - pinning | -0.8 [-5.2, 3.7] | No |
| LADL v1 - chronological ledger | +9.7 [5.6, 14.0] | Yes |
| LADL v1 - LADL v1 without hints | -5.0 [-8.5, -1.5] | No |
| Strict hedging - LADL v1 | -0.5 [-1.8, 0.7] | No |

LADL beats the two baselines that use the same extracted events, but not summaries or pinning. LADL v2 is worse than ordinary compaction with hints, with an interval entirely below zero. Extraction v2 makes Mistral worse rather than better, and action hints lower LADL v1 by 5.0 points. The table lists all 17 planned tests: the first 4 rows are the primary family, the next 7 the v2 family, and the last 6 the secondary family.

**Why: Mistral's extraction has low precision.** Recall is close to Qwen's, but Mistral adds many events that did not happen, mostly false commitments and false ambiguity events. Extraction v2 adds more of them.

| Confirm | Qwen v2 | Llama v2 | Mistral v1 | Mistral v2 |
|---|---:|---:|---:|---:|
| Event precision | 0.902 | 0.911 | 0.522 | 0.425 |
| Event recall | 0.864 | 0.934 | 0.813 | 0.824 |
| False commitment events | 18 | 30 | 402 | 643 |
| False ambiguity events | 12 | 6 | 379 | 599 |
| LADL probes with a false "unclear" flag | 0.9% | 0.5% | 12.3% | 19.4% |
| LADL accuracy | 81.0 | 84.2 | 68.7 | 64.0 |
| LADL accuracy with gold events | 86.1 | 85.8 | 86.7 | 86.7 |

A false ambiguity event marks the item as unclear, and the reducer keeps that flag until a later event changes the item's status. With v2, false flags alone account for wrong `clarify` answers on 14.1% of Mistral's LADL probes. With gold events, Mistral's LADL reaches 86.7%, the best of any Mistral condition, so the state representation itself still helps. No Mistral extraction output was truncated or unparseable.

**The same pattern on Test and Fresh (exploratory).** Mistral accuracy (%):

| Condition | Test | Fresh | Confirm |
|---|---:|---:|---:|
| Full history (no compaction) | 74.7 | 70.2 | 73.8 |
| Ordinary compaction | 66.7 | 64.6 | 66.3 |
| Constraint pinning | 66.1 | 64.8 | 69.4 |
| Chronological ledger (v2) | 52.0 | 53.6 | 56.9 |
| LLM-written transitions (v2) | 46.7 | 47.1 | 49.9 |
| LADL v1 | 60.8 | 59.5 | 68.7 |
| LADL v2 | 56.8 | 58.8 | 64.0 |
| LADL v2 without hints | 65.7 | 65.9 | 72.4 |
| LADL, gold events | 83.9 | 84.2 | 86.7 |

Event F1 for Mistral is 0.51 to 0.57 on Test and Fresh, compared with 0.83 to 0.93 for Qwen and Llama. LADL v2 trails ordinary compaction by 5.8 to 9.9 points on Test and Fresh, and the confidence intervals exclude zero. Across the three budgets and three compaction placements, LADL v2 trails ordinary compaction in all six settings and beats LLM-written transitions in all six.

**Action hints amplify bad state (exploratory).** For Mistral, removing hints raises LADL v2 by 8.9 points on Test, 7.1 on Fresh, and 8.4 on Confirm. Without hints, LADL v2 is level with ordinary compaction and pinning on Test and Fresh, and beats ordinary compaction by 6.1 [2.5, 9.7] on Confirm. The gap comes from probes whose item carries a false "unclear" flag (15% to 20% of probes). On those probes, the hinted ledger tells the policy to ask the user, and Mistral answers `clarify` 70% to 74% of the time, compared with 26% to 36% without hints. Accuracy on them rises from 13–17% to 44–57% without hints, while on all other probes the two versions differ by at most 4.3 points. This analysis was not planned, so it needs a separate test before it is claimed.

## Extraction v2

Prompt v2 clarifies that a clear partial approval is still explicit, and that a hedged statement should be an ambiguity event. It was developed on dev and frozen before Confirm.

| Confirm metric | Qwen v1 | Qwen v2 | Llama v1 | Llama v2 |
|---|---:|---:|---:|---:|
| Event extraction F1 | 0.859 | 0.882 | 0.865 | 0.922 |
| Approval F1 | 0.785 | 0.836 | 0.602 | 0.894 |
| Probes wrong because of extraction | 8.2% | 7.8% | 8.5% | 3.4% |
| Correct waits on 116 unmet guards | 87 | 89 | 55 | 84 |

The accuracy effect of v2 replicates for Llama on all three datasets: +8.6 points on Test, +3.3 on Fresh, and +5.0 on Confirm. For Qwen it is -1.2, +1.0, and -0.2, none significant. For Mistral it is -4.1 [-7.6, -0.3], -0.8 [-4.4, 2.9], and -4.7 [-8.5, -1.2], because v2 increases Mistral's false events.

## LADL versus the strongest baseline

This analysis is exploratory. The strongest baseline is chosen after seeing each dataset, and p-values are uncorrected.

| Dataset | Model | LADL v2 | Strongest baseline | Difference |
|---|---|---:|---|---|
| Test | Qwen | 74.2 | Chronological + hints, 73.3 | +0.9 [-3.6, 5.4] |
| Fresh | Qwen | 79.1 | Chronological + hints, 72.7 | +6.4 [2.3, 10.6] |
| Confirm | Qwen | 81.0 | Chronological, 73.6 | +7.4 [4.9, 9.9] |
| Test | Llama | 79.4 | Chronological, 80.0 | -0.6 [-4.4, 3.3] |
| Fresh | Llama | 80.7 | Chronological + hints, 79.3 | +1.4 [-1.1, 3.9] |
| Confirm | Llama | 84.2 | Chronological, 79.9 | +4.3 [1.2, 7.2] |
| Test | Mistral | 56.8 | Ordinary compaction, 66.7 | -9.9 [-15.4, -4.2] |
| Fresh | Mistral | 58.8 | Pinning, 64.8 | -6.0 [-10.2, -1.7] |
| Confirm | Mistral | 64.0 | Ordinary compaction + hints, 69.8 | -5.8 [-10.0, -1.6] |

On Confirm, LADL v2 is ahead of all seven compacted baselines for both Qwen and Llama after Holm correction over those 14 tests. This family was planned only for Mistral, so for Qwen and Llama it is exploratory.

## Action hints

Removing hints from LADL lowers Qwen by 6.6 points on Test, 8.6 on Fresh, and 3.3 on Confirm. The no-hint ledger compared with the chronological log is +0.6 on Test, -1.1 on Fresh, and +5.0 [2.3, 7.8] on Confirm. Hints help Qwen, but their contribution and the value of state without hints depend on the dataset. For Llama, hints do not significantly change LADL on any of the three datasets. For Mistral, hints lower LADL v2 by 7.1 to 8.9 points, as explained in the third-model section.

## Robustness

With extraction v2, Qwen LADL beats ordinary compaction, pinning, the chronological ledger, and LLM-written transitions at all three budgets and all three compaction placements. Llama LADL beats ordinary compaction, pinning, and LLM-written transitions in the same six settings. Against the chronological ledger, Llama is tied at all three Test budgets (+1.1, -0.6, -0.5), and ahead on Fresh with early (+4.2) and late (+3.8) compaction but not spread compaction (+1.9). Mistral LADL v2 trails ordinary compaction in all six settings and pinning in five, and beats LLM-written transitions in all six. It is ahead of the chronological ledger in two of six settings, Fresh with spread and late compaction.

## Where errors remain

- **Policy errors:** with gold events, 13.9% of Qwen decisions, 14.2% of Llama decisions, and 13.3% of Mistral decisions are wrong. Unneeded clarification accounts for 46 of Qwen's 127 errors, 71 of Llama's 130, and 27 of Mistral's 122.
- **Extraction errors:** on Confirm, extraction errors cause 18.9% (v1) and 23.5% (v2) of Mistral's LADL probes to be wrong, compared with 3.4% to 8.5% for Qwen and Llama.
- **Weak categories:** on Confirm with v2, Qwen reaches only 60.3% on ready commitments, and Llama reaches 65.6% on cancelled tasks.
- **Where the reducer helps:** after a cancellation followed by an approval, LADL was correct and the event-local log was wrong on 7 Qwen probes and 10 Llama probes.
- **Real examples:** `python -m src.eval.error_examples` writes seed-sampled success and failure cases from Confirm, including failures of LADL, to `results/confirm/error_examples.md`.

## RQ1: stale state

On Confirm under ordinary compaction, stale answers are 33.3% (Qwen) and 29.6% (Llama) of wrong state answers, above chance baselines of 12.9% and 16.3%. With full history they are 63.7% and 60.7%. Mistral shows the same pattern: 26.3% under ordinary compaction against a chance baseline of 12.8%, and 54.9% with full history. This repeats the earlier result: staleness is a real error type, but compaction is not its main cause.

## Implications for the final paper

1. State the main result as conditional: LADL helps when event extraction is precise. For Qwen and Llama it beats summaries, pinning, and LLM-written transitions. For Mistral, whose extraction has low precision, it beats only the two baselines that share its extracted events.
2. Report the gold-event condition for all three models (83% to 87%). It shows that the ledger state is useful once events are right, including for Mistral.
3. Use extraction v2 for Qwen and Llama, report v1 to show the effect of the fix, and report that v2 hurts Mistral. The planned v1 test against LLM-written transitions was null for Llama.
4. Do not claim that LADL always beats a chronological event log.
5. Replace the milestone statement that Qwen's advantage over the log disappears without hints. Report the Mistral no-hint result only as exploratory.
6. Name two remaining bottlenecks: the policy with correct state for Qwen and Llama, and extraction precision for Mistral.

## Limitations

- The Confirm text was written by Claude. It is separate from the original text, but it is not human-written language.
- The idea behind extraction v2 came from errors observed earlier. Its wording was tuned only on dev, and Confirm remained unseen until the prompt was frozen.
- The study uses three 7-8B models and one policy prompt per model. Prompts were developed with Qwen and Llama only. Mistral is the only held-out model, so one model decides how well the method transfers.
- Test, Fresh, and Confirm use synthetic workplace dialogues with deterministic gold rules shared with LADL.
- The replication and strongest-baseline analyses are exploratory.

## Reproduce

Run from the project directory on PACE-ICE. Repeat each job with `configs/llama8b.yaml`. Mistral runs every job except `dev`, as shown in the last three lines.

```bash
python -m src.generation.build --confirm --out data/confirm --n-per-family 4 --seed 20261123
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml dev
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml replicate
sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml v2-robust
sbatch scripts/pace_download.sbatch mistralai/Mistral-7B-Instruct-v0.3
sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml hardcap,extended,replicate,v2-robust
CACHE_SUFFIX=confirm sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml confirm
```

After copying the run directories back:

```bash
python -m src.eval.dev_extraction_report --runs results/runs
python -m src.eval.confirm_report --out results/confirm
python -m src.eval.replication_report --out results/confirm
python -m src.eval.post_milestone_analysis --out results/confirm
python -m src.eval.three_model_report --out results/confirm
python -m src.eval.error_examples --out results/confirm/error_examples.md
```

## AI assistance

Claude (Anthropic) designed and implemented these experiments with the team's direction, wrote the Confirm surface text, ran the PACE jobs, and drafted this note from the generated result files. This is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
