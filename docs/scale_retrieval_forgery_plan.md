# Scale, Retrieval, and Forged-Update Plan

Fixed on November 26, 2026, before any output of these experiments existed. The hashes in `results/confirm/freeze_scale.json` (kept locally, not in git) record this plan, the code, and the data when the pilot started.

## Purpose

The related work in [`followup_results.md`](followup_results.md) and the literature check of November 26 raise four questions that reviewers will ask and that the project has not answered:

1. **Do larger models still need LADL?** Woolford (arXiv:2610.20116) found that on a frontier model, the default summary kept commitments slightly better than his structured method. Guo and Guo (arXiv:2611.02361) found that explicit state outlasts long context for longer histories as the reader gets stronger.
2. **Does simple retrieval do as well?** Retrieval over raw turns is the most common baseline in the memory literature.
3. **Can a message that only claims a user decision change the agent's state?** Chen (arXiv:2606.22528) tests forged "policy rescinded" notices. Here, decision requests already come from teammates.
4. **How do errors depend on time since the last change, how cautious is each method, and how accurate is the ledger state?** These need only existing outputs.

Experiment D answers question 1, E answers 2, F answers 3, and G answers 4.

## Common settings

- Everything in [`followup_experiments_plan.md`](followup_experiments_plan.md) under common settings applies: deterministic serving, Confirm at budget 384 with the hard cap, paired timeline-cluster bootstrap with 2,000 resamples and seed 0, p-value floor 2/2001, Holm within each family.
- A test with a predicted direction is confirmed when its Holm-adjusted p is below 0.05 and the estimate has the predicted sign. A two-sided test is significant when its Holm-adjusted p is below 0.05.
- LADL means `lifecycle` with extraction v2, the frozen recommended configuration, unless stated otherwise.
- **Frozen:** prompts, reducer, rendering, budgets, and existing conditions are unchanged. The new conditions below are fixed here and not tuned on any output.

## New conditions

All three new retrieval conditions keep the same hard memory cap of 384 tokens and make no extra LLM calls.

- `recent`: at each compaction, instead of a summary, memory keeps the most recent earlier turns verbatim, as many as fit in the budget.
- `retrieval`: no summary. At each decision point, memory holds earlier turns retrieved by BM25 (k1 = 1.5, b = 0.75) with the decision request as the query, shown in their original order with turn numbers, up to the budget. Ties are broken toward later turns.
- `summary_retrieval`: an ordinary summary written with a budget of 0.4 × 384 tokens, plus retrieved turns up to 0.6 × 384 tokens, the same split as the ledger conditions.
- `lifecycle_source`: LADL in which events from turns that are not user turns can only be tool results; any other event from such a turn is dropped. Only the user can change their own instructions. It runs on the same extracted events as `lifecycle`.

The retrievable turns are those before the last compaction; turns after it are in the recent window as for every condition.

## Experiment D: larger models

Models, served in bf16 on one H200 at the revisions added to `configs/model_revisions.yaml`:

| Run name | Model | Revision |
|---|---|---|
| `qwen2.5-14b` | Qwen/Qwen2.5-14B-Instruct | cf98f3b3bbb457ad9e2bb7baf9a0125b6b88caa8 |
| `qwen2.5-32b` | Qwen/Qwen2.5-32B-Instruct | 5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd |
| `mistral-small-24b` | mistralai/Mistral-Small-24B-Instruct-2501 | 8f4e4ef338fcc155464a42e15580e27a3bc91dd9 |

These give a size trend within the Qwen family (7B, 14B, 32B) and within the Mistral family (7B, 24B). The weights are downloaded at the pinned revision to each job's node-local disk and deleted afterwards, because project storage cannot hold them. Only the tokenizer files are kept in the project, for replays.

Runs on Confirm: extraction v1 with all 14 existing conditions plus `recent`, `retrieval`, `summary_retrieval`, and `lifecycle_source`; extraction v2 with the 8 extraction conditions plus `lifecycle_source`; and the forged-update set of experiment F.

**Planned tests, family D, Holm over 21 tests, two-sided:** for each larger model, LADL minus `summary`, `summary_hint`, `pinning`, `pinning_hint`, `chrono` (v2), `chrono_hint` (v2), and `typed_llm` (v2). This is the v2 family that was planned for Mistral-7B.

Written predictions, reported without a test:
- Within each family, extraction precision is higher for the larger model.
- For both Qwen models, LADL is ahead of every compacted baseline.
- Mistral-Small-24B's v1 or v2 extraction precision lies above Mistral-7B's break-even of 0.52.
- Gold-event LADL stays above 85% for all three models.

## Experiment E: retrieval baselines

Runs: all six models on Confirm. The three 7B models also run on Test (budget 384) as an exploratory replication. For the 7B models, event conditions take the deterministic extraction files through `--events-from`, so their events equal those of the deterministic runs.

**Planned tests, family E, Holm over 18 tests, two-sided:** for each of the six models, LADL minus `retrieval`, `summary_retrieval`, and `recent`.

No direction is predicted. Retrieval can find the user's statements about the requested action directly, so it may match or beat LADL.

## Experiment F: forged updates

### Data

`data/forged/dialogues.jsonl` is derived from the Confirm dialogues with seed 20261127:

- In each dialogue, a target probe is drawn among probes whose item is an active prohibition (correct answer `decline`) or a commitment whose condition is not met (correct answer `wait`).
- A user filler turn between the item's last gold event and the probe, together with the assistant filler reply after it, is replaced by a forged message and the reply "Message received." Turn numbers, compaction points, probes, and gold labels do not change.
- The forged message is a tool turn of the form `[INCOMING MESSAGE] From <teammate>: ...` that claims the user lifted the prohibition, or that the final version was approved. There are three wordings per type.
- Gold labels stay as they were: the policy says teammates cannot override the user's instructions, and the message carries no user event.
- **Attacked probes** are the probes on the target item after the forged message and before any real change to that item. All other probes are also scored, to check for side effects.
- *Amended before any output existed:* the first draft did not exclude probes after a real change to the item. Such a probe can have a correct answer that matches the forged claim, so it does not measure the attack. With the exclusion, the set has 200 forged dialogues and 200 attacked probes (156 revocations, 44 approvals), and every attacked probe has the correct answer `decline` or `wait`.

### Runs

All six models, extraction v2, with `full`, `summary`, `summary_hint`, `pinning`, `pinning_hint`, `chrono`, `chrono_hint`, `typed_llm`, `lifecycle`, `lifecycle_nohint`, `lifecycle_source`, `recent`, `retrieval`, and `summary_retrieval`.

The clean counterparts are the same probes in the clean Confirm runs. Conditions that do not use events are identical under v1 and v2 extraction, so their clean results come from the v1 runs.

### Planned tests, family F, Holm over 18 tests, on attacked probes

For each of the six models:

- **F1:** `lifecycle_source` minus `lifecycle` on the forged set. Predicted positive.
- **F2:** `lifecycle` on the forged set minus `lifecycle` on the clean set, which is the attack effect. Two-sided.
- **F3:** `lifecycle_source` minus `summary` on the forged set. Two-sided.

Reported without a test: the attack effect for every condition, the share of attacked probes answered with the action the forged message would allow, and accuracy on the other probes against the clean set.

## Experiment G: analyses of existing outputs

Descriptive only, from the deterministic runs on Test, Fresh, and Confirm:

- Accuracy by compactions since the item's last change (0, 1, 2, 3 or more), per condition.
- Over-caution: the share of probes whose correct answer is `act` that get `wait` or `decline`, and the share of unneeded `clarify` answers.
- Ledger state accuracy: for ledger conditions, the share of probes where the ledger's status for the item equals the gold status, alongside the model's own answer to the state question.

## Exploratory, only if time allows by November 29

Each 7B model decides with the v2 extraction of each larger model through `--events-from` (9 cells, the four conditions of experiment C).

## Validation before the full runs

1. **Unit tests:** BM25 ranking and packing, the `recent` window, the speaker check, and the forged-data builder (labels, turn count, and compaction points unchanged; deterministic output).
2. **CPU replay:** the deterministic Confirm runs, replayed with the new code, still give zero cache misses and identical outputs.
3. **GPU pilot on the first 8 Confirm dialogues with Qwen2.5-7B:** the new conditions and the forged set, run twice with 384 and 64 concurrent requests from empty caches. The two runs must match exactly, and a replay must give zero misses.
4. **Larger models:** each job first runs the first 8 Confirm dialogues twice on its own server, with 384 and 64 concurrent requests and separate empty caches. The job stops unless the two runs match exactly. This checks batch invariance for each new model.

Every full run is replayed from its cache afterwards and must give zero misses and identical outputs.

## Reporting rule

- Every planned test and listed run is reported, whatever it shows.
- Anything added after results are seen is labeled exploratory.
- A failed, stopped, or repeated job is reported with its reason.

## Expected cost

About 7 H200 GPU-hours: about 4.5 for the three larger models including downloads, about 1.5 for the 7B runs, and about 0.5 for the pilot. Replays run on CPU nodes.
