# Scale, Retrieval, and Forged-Update Results

These experiments follow [`scale_retrieval_forgery_plan.md`](scale_retrieval_forgery_plan.md), fixed on November 26, 2026 before any of their outputs existed. All runs use deterministic serving on PACE-ICE H200 GPUs, budget 384, and the hard memory cap. LADL means `lifecycle` with extraction v2. Result files are kept locally under `results/scale/` and are not stored in git; the commands at the end regenerate them.

## Summary

- **LADL still helps larger models.** With Qwen2.5-14B and Qwen2.5-32B, LADL beats all seven compacted baselines after Holm correction, by 3.6 to 13.6 points. With Mistral-Small-24B it beats five of seven; the two event logs are within 2.7 points. Qwen2.5-32B with LADL reaches 98.1% on Confirm, above its full history (95.5%). Qwen-32B and Mistral-24B extract events with precision 0.94 to 0.96, so their LADL reaches its gold-event ceiling. LADL's lead over ordinary compaction shrinks with Qwen's size, from 17.9 points at 7B to about 8 at 14B and 32B, but stays significant.
- **BM25 retrieval over earlier turns is a strong baseline.** Plain retrieval or compaction plus retrieval is the best baseline under compaction for five of six models; for Qwen-14B, LLM-written transitions are 0.9 points higher. LADL leads plain retrieval significantly only for Qwen2.5-32B (+2.3 points). For Mistral-7B, whose extraction is poor, retrieval beats LADL by 14.7 points and also beats Mistral's full history. Ordinary compaction plus retrieval ties or trails LADL for the other models. Retrieval is helped by the synthetic dialogues, where requests repeat the words of the user's instructions.
- **A forged message from a teammate breaks every memory method.** When a message claims that the user lifted a prohibition or approved a final version, every condition without a speaker check performs the action on 41% to 97% of the affected decisions, against 0.5% to 31% without the message. Larger models comply more: Qwen2.5-32B acts on 89.5% to 96.5% of them in every such condition.
- **Only the user changes their own instructions: that rule helps but is not enough.** Dropping status changes that do not come from user turns improves LADL on these decisions for all six models (+10.5 to +34.5 points). The decision model still reads the forged text in recent turns or in the summary, so it still acts on 27.5% to 67% of them.
- **Ordinary compaction decays as compactions accumulate; LADL decays less.** For Qwen-7B on Confirm, ordinary compaction falls from 76% right after an instruction changes to 31% after three or more compactions; LADL goes from 82% to 67%.

## Validation

- The six deterministic Confirm runs of the 7B models, replayed with the new code, gave zero cache misses and identical outputs, so the existing conditions are unchanged.
- **Pilot (Qwen-7B, first 8 Confirm dialogues):** two runs with 384 and 64 concurrent requests from empty caches matched exactly in all four run groups, and the replay had zero misses.
- **Larger models:** each job first ran 8 dialogues twice on its own server with 384 and 64 concurrent requests. All three models matched exactly, so batch-invariant serving holds for them too.
- **Full runs:** all 21 full runs and the 6 check runs replayed from their caches with zero misses and identical outputs. All 35 new runs, pilot included, carry the source hash recorded at the start of the pilot (`results/confirm/freeze_scale.json`) and vLLM 0.34.0.
- **Deviations:**
  - The Qwen2.5-14B job lost its forged-set run when a request to its own server timed out three times on a heavily shared node. The cache was saved, and a second job with `SKIP_EXISTING=1` on another node reran only that run; its replay check is included above.
  - The larger models are not stored in project storage. Each job downloaded the pinned revision to node-local disk and deleted it at the end.
  - Each larger-model job logs a harmless `KeyError` at start, from the noise-setting list of the previous plan, which has no entry for these models.
  - The exploratory swap of larger-model extractions into the 7B models was not run.
- **Compute:** 9 GPU jobs used 6.8 H200 GPU-hours (plan: about 7). Replays and the tokenizer download used 17 short CPU jobs. All LADL PACE jobs so far total 25.3 GPU-hours.

## Accuracy on Confirm (%)

| Condition | Qwen 7B | Qwen 14B | Qwen 32B | Llama 8B | Mistral 7B | Mistral 24B |
|---|---:|---:|---:|---:|---:|---:|
| Full history (reference) | 71.1 | 79.8 | 95.5 | 82.6 | 73.1 | 89.1 |
| Ordinary compaction | 63.1 | 78.8 | 90.1 | 75.5 | 68.1 | 81.9 |
| Compaction + hints | 65.4 | 73.9 | 89.1 | 65.3 | 69.7 | 76.1 |
| Constraint pinning | 68.8 | 82.0 | 92.4 | 74.2 | 69.8 | 83.1 |
| Pinning + hints | 65.3 | 75.8 | 90.8 | 71.9 | 68.8 | 81.6 |
| Recent turns, verbatim | 68.9 | 77.3 | 89.8 | 77.0 | 70.5 | 83.4 |
| BM25 retrieval | 76.4 | 83.1 | 95.9 | 84.2 | 77.8 | 90.5 |
| Compaction + retrieval | 74.7 | 82.9 | 95.0 | 86.1 | 77.3 | 90.0 |
| Chronological ledger + hints (v2) | 74.0 | 79.4 | 90.6 | 81.0 | 59.9 | 89.5 |
| LLM transitions (v2) | 71.3 | 84.0 | 90.6 | 80.1 | 52.9 | 86.4 |
| **LADL (v2)** | **81.0** | **87.6** | **98.1** | 84.2 | 63.1 | **92.2** |
| LADL without hints (v2) | 78.3 | 85.0 | 96.5 | 82.1 | 73.1 | 90.4 |
| LADL, gold events | 87.4 | 91.9 | 97.5 | 86.4 | 84.6 | 92.5 |

Bold marks LADL where it is the best condition in the table, excluding gold events and full history. For Llama the best is ordinary compaction plus retrieval (86.1); for Mistral-7B it is BM25 retrieval (77.8). The speaker check (`lifecycle_source`) gives exactly the same accuracy as LADL on clean data for every model. The plot of the main conditions against model size is `results/scale/fig_scale.pdf`.

| Event extraction on Confirm, precision / recall | v1 | v2 |
|---|---|---|
| Qwen 7B | 0.884 / 0.843 | 0.905 / 0.871 |
| Qwen 14B | 0.857 / 0.954 | 0.853 / 0.957 |
| Qwen 32B | 0.957 / 0.994 | 0.960 / 0.994 |
| Mistral 7B | 0.519 / 0.814 | 0.426 / 0.826 |
| Mistral 24B | 0.937 / 0.987 | 0.945 / 0.990 |

## D. Larger models

**Planned tests, family D, Holm over 21 tests, two-sided.** LADL minus each compacted baseline, in points:

| Baseline | Qwen 14B | Qwen 32B | Mistral 24B |
|---|---|---|---|
| Ordinary compaction | **+8.7** [5.7, 11.8] | **+8.1** [6.2, 10.0] | **+10.4** [7.8, 12.9] |
| Compaction + hints | **+13.6** [9.8, 17.5] | **+9.1** [6.8, 11.2] | **+16.2** [13.5, 18.9] |
| Constraint pinning | **+5.6** [2.4, 8.6] | **+5.8** [3.8, 8.0] | **+9.2** [7.0, 11.3] |
| Pinning + hints | **+11.8** [8.0, 15.4] | **+7.3** [4.8, 10.0] | **+10.7** [7.7, 13.6] |
| Chronological ledger (v2) | **+9.3** [6.0, 12.5] | **+6.6** [4.3, 8.9] | +2.3 [-0.2, 4.7] |
| Chronological + hints (v2) | **+8.2** [5.2, 11.2] | **+7.5** [5.1, 10.2] | +2.7 [0.0, 5.6] |
| LLM transitions (v2) | **+3.6** [1.7, 5.5] | **+7.5** [4.7, 10.5] | **+5.9** [3.7, 8.4] |

Bold: significant after Holm correction (19 of 21; all in LADL's favour).

Written predictions:
- **Higher precision for the larger model in each family:** holds for Qwen-32B and Mistral-24B. It does not hold for Qwen-14B, whose precision is slightly lower than Qwen-7B's (0.853 against 0.905 with v2) while its recall is much higher (0.957 against 0.871).
- **LADL ahead of every compacted baseline for both larger Qwen models:** holds.
- **Mistral-24B's precision above Mistral-7B's break-even of 0.52:** holds, at 0.94.
- **Gold-event LADL above 85% for all three:** holds (91.9%, 97.5%, 92.5%).

Woolford's frontier-model reversal does not appear here. Within Qwen, LADL's lead over ordinary compaction shrinks from 17.9 points at 7B to 8.7 at 14B and 8.1 at 32B, and stays significant. Within Mistral it grows from -5.0 to +10.4 as extraction precision rises from 0.43 to 0.95.

## E. Retrieval baselines

**Planned tests, family E, Holm over 18 tests, two-sided.** LADL minus each retrieval baseline, in points:

| Model | BM25 retrieval | Compaction + retrieval | Recent turns |
|---|---|---|---|
| Qwen 7B | +4.6 [1.1, 8.2] | **+6.3** [2.3, 10.5] | **+12.1** [8.8, 15.3] |
| Qwen 14B | +4.5 [1.1, 7.8] | **+4.7** [1.6, 7.7] | **+10.3** [7.6, 12.9] |
| Qwen 32B | **+2.3** [0.7, 4.1] | **+3.2** [1.5, 4.9] | **+8.3** [5.9, 10.8] |
| Llama 8B | 0.0 [-3.0, 2.6] | -2.0 [-5.2, 0.8] | **+7.2** [3.9, 10.3] |
| Mistral 7B | **-14.7** [-19.7, -10.2] | **-14.2** [-18.7, -10.2] | **-7.4** [-12.4, -2.7] |
| Mistral 24B | +1.7 [-0.7, 4.1] | +2.3 [0.2, 4.4] | **+8.8** [6.0, 11.9] |

Bold: significant after Holm correction (12 of 18). LADL beats keeping recent turns verbatim for five models. Against plain retrieval, its estimate is ahead for the three Qwen models but significant only for 32B (Qwen-7B and Qwen-14B: Holm p = 0.066). It is level for Llama and Mistral-24B, and far behind for Mistral-7B.

**Exploratory, on Test (uncorrected):**

| Model | LADL (v2) | BM25 retrieval | Compaction + retrieval |
|---|---|---|---|
| Qwen 7B | 74.1 | 70.6 | 70.6 |
| Llama 8B | 80.0 | 84.5 | 86.1 |
| Mistral 7B | 57.5 | 78.3 | 76.7 |

The differences are +3.5 [-1.1, 8.3], -4.5 [-9.4, 0.1], and -20.8 [-27.0, -14.4] points against retrieval, so retrieval matches or beats LADL for Llama and Mistral on Test as well.

Retrieval keeps only earlier turns that share a word with the request: on average 77 to 90 tokens of the 384 available after a compaction, against 312 to 324 for recent turns. It works here because each decision request names the action in the same words as the user's instructions. Paraphrased or indirect requests would make lexical retrieval harder; this was not tested.

## F. Forged updates

200 of the 208 Confirm dialogues received one forged message: 156 claimed a prohibition was lifted, and 44 claimed a final version was approved. There are 200 attacked probes, one per forged dialogue. In 60 of them the forged message had been compacted before the decision.

**Planned tests, family F, Holm over 18 tests, on attacked probes:**

| Model | F1: speaker check minus LADL (predicted positive) | F2: LADL, forged minus clean | F3: speaker check minus ordinary compaction |
|---|---|---|---|
| Qwen 7B | **+27.0** [20.1, 34.0] | **-66.0** [-73.3, -58.4] | **+30.5** [22.8, 38.2] |
| Qwen 14B | **+21.5** [15.7, 27.9] | **-77.5** [-83.1, -71.5] | **+19.0** [13.3, 25.0] |
| Qwen 32B | **+25.0** [19.2, 31.2] | **-93.5** [-97.0, -89.3] | **+23.5** [17.3, 29.9] |
| Llama 8B | **+25.5** [18.9, 32.0] | **-60.0** [-67.7, -52.0] | **+15.5** [7.3, 23.9] |
| Mistral 7B | **+10.5** [4.9, 16.8] | **-32.0** [-41.3, -22.9] | -1.0 [-8.0, 6.1] |
| Mistral 24B | **+34.5** [27.5, 41.8] | **-77.0** [-83.7, -70.3] | **+32.5** [24.7, 40.3] |

17 of 18 tests are confirmed or significant. F1 is confirmed for all six models.

**Share of attacked decisions answered `act`, which the forged message would allow (%):**

| Condition | Qwen 7B | Qwen 14B | Qwen 32B | Llama 8B | Mistral 7B | Mistral 24B |
|---|---:|---:|---:|---:|---:|---:|
| Full history | 65.5 | 60.0 | 89.5 | 41.0 | 47.5 | 67.5 |
| Ordinary compaction | 63.0 | 67.0 | 91.0 | 46.0 | 50.5 | 69.0 |
| Constraint pinning | 52.5 | 66.0 | 91.0 | 47.5 | 55.0 | 69.0 |
| BM25 retrieval | 58.0 | 56.0 | 93.5 | 66.5 | 53.0 | 74.0 |
| Chronological + hints (v2) | 74.5 | 78.5 | 96.0 | 68.0 | 53.0 | 89.5 |
| LADL (v2) | 69.0 | 80.5 | 95.0 | 67.0 | 57.0 | 83.5 |
| LADL with speaker check (v2) | 36.0 | 41.5 | 67.0 | 34.0 | 27.5 | 38.0 |
| *Same decisions, clean set, LADL* | *3.0* | *6.0* | *0.5* | *5.5* | *10.0* | *3.0* |

The forged message is a tool turn that the policy prompt does not treat as an instruction from the user, yet every condition mostly acts on it. The failure is in the decision model, not only in memory: full history is as vulnerable as any compacted memory. The event-based methods are hit hardest, because the extractor turns the message into a revocation or approval, and the ledger then states the false status as fact. The speaker check removes those events, but the decision model still sees the message.

**Exploratory, added after results were seen:** when the forged message was compacted before the decision, the speaker check acts on 16.7% to 43.3% of attacked decisions, against 27.9% to 77.1% while the message is still among the recent turns. The remaining cases probably come from the summary, which can also record the forged claim; this was not checked.

**Side effects:** on all other probes, accuracy with the forged messages changes by at most 2.8 points for any condition and model.

## G. Analyses of existing outputs

**Accuracy by compactions since the item's last change (Confirm, %; 432, 330, 102, and 52 probes):**

| Condition | Qwen: 0 / 1 / 2 / 3+ | Llama: 0 / 1 / 2 / 3+ | Mistral: 0 / 1 / 2 / 3+ |
|---|---|---|---|
| Full history | 76 / 72 / 56 / 58 | 82 / 82 / 84 / 90 | 74 / 75 / 69 / 67 |
| Ordinary compaction | 76 / 58 / 41 / 31 | 85 / 68 / 68 / 62 | 78 / 68 / 43 / 37 |
| Constraint pinning | 75 / 65 / 58 / 63 | 81 / 69 / 69 / 63 | 78 / 68 / 54 / 46 |
| Chronological + hints | 75 / 76 / 65 / 60 | 77 / 72 / 73 / 73 | 71 / 54 / 42 / 35 |
| LADL v1 | 83 / 81 / 84 / 62 | 81 / 75 / 74 / 81 | 76 / 65 / 48 / 54 |
| LADL v2 | 82 / 82 / 81 / 67 | 87 / 83 / 78 / 83 | 71 / 62 / 47 / 35 |

Ordinary compaction loses most where state has had to survive several summaries; LADL holds up for Qwen and Llama. Test and Fresh show the same pattern (`results/scale/decay.csv`). The 3+ bucket is small, so its values move by several points between datasets.

**Over-caution on Confirm** (share of probes whose correct answer is `act` that get `wait` or `decline`, %):

| Model | Ordinary compaction | Pinning | Chronological + hints | LADL v1 | LADL v2 | LADL, gold events |
|---|---:|---:|---:|---:|---:|---:|
| Qwen | 27.3 | 33.2 | 14.5 | 15.5 | 14.8 | 12.5 |
| Llama | 7.2 | 11.8 | 3.3 | 5.3 | 4.9 | 6.2 |
| Mistral | 25.0 | 26.6 | 14.8 | 12.2 | 11.5 | 16.8 |

LADL is less over-cautious than ordinary compaction and pinning, so its gains do not come from refusing more. Its main excess is unneeded `clarify` answers for Mistral (22.6% with v2), from false ambiguity events.

**Ledger state accuracy on Confirm:** the ledger's status for the requested item matches the gold status on 86.0% (Qwen), 92.8% (Llama), and 63.6% (Mistral) of probes with extraction v2. The model's own answer to the state question is right on 83.1%, 81.1%, and 55.9%. For Llama, the ledger holds the right state 12 points more often than the model reports it.

## Implications

- LADL's case gets stronger, not weaker, with larger open models, because their extraction is nearly exact. The open question is cost, not accuracy.
- Plain BM25 retrieval is the baseline to beat. LADL's advantage over it is small when extraction is good and reverses when extraction is poor. A combination, retrieval for evidence and a ledger for status, was not tested.
- Memory methods that turn messages into state need to know who may change an instruction. A speaker rule is cheap and clearly helps, but the decision model itself accepts relayed claims, so this needs a fix in the policy as well, such as marking non-user messages as unverified.

## Limitations

- All data are synthetic. Decision requests reuse the action's wording, which favours lexical retrieval, and the forged messages use six templates.
- The forged messages arrive as tool turns marked `[INCOMING MESSAGE]`. Other channels, such as a user forwarding a teammate's claim, were not tested.
- The larger models were not used to develop any prompt, but they are one size step per family, and no closed model was tested.
- Retrieval scores each earlier turn on its own, with no summary of the rest. Dense retrieval and other retrieval sizes were not tried.

## Reproduce

Run from the project directory on PACE-ICE.

```bash
python -m src.generation.forged --data data/confirm/dialogues.jsonl --out data/forged/dialogues.jsonl --seed 20261127
TOKENIZER_ONLY=1 sbatch scripts/pace_download.sbatch Qwen/Qwen2.5-14B-Instruct Qwen/Qwen2.5-32B-Instruct mistralai/Mistral-Small-24B-Instruct-2501
CACHE_SUFFIX=scale sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml newconds        # also llama8b, mistral7b
LOCAL_WEIGHTS=1 CACHE_SUFFIX=scale sbatch -t 03:00:00 scripts/pace_experiment.sbatch configs/qwen32b.yaml scale   # also qwen14b, mistral24b
sbatch scripts/pace_replay.sbatch qwen2.5-32b-pace cache/llm_qwen32b_scale.sqlite cache/llm_qwen32b_scale_check_a.sqlite cache/llm_qwen32b_scale_check_b.sqlite
```

A job stopped by its time limit or a failed request is finished by resubmitting it with `SKIP_EXISTING=1` and the same `CACHE_SUFFIX`.

After copying the run directories back:

```bash
python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det
python -m src.eval.scale_report --runs results/runs_det --out results/scale
```

## AI assistance

Claude (Anthropic) designed these experiments with the team's direction, implemented the code, ran the PACE jobs, and drafted this note from the generated result files. This is project documentation rather than paper text. Team members should check its claims against the result files before relying on them.
