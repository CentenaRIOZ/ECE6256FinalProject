# Reproducibility Checks

Checked on November 24, 2026, at commit `d791b52` plus the fixes listed below. Raw run records and result files stay on the team's machines and are not stored in git.

## Summary

- **Data, code, and analysis are reproducible.** Generated data regenerates byte for byte, the current code reproduces the original prompts, and every report regenerates the same tables from the raw runs.
- **The model runs reported so far are not exactly reproducible.** vLLM gave slightly different answers to identical requests depending on batching. A rerun from scratch changes 6% to 15% of individual decisions, though condition accuracy moves by at most 2.6 points.
- **Most conclusions survive a rerun, but borderline ones do not.** On Confirm, 48 of 51 planned four-way tests keep their conclusion. The three that change were close to the significance threshold.
- **Exact reproducibility now works for all three models.** In a pilot on the full Confirm set, batch-invariant serving with shared in-flight requests gave identical outputs across independent runs on different nodes and at different load. A replay from the cache also matched exactly. This is the default for new runs, and the existing experiments are being rerun this way ([`deterministic_rerun_plan.md`](deterministic_rerun_plan.md)).

## What was checked

### 1. Data

Running the documented generator commands in a fresh clone reproduces the committed files exactly: the Confirm set, the three Fresh placements and their timelines, the 48 original timelines, and the 192 template dialogues. The paraphrased dialogues in `data/dialogues/dialogues.jsonl` were sampled from an LLM at temperature 0.8, so the committed file is the canonical version.

### 2. Code versus results

`src/eval/replay_check.py` reruns each finished run with `--cache-only`. Every LLM call is answered from that run's cache, and a cache miss means the current code sent a prompt the original run never sent.

| Measure | Result |
|---|---|
| Original PACE runs replayed | 54, with all 1,263,998 LLM calls |
| Cache misses | 12,090 (0.96%) |
| Runs replayed with no difference at all | 4 hint-baseline runs, which repeat no prompt |
| Dialogues whose extraction changed | 7, in 4 runs |
| Decisions changed per run | 0% to 7.1%, mean 2.3% |

The misses come from identical requests sent at the same moment. The four variants of a timeline share their text, and several conditions share summary prompts. vLLM sometimes answered two identical concurrent requests differently, and the cache kept only one answer. In one run we checked, 21 of the 22 summaries that changed in the replay were exactly another condition's original summary. Because runs without repeated prompts replay exactly and the remaining misses follow from this mechanism, the current code sends the same prompts as the code that produced the results.

### 3. Analysis

Every report script was rerun from the raw runs in a fresh clone, both with this machine's packages and with the PACE environment. All tables, Markdown reports, and paper tables were byte-identical, except that three RQ1 columns differed in the 16th decimal place. One documented command was wrong: the original analysis must include the two strict-hedging runs. This is now fixed in the README and `scripts/run_all.sh`.

### 4. Rerun without the cache

Confirm v1 and v2 were rerun for all three models with the same code, model revisions, and environment, but with an empty cache.

| Model | Decision agreement, v1 | Decision agreement, v2 | Dialogues with changed extraction, v1 / v2 |
|---|---:|---:|---|
| Qwen | 87.3% | 87.8% | 15 / 17 of 208 |
| Llama | 92.9% | 94.2% | 19 / 17 of 208 |
| Mistral | 88.6% | 85.0% | 29 / 62 of 208 |

Condition accuracy changed by about 0 points on average and by at most 2.6 points. Event F1 changed by at most 0.003, and approval F1 by at most 0.011.

Of the 51 planned four-way tests on Confirm, 48 kept their conclusion. These changed:

| Test | Original | Rerun |
|---|---|---|
| Llama: LADL v1 - chronological ledger + hints (primary) | +5.0, confirmed (p = 0.018) | +3.5, not confirmed (p = 0.088) |
| Llama: LADL v1 - pinning (secondary) | +5.2, confirmed (p = 0.049) | +2.9, not confirmed (p = 0.73) |
| Mistral: LADL v2 - chronological ledger + hints (v2 family) | +3.4, not confirmed (p = 0.19) | +4.9, confirmed (p = 0.015) |

So the primary two-model result is 7 of 8 tests in the original run and 6 of 8 in the rerun. For the execute-versus-not sensitivity metric, 44 of 51 conclusions were unchanged.

### 5. Deterministic serving

Two Qwen jobs ran the first 52 Confirm dialogues with extraction v1 and v2, `VLLM_BATCH_INVARIANT=1`, shared in-flight requests, and separate empty caches, on two different nodes. All 5,016 probe records were identical in every field except latency, and the extractions were byte-identical. Each job took 3 minutes, the same rate as the original runs.

These outputs agree with the original run on only 85% to 88% of decisions, so deterministic runs cannot reproduce numbers from the earlier nondeterministic runs.

### 6. Deterministic pilot on the full Confirm set

The pilot followed [`deterministic_rerun_plan.md`](deterministic_rerun_plan.md), which was fixed before it ran. For each model, run 1 used 384 concurrent requests and run 2 used 64, each from an empty cache. The six jobs ran on five different H200 nodes, and all twelve run records carry the source hash recorded before the pilot.

| Check | Qwen | Llama | Mistral |
|---|---|---|---|
| Probe records identical between run 1 and run 2 (v1 + v2) | 20,152 of 20,152 | 20,152 of 20,152 | 20,152 of 20,152 |
| Extractions identical between runs | Yes | Yes | Yes |
| Cache misses when replaying run 1 | 0 of 68,342 | 0 of 68,453 | 0 of 70,494 |
| Replay identical to run 1 | Yes | Yes | Yes |
| Job time, run 1 / run 2 | 18 / 41 min | 14 / 18 min | 18 / 28 min |

The pilot passed every criterion, so stage 2 reruns the other existing experiments in the same mode.

### 7. Stage 2: the other existing experiments

Every existing PACE experiment was rerun once with its original settings, using the tag `-det1`. Pilot run 1 serves as the deterministic Confirm run. Qwen and Llama finished in 45 and 55 minutes. Three problems came up with Mistral and were fixed without changing any run code:

- **One node was slow.** Every job on `atl1-1-03-015-16-0` ran slowly. The first Mistral stage 2 job landed there and hit its 2.5-hour limit after finishing Test at three budgets and Fresh at three placements. Deterministic mode itself is not the cause: the same Mistral Test run took 336 seconds on another node, against 320 seconds for the original nondeterministic run.
- **A time limit lost the cache.** Bash runs a signal handler only after its foreground child exits, so the job was killed before it saved its LLM cache. Runs now go to the background and the shell waits on them, so the handler runs at once. A local test confirmed this. The six finished runs are complete. Independent reruns reproduced them exactly, and their caches can now replay them.
- **Another job held the port.** On one node, port 8002 belonged to a server serving a different model, so two jobs failed with "model does not exist". Jobs now serve on a free port and start only if the server lists their own model. No earlier job shared a server: jobs for the same model never ran on the same node at the same time.

**Code identity.** After the pilot, three new tools (`determinism_check.py`, `check_surface.py`, `cues.py`) and an import change in `paraphrase.py` were synced to PACE before stage 2 started, so stage 2 records source hash `3bf209e8` rather than the pilot's `440c321b`. Removing those four changes from the stage 2 tree reproduces `440c321b` exactly, and none of the changed files is imported by `src/eval/run.py`. All stage 2 runs share hash `3bf209e8`.

**Verification.** Every stage 2 run was checked one of two ways:

- **Cache replay:** 49 of the 54 run-budget combinations replayed from their own caches with zero misses and identical records and extractions. These cover all 19 Qwen and 19 Llama combinations and 11 of Mistral's 16.
- **Independent rerun:** the 5 Mistral runs that lost their cache were rerun on other nodes and compared field by field. All 5 were identical: 44,704 probe records and every extraction. The rerun caches can now replay them as well.

Analysis tools changed after stage 2, so later verification runs record other whole-source hashes. The modules `src/eval/run.py` imports (`run`, `extractor`, `content`, `reducer`, `client`, `managers`, `policy`) did not change. New runs also record `run_sha256`, a hash of only the modules they imported, so unrelated tool changes no longer alter it.

### 8. Three runs of Confirm

`python -m src.eval.run_variability` applies the planned tests to the original run, the cache-free rerun, and the deterministic run.

- 32 of the 37 planned four-way tests reach the same conclusion in all three runs.
- The five that change are all near the threshold: Llama LADL v1 minus the chronological ledger with hints (primary) and minus pinning, Qwen LADL v1 minus LADL without hints, and Mistral LADL v2 minus the chronological ledger with and without hints.
- A planned difference changes by at most 3.9 points between runs, and condition accuracy by at most 3.1 points.
- In the deterministic run, 6 of the 8 two-model primary tests are confirmed. The original run had 7 of 8.

### 9. What changes when the deterministic runs are reported

All reports were regenerated from the deterministic runs (`python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det`, then each report with `--runs results/runs_det`). Condition accuracy changed by 1.0 point on average and by at most 4.4 points, across 117 condition-dataset-model cells.

| Claim | Original runs | Deterministic runs |
|---|---|---|
| Confirm, two-model primary tests confirmed | 7 of 8 | 6 of 8 (Llama LADL v1 - chronological + hints: +3.6, p = 0.106) |
| Confirm, two-model secondary tests confirmed | 7 of 12 | 5 of 12 (Qwen hint effect +4.1, p = 0.077; Llama LADL v1 - pinning +3.8, p = 0.216) |
| Confirm, Mistral v2 family confirmed | 2 of 7 | 1 of 7 (LADL v2 - chronological: +4.4, p = 0.060) |
| Confirm, LADL v2 above all 7 baselines for Qwen and Llama (exploratory) | 14 of 14 | 14 of 14 |
| Fresh confirmation of Nov 21, Qwen | 5 of 6 | 5 of 6, same tests |
| Fresh confirmation of Nov 21, Llama | 1 of 6 (pinning) | 3 of 6: LLM transitions +3.6, hints hurt (-5.6), strict hedging +3.3; pinning +4.5 not confirmed |
| Extraction v2 effect for Llama, Test / Fresh / Confirm | +8.6 / +3.3 / +5.0 | +7.5 / +4.8 / +6.1 |
| LADL v2 - strongest baseline, Qwen | +0.9 / +6.4 / +7.4 | +2.4 / +5.0 / +7.0 |
| LADL v2 - strongest baseline, Llama | -0.6 / +1.4 / +4.3 | +0.3 / +0.7 / +3.2 |
| LADL v2 - strongest baseline, Mistral | -9.9 / -6.0 / -5.8 | -9.3 / -7.7 / -6.7 |
| Largest effect of the hard memory cap | 1.5 points | 0.6 points |
| Wrong decisions with gold events, Qwen / Llama / Mistral | 13.9 / 14.2 / 13.3% | 12.6 / 13.6 / 15.4% |
| RQ1 stale share under ordinary compaction, Confirm | 33.3 / 29.6 / 26.3% | 33.0 / 30.7 / 27.7% |

The qualitative findings hold: LADL beats summaries, pinning, and LLM-written transitions for Qwen and mostly for Llama; it does not reliably beat the event log; extraction v2 fixes Llama's approval extraction; Mistral's low extraction precision undoes the gain; and RQ1 is unchanged. The claims that change are the ones near the significance threshold, mostly for Llama.

## Fixes made

- **Deterministic serving by default:** `scripts/pace_experiment.sbatch` now sets `VLLM_BATCH_INVARIANT=1`.
- **Shared in-flight requests:** identical requests issued at the same time share one response, so the cache holds exactly what every condition used.
- **Pinned model weights:** `configs/model_revisions.yaml` fixes the Hugging Face revision used by vLLM, the token counter, and the download jobs.
- **Pinned packages:** `requirements.txt` gives exact versions, and `scripts/pace_setup.sbatch` installs `scripts/pace_env_freeze.txt` and warns if the result differs.
- **Run records:** each run's metadata now stores the data path and split, a hash of all source files, a hash of only the modules the run imported, the git commit when available, the model revision, and the vLLM version.
- **Job robustness:** a time limit now saves the cache, each job serves on a free port and checks that the server is its own, and the slow node `atl1-1-03-015-16-0` is excluded.
- **Replay tool:** `python -m src.eval.replay_check` replays finished runs from their caches.

## Remaining limits

- Numbers from runs made before these fixes can only be reproduced to within about 2.6 points per condition, and conclusions near the significance threshold may change.
- Batch invariance was verified on H200 GPUs with vLLM 0.34.0. Other GPU types or vLLM versions may give different, though internally repeatable, outputs.
- Exact replay of a finished run also needs its LLM cache, which is kept on PACE and not in git.

## Reproduce these checks

```bash
sbatch scripts/pace_replay.sbatch
RUN_TAG=-rerun1 CACHE_SUFFIX=rerun1 VLLM_BATCH_INVARIANT=0 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
LIMIT=52 RUN_TAG=-detA CACHE_SUFFIX=detA sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
LIMIT=52 RUN_TAG=-detB CACHE_SUFFIX=detB sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
# Pilot: repeat with configs/llama8b.yaml and configs/mistral7b.yaml
RUN_TAG=-det1 CACHE_SUFFIX=det1 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
RUN_TAG=-det2 CACHE_SUFFIX=det2 MAX_CONCURRENCY=64 sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml confirm
REPLAY_OUT=results/replay_det/qwen2.5-7b-det1 sbatch scripts/pace_replay.sbatch qwen2.5-7b-det1 cache/llm_qwen7b_det1.sqlite
```

After copying the run folders back:

```bash
python -m src.eval.determinism_check results/runs/qwen2.5-7b-det1-pace-confirm-v1 results/runs/qwen2.5-7b-det2-pace-confirm-v1
```

## AI assistance

Claude (Anthropic) ran these checks, implemented the fixes, and drafted this note from the generated outputs. Team members should verify its claims before relying on them.
