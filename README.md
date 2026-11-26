# Beyond Remembering: Active Constraints & Pending Commitments Across Context Compaction

ECE 6256 / CS 6604, Fall 2026 — Sheng Lu, Qixiang Fan, Ziyan Fan, Xiuping Zhu.
Proposal: [docs/Final_Project_Proposal.pdf](docs/Final_Project_Proposal.pdf)

## Idea
Context compaction can lose or corrupt *mutable* state: revoked prohibitions,
conditional commitments that become ready, and actions already completed. We
test whether a **Lifecycle-Aware Dialogue Ledger** (typed records + a deterministic
reducer of evidence-backed state transitions) improves tool-action correctness
under repeated compaction, compared with summaries, pinning, and chronological ledgers.

- **RQ1:** Does mutable state degrade differently from static constraints (stale vs. missing)?
- **RQ2:** At equal memory budget, does lifecycle tracking beat pinning / chronological memory?
- **RQ3:** Which errors come from wrong stored state vs. wrong decisions given correct state?

## Method
- **Record:** id, type (prohibition | conditional commitment | action outcome), scope, trigger, evidence turn, event time.
- **States:** prohibition `active → revoked`; commitment `waiting → ready → completed`, or `cancelled`.
  - Only explicit approval that satisfies the guard moves `waiting → ready`.
  - Only a verified mock-tool success moves `ready → completed`. A failed call leaves the commitment pending.
  - Every transition keeps its supporting event ID. Ambiguous updates trigger `clarify`.
- **Loop:** compaction at fixed checkpoints, with the ledger persisted inside the same token budget. The policy picks `act | wait | clarify | decline` and uses sandboxed mock tools.

## Data
- 30–50 gold event timelines covering revocation, success/failure followed by repeat requests, and conditional triggering, including misleading partial approvals.
- 120–200 dialogues of 25–40 turns built from templates plus LLM paraphrase, with filler and 1–5 compaction rounds.
- Held-out templates are used only for testing.

## Conditions
1. Full history without compaction (upper reference)
2. Ordinary compaction
3. Constraint pinning
4. Chronological event ledger
5. Typed ledger with LLM-written transitions
6. **Lifecycle ledger (ours)**

Conditions 2–5 use matched token budgets.

Ablations: transition logic, tool-success evidence, compaction count and location, gold-state intervention, and gold extraction as an upper bound.

## Metrics
- **Primary:** action correctness, violation rate, over-restriction, premature completion, duplicate execution.
- **Secondary:** per-checkpoint state accuracy, clarification rate, tokens, latency, cost.
- **Statistics:** paired comparisons and bootstrap 95% CIs resampled over timelines.
- **Error taxonomy:** bad extraction / bad transition / lost ledger state / wrong action despite correct state.

## Compute & timeline
- PACE-ICE inference with 7–8B instruction models. No training. Log GPU type and hours.
- **Nov 19:** milestone, ordinary-summary baseline plus a first result
- **Dec 3:** poster
- **Dec 8:** paper and code

## Roles
- **Sheng Lu:** taxonomy, gold timelines, paraphrase validation
- **Qixiang Fan:** extraction, reducer, transition ablations
- **Ziyan Fan:** compaction/pinning baselines, PACE-ICE
- **Xiuping Zhu:** evaluation harness, statistics, error analysis, reproducibility

## Results (Test split, 664 probes, B=384, hard memory cap)
Numbers in this README and in `docs/` are copied from result files. Those files, the raw run records, and logs are generated locally under `results/` by the commands below and are not stored in git. Paper: [`paper/main.pdf`](paper/main.pdf). Poster: [`poster/poster.pdf`](poster/poster.pdf).
PACE-ICE control experiments and their interpretation: [`docs/pace_experiments.md`](docs/pace_experiments.md).
Post-milestone confirmation, extraction, and third-model (Mistral-7B) results: [`docs/post_milestone_results.md`](docs/post_milestone_results.md).
Reproducibility checks and the deterministic reruns: [`docs/reproducibility.md`](docs/reproducibility.md).
Dialogue-level metrics, cost and latency, the extraction-noise dose-response, and extractor/decision-model swaps: [`docs/followup_results.md`](docs/followup_results.md) (plan: [`docs/followup_experiments_plan.md`](docs/followup_experiments_plan.md)).

Four-way decision accuracy (%) from the deterministic PACE-ICE runs. Extraction v1 unless noted. Mistral-7B was added later as a held-out model. Bold marks the best condition under compaction in each column, excluding gold events.

| Condition | Qwen2.5-7B | Llama-3.1-8B | Mistral-7B |
|---|---|---|---|
| Full history (reference) | 60.1 | 81.9 | 72.7 |
| Ordinary compaction | 60.1 | 72.0 | **66.9** |
| Constraint pinning | 62.5 | 68.8 | 66.6 |
| Chronological event ledger | 70.0 | 78.6 | 53.8 |
| Typed ledger, LLM transitions | 70.0 | 69.0 | 52.7 |
| **Lifecycle ledger (ours)** | **74.1** | 72.4 | 61.7 |
| Ours, extraction v2 | 74.1 | **80.0** | 57.5 |
| Ours, strict hedging (post hoc) | 74.1 | 78.0 | 61.7 |
| Ours, gold events | 82.2 | 83.4 | 84.0 |

## Setup
```bash
pip install -r requirements.txt  # Python 3.12, exact versions; full PACE-ICE environment: scripts/pace_env_freeze.txt
python -m pytest -q tests       # reducer / generator / registry unit tests
```

## Reproduce (local, 2 GPUs)
```bash
scripts/serve_vllm.sh Qwen/Qwen2.5-7B-Instruct 0 8000           # terminal 1
scripts/serve_vllm.sh meta-llama/Llama-3.1-8B-Instruct 1 8001   # terminal 2
scripts/run_all.sh        # data -> paraphrase -> tests -> runs (B=384, sweep 256/768) -> analysis
```
On PACE-ICE: `sbatch scripts/pace_run.sbatch configs/qwen7b.yaml Qwen/Qwen2.5-7B-Instruct`.
All LLM calls are cached in `cache/*.sqlite` (temperature 0, seed 0), so re-running analysis is free. PACE-ICE jobs serve the model revisions in `configs/model_revisions.yaml` with batch-invariant vLLM, so a rerun reproduces every response exactly. Runs made before Nov 24, 2026 were not batch-invariant; see [`docs/reproducibility.md`](docs/reproducibility.md) for what that means for their numbers.

Individual steps:
| Step | Command |
|---|---|
| Gold timelines + dialogues | `python -m src.generation.build --out data --n-timelines 48` |
| Paraphrase (+ judge) | `python -m src.generation.paraphrase` |
| Run conditions | `python -m src.eval.run --config configs/qwen7b.yaml [--conditions summary,lifecycle] [--limit 5] [--budget 256]` |
| Extraction quality | `python -m src.eval.extraction_eval --extractions results/runs/<run>/extractions.jsonl` |
| Tables + figures | `python -m src.eval.analyze --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b results/runs/qwen2.5-7b-strict results/runs/llama3.1-8b-strict` |
| Budget sweep | `python -m src.eval.budget_sweep --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b` |
| Milestone tables | `python -m src.eval.milestone_tables --budget 384 --out paper/tables` |
| PACE-ICE setup | `sbatch scripts/pace_setup.sbatch` (versions: `scripts/pace_env_freeze.txt`) |
| PACE-ICE controls, no cap and hard cap | `sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml full`, then the same with `configs/llama8b.yaml` |
| Control report | `python -m src.eval.control_report --budget 384 --out results/controls` |
| RQ1 chance baseline and Holm tests | `python -m src.eval.robustness --runs results/runs/qwen2.5-7b-pace-hardcap results/runs/llama3.1-8b-pace-hardcap --budget 384 --out results/robustness` |
| Fresh timelines and compaction placements | `python -m src.generation.build --fresh --out data/fresh --n-per-family 4 --seed 20261121` |
| PACE-ICE budget, fresh-data, and placement runs | `sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml extended`, then the same with `configs/llama8b.yaml` |
| Extended report | `python -m src.eval.extended_report --out results/extended` |
| Error attribution and approval extraction | `python -m src.eval.error_analysis --out results/extended` |
| New-language Confirm data | `python -m src.generation.build --confirm --out data/confirm --n-per-family 4 --seed 20261123` |
| PACE-ICE post-milestone runs | `sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml dev`, then `confirm`, `replicate`, and `v2-robust`; repeat with `configs/llama8b.yaml` |
| Dev extraction comparison | `python -m src.eval.dev_extraction_report --runs results/runs` |
| Planned confirmation tests | `python -m src.eval.confirm_report --out results/confirm` |
| Exploratory replication | `python -m src.eval.replication_report --out results/confirm` |
| v2 robustness, disaggregation, and RQ1 | `python -m src.eval.post_milestone_analysis --out results/confirm` |
| Real error examples | `python -m src.eval.error_examples --out results/confirm/error_examples.md` |
| Replay finished runs from their caches (PACE-ICE) | `sbatch scripts/pace_replay.sbatch` |
| Reports from the deterministic runs | `python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det`, then any report above with `--runs results/runs_det` |
| Check two runs are identical | `python -m src.eval.determinism_check <run_dir_a> <run_dir_b>` |
| Compare planned tests across runs | `python -m src.eval.run_variability --run original=results/runs --run deterministic=results/runs_det --out results/det/variability` |
| PACE-ICE third model (Mistral-7B, plan in `docs/third_model_plan.md`) | `sbatch scripts/pace_download.sbatch mistralai/Mistral-7B-Instruct-v0.3`, then `sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml hardcap,extended,replicate,v2-robust` and `CACHE_SUFFIX=confirm sbatch scripts/pace_experiment.sbatch configs/mistral7b.yaml confirm` |
| Three-model accuracy and extraction | `python -m src.eval.three_model_report --out results/confirm` |
| Follow-up runs on PACE-ICE (plan in `docs/followup_experiments_plan.md`) | `CACHE_SUFFIX=followup sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml noise,swap` and `LIMIT=8 CACHE_SUFFIX=latency sbatch scripts/pace_experiment.sbatch configs/qwen7b.yaml latency`, for each model |
| Run with other events | `python -m src.eval.run ... --gold-noise precision=0.5,recall=1.0,seed=0` or `--events-from results/runs/<run>/extractions.jsonl` |
| Check `--events-from` against the deterministic runs (PACE-ICE) | `sbatch scripts/pace_events_replay.sbatch` |
| Dialogue-level metrics, cost, and latency | `python -m src.eval.dialogue_report --runs results/runs_det --replays results/replay_followup/det_confirm --out results/followup/dialogue` |
| Noise dose-response and swap reports | `python -m src.eval.followup_report --runs results/runs_det --out results/followup` |

## Data
- 48 gold timelines (`data/timelines/`). Each combines a primary family, a secondary family from another category, and a static control prohibition, with one distinct tool per item.
- Families:
  - **Revocation:** REV1 revoke, REV2 reinstate, REV3 ambiguous then revoke, REV4 selective revoke
  - **Completion:** DONE1 success then repeat, DONE2 failure, DONE3 failure then retry, COND4/COND5 triggered then success/failure
  - **Conditional:** COND1 partial then final approval, COND2 only partial approvals, COND3 hedged approval, CANC1 cancelled then approved
- 192 dialogues: each timeline has 4 variants with 1, 2, 3 or 5 compactions, and variants 1 and 3 are paraphrased. Dialogues are 24–42 turns.
- 872 decision probes. The dev split is 12 timelines rendered with dev templates and is used only for prompt development. The test split is 36 timelines rendered with held-out templates.
- Probes come from teammates, a workflow engine or reminders, never from the user. The model's answer is not fed back, so the gold labels stay deterministic.
- Paraphrases are kept only if they pass entity/cue checks and an equivalence judge (Qwen). A manual audit of 40 accepted paraphrases is in `data/paraphrase_audit.md`.

## Conditions (`src/memory/managers.py`)
All conditions use a memory budget of B tokens (default 384) for the summary plus the persistent block. The block may use at most 0.6·B.

| id | description |
|---|---|
| `full` | Full history, no compaction (reference) |
| `summary` | Recursive task-focused compaction |
| `pinning` | Summary plus a pinned rules text, updated by the LLM after every user/tool turn |
| `chrono` | Summary plus a chronological log of extracted events, with no states (oldest entries dropped at the budget) |
| `typed_llm` | Summary plus a typed ledger whose statuses the LLM writes |
| `lifecycle` | **Ours:** summary plus a typed ledger with the deterministic reducer |
| `lifecycle_gold` | The same ledger built from gold events. This is the gold-state intervention and also the extraction upper bound |
| `abl_noguard` | Ours with guard logic removed |
| `abl_noreceipt` | Ours with tool-success evidence removed |

## Layout
```
data/        timelines/ (gold specs), dialogues/ (generated jsonl), paraphrase_audit.md
src/
  generation/  content.py (tools, actions, templates), build.py (families, rendering, gold labels), paraphrase.py
  extraction/  extractor.py (per-turn LLM extraction + item registry)
  ledger/      reducer.py (record schema, deterministic lifecycle reducer, gold decision rules, rendering)
  memory/      managers.py (all memory conditions, compaction, budgets)
  policy/      policy.py (act/wait/clarify/decline policy + state-recall query)
  llm/         client.py (async OpenAI-compatible client, sqlite cache, token counting)
  eval/        run.py, analyze.py, extraction_eval.py, budget_sweep.py
configs/     model / budget configs (dev_* = dev split)
scripts/     serve_vllm.sh, run_all.sh, pace_run.sbatch
results/     generated locally, not in git: runs/ (raw probe outputs), reports, tables, figures
paper/ poster/
```
