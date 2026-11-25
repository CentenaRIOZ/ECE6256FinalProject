# Post-Milestone Experiment Results

These experiments test the open questions from the milestone. The confirmation rule in [`post_milestone_confirmation_plan.md`](post_milestone_confirmation_plan.md) was fixed before the Confirm set was run. The third-model rule in [`third_model_plan.md`](third_model_plan.md) was fixed before any Mistral run.

All numbers below come from the deterministic reruns of November 24-25, 2026 (run tag `-det1`), which reproduce exactly from the same code and settings. The reporting rule in [`deterministic_rerun_plan.md`](deterministic_rerun_plan.md) makes them the reported results. [`reproducibility.md`](reproducibility.md) compares them with the earlier nondeterministic runs. The result files, raw run records, and freeze hashes are kept locally under `results/` and are not stored in git. The commands at the end regenerate them.

## Summary

- **LADL mostly holds up on new wording for Qwen and Llama.** On 52 new timelines with separate actions and text, LADL beats 6 of 8 hint-parity baselines after Holm correction. Both exceptions are Llama: against the chronological ledger with hints (+3.6, p = 0.106) and against LLM-written transitions (0.0). With extraction v2, LADL is ahead of all seven compacted baselines for both models (exploratory).
- **It does not hold for a third model with weak extraction.** On Mistral-7B, which played no part in development, LADL beats the event log and LLM-written transitions but not ordinary compaction or pinning. Mistral's extractor adds many events that did not happen. With gold events, Mistral's LADL reaches 84.6%, its best condition.
- **Extraction v2 fixes the main Llama failure but hurts Mistral.** For Llama, approval F1 rises from 0.61 to 0.89, and LADL accuracy rises by 6.1 points on Confirm. Qwen does not change meaningfully. For Mistral, v2 adds more false events and lowers LADL by 4.7 points.
- **LADL is not uniformly better than an event log.** With v2, Qwen leads the strongest baseline by 7.0 points on Confirm and 5.0 on Fresh, but only 2.4 on Test, which is not significant. Llama leads by 0.3 to 3.2 points, significantly only on Confirm.
- **The milestone's action-hint conclusion needs revising.** Hints add about 4 to 5 points to Qwen's LADL on every dataset. Without hints, Qwen's ledger is level with the chronological log on Test and Fresh, and ahead by 3.6 [0.1, 7.4] points on Confirm. For Llama with extraction v1, hints lower LADL by 5.6 points on Fresh.
- **The largest remaining error source depends on the model.** For Qwen and Llama it is the policy: even with gold events, 12.6% and 13.6% of Confirm decisions are wrong. For Mistral it is extraction.
- **Borderline conclusions are fragile.** Across three runs of Confirm, 32 of 37 planned conclusions agree. The five that change, mostly for Llama, are near the significance threshold and should be reported with that caveat.

## What was run

All runs use PACE-ICE H200 GPUs, temperature 0, batch-invariant vLLM serving, and the hard memory cap. Qwen2.5-7B-Instruct and Llama-3.1-8B-Instruct were used throughout. Mistral-7B-Instruct-v0.3 was added afterwards as a held-out model.

| Experiment | Data | Purpose |
|---|---|---|
| Extraction v1 versus v2 | Dev split, 208 probes | Develop and freeze the approval-extraction prompt (Qwen and Llama only) |
| Confirmation | New Confirm set, 916 probes | Run the planned tests on separate actions and text |
| Replication | Test (664) and Fresh (912) | Check v2 and hint-parity baselines on earlier data |
| v2 robustness | Test budgets 256, 384, 768; Fresh early, spread, late | Check sensitivity to budget and compaction location |
| Third model | All of the above except dev | Check whether the results depend on the development models |

Across the project, 39 PACE GPU jobs have used about 13.8 H200 GPU-hours, including startup, smoke tests, and 9.4 hours of reproducibility checks and deterministic reruns.

## Planned confirmation results

Four-way accuracy differences in percentage points on the Confirm set, with 95% confidence intervals. `Yes` means positive after Holm correction.

**Primary family: LADL v1 minus hint-parity baselines**

| Baseline | Qwen | Confirmed | Llama | Confirmed |
|---|---|---|---|---|
| Ordinary compaction + hints | +15.9 [12.3, 19.9] | Yes | +12.8 [9.1, 16.3] | Yes |
| Pinning + hints | +16.0 [12.7, 19.4] | Yes | +6.1 [2.8, 9.3] | Yes |
| Chronological ledger + hints | +7.8 [4.4, 11.2] | Yes | +3.6 [0.0, 7.2] | No |
| LLM-written transitions | +10.0 [5.9, 14.3] | Yes | 0.0 [-2.2, 2.1] | No |

Adding hints did not always strengthen a baseline. For Llama, ordinary compaction fell from 75.5% to 65.3%, pinning from 74.2% to 71.9%, and the chronological ledger from 80.3% to 74.5%. These tests therefore should not be read alone, so the unhinted comparisons below matter.

**Secondary family**

| Comparison | Qwen | Confirmed | Llama | Confirmed |
|---|---|---|---|---|
| LADL v1 - ordinary compaction | +18.2 [14.7, 21.9] | Yes | +2.5 [-1.2, 6.0] | No |
| LADL v1 - pinning | +12.6 [8.8, 16.3] | Yes | +3.8 [0.2, 7.4] | No |
| LADL v1 - chronological ledger | +7.8 [4.5, 11.0] | Yes | -2.3 [-6.6, 1.5] | No |
| LADL v1 - LADL without hints | +4.1 [1.2, 7.2] | No | -2.9 [-6.4, 0.4] | No |
| LADL v2 - LADL v1 | -0.3 [-2.2, 1.4] | No | +6.1 [3.7, 8.8] | Yes |
| Strict hedging - LADL v1 | 0.0 [0.0, 0.0] | No | +4.8 [2.6, 7.3] | Yes |

In the earlier nondeterministic run, Llama's comparison with the chronological ledger plus hints, Llama's comparison with pinning, and Qwen's hint effect were also confirmed. They sit near the threshold and change between runs.

## Third model: Mistral-7B-Instruct-v0.3

Mistral played no part in developing LADL, the baselines, or extraction v2. Its tests were fixed in [`third_model_plan.md`](third_model_plan.md) before any Mistral output existed. They use separate Holm families, so the two-model results above are unchanged.

**Planned tests on Confirm**

| Comparison | Difference | Confirmed |
|---|---|---|
| LADL v1 - ordinary compaction + hints | -1.9 [-5.4, 1.7] | No |
| LADL v1 - pinning + hints | -1.0 [-4.7, 2.5] | No |
| LADL v1 - chronological ledger + hints | +8.3 [5.3, 11.6] | Yes |
| LADL v1 - LLM-written transitions | +11.9 [8.8, 15.1] | Yes |
| LADL v2 - ordinary compaction | -5.0 [-9.9, -0.4] | No |
| LADL v2 - ordinary compaction + hints | -6.6 [-10.5, -2.6] | No |
| LADL v2 - pinning | -6.7 [-11.3, -2.2] | No |
| LADL v2 - pinning + hints | -5.7 [-9.9, -1.8] | No |
| LADL v2 - chronological ledger | +4.4 [0.5, 7.8] | No |
| LADL v2 - chronological ledger + hints | +3.2 [-0.2, 6.4] | No |
| LADL v2 - LLM-written transitions | +10.2 [6.7, 13.7] | Yes |
| LADL v2 - LADL v1 | -4.7 [-7.3, -2.1] | No |
| LADL v1 - ordinary compaction | -0.3 [-4.8, 4.2] | No |
| LADL v1 - pinning | -2.0 [-6.0, 2.3] | No |
| LADL v1 - chronological ledger | +8.3 [4.7, 11.9] | Yes |
| LADL v1 - LADL v1 without hints | -3.6 [-6.8, -0.3] | No |
| Strict hedging - LADL v1 | 0.0 [0.0, 0.0] | No |

The table lists all 17 planned tests: the first 4 rows are the primary family, the next 7 the v2 family, and the last 6 the secondary family. LADL v1 beats the baselines that share its extracted events, but not summaries or pinning. LADL v2 is worse than all four summary and pinning baselines, with intervals entirely below zero, and its lead over the event log (+4.4) misses the corrected threshold. Extraction v2 makes Mistral worse, and action hints lower LADL v1 by 3.6 points.

**Why: Mistral's extraction has low precision.** Recall is close to Qwen's, but Mistral adds many events that did not happen, mostly false commitments and false ambiguity events. Extraction v2 adds more of them.

| Confirm | Qwen v2 | Llama v2 | Mistral v1 | Mistral v2 |
|---|---:|---:|---:|---:|
| Event precision | 0.905 | 0.912 | 0.519 | 0.426 |
| Event recall | 0.871 | 0.935 | 0.814 | 0.826 |
| False commitment events | 18 | 31 | 403 | 649 |
| False ambiguity events | 12 | 5 | 388 | 603 |
| LADL probes with a false "unclear" flag | 0.9% | 0.7% | 13.0% | 19.5% |
| LADL accuracy | 81.0 | 84.2 | 67.8 | 63.1 |
| LADL accuracy with gold events | 87.4 | 86.4 | 84.6 | 84.6 |

A false ambiguity event marks the item as unclear, and the reducer keeps that flag until a later event changes the item's status. With v2, false flags alone account for wrong `clarify` answers on 13.9% of Mistral's LADL probes. With gold events, Mistral's LADL reaches 84.6%, the best of any Mistral condition, so the state representation itself still helps. No Mistral extraction output was truncated or unparseable.

**The same pattern on Test and Fresh (exploratory).** Mistral accuracy (%):

| Condition | Test | Fresh | Confirm |
|---|---:|---:|---:|
| Full history (no compaction) | 72.7 | 71.3 | 73.1 |
| Ordinary compaction | 66.9 | 62.8 | 68.1 |
| Constraint pinning | 66.6 | 65.4 | 69.8 |
| Chronological ledger (v2) | 53.5 | 53.3 | 58.7 |
| LLM-written transitions (v2) | 48.2 | 47.5 | 52.9 |
| LADL v1 | 61.7 | 60.4 | 67.8 |
| LADL v2 | 57.5 | 58.7 | 63.1 |
| LADL v2 without hints | 66.0 | 66.0 | 73.1 |
| LADL, gold events | 84.0 | 83.4 | 84.6 |

Event F1 for Mistral is 0.51 to 0.57 on Test and Fresh, compared with 0.82 to 0.94 for Qwen and Llama. LADL v2 trails ordinary compaction by 9.3 points on Test and 4.2 on Fresh; the Fresh interval just includes zero. Across the three budgets and three compaction placements, LADL v2 trails ordinary compaction and pinning in all six settings, with intervals below zero in five and six of them, and beats LLM-written transitions in all six.

**Action hints amplify bad state (exploratory).** For Mistral, removing hints raises LADL v2 by 8.4 points on Test, 7.3 on Fresh, and 10.0 on Confirm. Without hints, LADL v2 is level with ordinary compaction and pinning on Test and Fresh, and beats them by 5.0 [1.6, 8.4] and 3.4 [0.1, 6.8] points on Confirm. The gap comes from probes whose item carries a false "unclear" flag (15% to 20% of probes). On those probes, the hinted ledger tells the policy to ask the user, and Mistral answers `clarify` 70% to 71% of the time, compared with 24% to 38% without hints. Accuracy on them rises from 14–19% to 42–59% without hints, while on all other probes the two versions differ by at most 3.5 points. This analysis was not planned, so it needs a separate test before it is claimed.

## Extraction v2

Prompt v2 clarifies that a clear partial approval is still explicit, and that a hedged statement should be an ambiguity event. It was developed on dev and frozen before Confirm.

| Confirm metric | Qwen v1 | Qwen v2 | Llama v1 | Llama v2 |
|---|---:|---:|---:|---:|
| Event extraction F1 | 0.863 | 0.888 | 0.864 | 0.924 |
| Approval F1 | 0.793 | 0.846 | 0.605 | 0.894 |
| Probes wrong because of extraction | 8.0% | 6.8% | 8.8% | 3.6% |
| Correct waits on 116 unmet guards | 88 | 89 | 54 | 85 |

The accuracy effect of v2 replicates for Llama on all three datasets: +7.5 points on Test, +4.8 on Fresh, and +6.1 on Confirm. For Qwen it is 0.0, +1.8, and -0.3, none significant. For Mistral it is -4.2 [-7.9, -0.3], -1.8 [-5.5, 2.2], and -4.7 [-7.3, -2.1], because v2 increases Mistral's false events.

## LADL versus the strongest baseline

This analysis is exploratory. The strongest baseline is chosen after seeing each dataset, and p-values are uncorrected.

| Dataset | Model | LADL v2 | Strongest baseline | Difference |
|---|---|---:|---|---|
| Test | Qwen | 74.1 | Chronological + hints, 71.7 | +2.4 [-1.4, 6.0] |
| Fresh | Qwen | 78.4 | Chronological + hints, 73.4 | +5.0 [1.4, 8.6] |
| Confirm | Qwen | 81.0 | Chronological + hints, 74.0 | +7.0 [3.3, 10.6] |
| Test | Llama | 80.0 | Chronological, 79.7 | +0.3 [-4.0, 4.8] |
| Fresh | Llama | 81.9 | Chronological, 81.2 | +0.7 [-2.0, 3.5] |
| Confirm | Llama | 84.2 | Chronological + hints, 81.0 | +3.2 [0.2, 5.9] |
| Test | Mistral | 57.5 | Ordinary compaction, 66.9 | -9.3 [-14.7, -4.1] |
| Fresh | Mistral | 58.7 | Ordinary compaction + hints, 66.3 | -7.7 [-11.8, -3.3] |
| Confirm | Mistral | 63.1 | Pinning, 69.8 | -6.7 [-11.3, -2.2] |

On Confirm, LADL v2 is ahead of all seven compacted baselines for both Qwen and Llama after Holm correction over those 14 tests. This family was planned only for Mistral, so for Qwen and Llama it is exploratory.

## Action hints

Removing hints from LADL (v1) lowers Qwen by 4.8 points on Test, 4.1 on Fresh, and 4.1 on Confirm, with every interval above zero. The no-hint ledger compared with the chronological log is -0.8 on Test, +1.3 on Fresh, and +3.6 [0.1, 7.4] on Confirm. Hints help Qwen, and the value of state without hints depends on the dataset.

For Llama, hints change LADL v1 by -3.5 on Test, -5.6 [-9.0, -2.3] on Fresh, and -2.9 on Confirm. With extraction v2 the effect is +1.1, -0.3, and +2.1, none significant, so the harm appears with the noisier v1 extraction. For Mistral, hints lower LADL v2 by 7.3 to 10.0 points, as explained in the third-model section.

## Robustness

With extraction v2, Qwen LADL beats ordinary compaction, pinning, the chronological ledger, and LLM-written transitions at all three budgets and all three compaction placements. Llama LADL beats ordinary compaction, pinning, and LLM-written transitions in the same six settings. Against the chronological ledger, Llama is tied at all three Test budgets (+1.5, +0.3, +1.1), and ahead on Fresh with early (+3.4) and late (+3.8) compaction but not spread compaction (+0.7). Mistral LADL v2 trails ordinary compaction in all six settings and pinning in all six, and beats LLM-written transitions in all six. It is ahead of the chronological ledger in three of six settings: budget 768, and Fresh with spread and late compaction.

## Where errors remain

- **Policy errors:** with gold events, 12.6% of Qwen decisions, 13.6% of Llama decisions, and 15.4% of Mistral decisions are wrong. Unneeded clarification accounts for 49 of Qwen's 115 errors, 63 of Llama's 125, and 38 of Mistral's 141.
- **Extraction errors:** on Confirm, extraction errors cause 19.8% (v1) and 23.0% (v2) of Mistral's LADL probes to be wrong, compared with 3.6% to 8.8% for Qwen and Llama.
- **Weak categories:** on Confirm with v2, Qwen reaches only 61.8% on ready commitments, and Llama 70.0% on completed tasks and 71.9% on cancelled tasks.
- **Where the reducer helps:** after a cancellation followed by an approval, LADL was correct and the event-local log was wrong on 10 Qwen probes and 10 Llama probes.
- **Real examples:** `python -m src.eval.error_examples` writes seed-sampled success and failure cases from Confirm, including failures of LADL, to `results/confirm/error_examples.md`.

## RQ1: stale state

On Confirm under ordinary compaction, stale answers are 33.0% (Qwen) and 30.7% (Llama) of wrong state answers, above chance baselines of 12.6% and 16.5%. With full history they are 63.7% and 61.8%. Mistral shows the same pattern: 27.7% under ordinary compaction against a chance baseline of 12.8%, and 54.5% with full history. This repeats the earlier result: staleness is a real error type, but compaction is not its main cause.

## Implications for the final paper

1. State the main result as conditional: LADL helps when event extraction is precise. For Qwen, and with extraction v2 for Llama, it beats summaries, pinning, and LLM-written transitions. For Mistral, whose extraction has low precision, it beats only the baselines that share its extracted events.
2. Report the gold-event condition for all three models (82% to 87%). It shows that the ledger state is useful once events are right, including for Mistral.
3. Use extraction v2 for Qwen and Llama, report v1 to show the effect of the fix, and report that v2 hurts Mistral. The planned v1 tests for Llama against LLM-written transitions and against the event log with hints were not confirmed.
4. Do not claim that LADL always beats a chronological event log.
5. Replace the milestone statement that Qwen's advantage over the log disappears without hints. Report the Mistral no-hint result only as exploratory.
6. Name two remaining bottlenecks: the policy with correct state for Qwen and Llama, and extraction precision for Mistral.
7. Flag the conclusions that changed between runs ([`reproducibility.md`](reproducibility.md)) and avoid resting a claim on any of them.

## Limitations

- The Confirm text was written by Claude. It is separate from the original text, but it is not human-written language.
- The idea behind extraction v2 came from errors observed earlier. Its wording was tuned only on dev, and Confirm remained unseen until the prompt was frozen.
- The study uses three 7-8B models and one policy prompt per model. Prompts were developed with Qwen and Llama only. Mistral is the only held-out model, so one model decides how well the method transfers.
- Test, Fresh, and Confirm use synthetic workplace dialogues with deterministic gold rules shared with LADL.
- The replication and strongest-baseline analyses are exploratory.
- The deterministic runs replaced runs whose results had already been seen. The reporting rule was fixed before the deterministic pilot, and every conclusion that changed is listed in `reproducibility.md`.

## Reproduce

Run from the project directory on PACE-ICE. Repeat each job with `configs/llama8b.yaml`. Mistral runs every job except `dev` and the no-cap Test run. Jobs serve deterministically by default.

```bash
python -m src.generation.build --confirm --out data/confirm --n-per-family 4 --seed 20261123
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml full,extended,dev,replicate,v2-robust
sbatch scripts/pace_download.sbatch mistralai/Mistral-7B-Instruct-v0.3
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml confirm
RUN_TAG=-det1 sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml hardcap,extended,replicate,v2-robust
```

After copying the run directories back:

```bash
python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det
python -m src.eval.dev_extraction_report --runs results/runs_det
python -m src.eval.confirm_report --runs results/runs_det --out results/det/confirm
python -m src.eval.replication_report --runs results/runs_det --out results/det/confirm
python -m src.eval.post_milestone_analysis --runs results/runs_det --out results/det/confirm
python -m src.eval.three_model_report --runs results/runs_det --out results/det/confirm
python -m src.eval.error_examples --runs results/runs_det --out results/det/confirm/error_examples.md
```

## AI assistance

Claude (Anthropic) designed and implemented these experiments with the team's direction, wrote the Confirm surface text, ran the PACE jobs, and drafted this note from the generated result files. This is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
