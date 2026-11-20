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

## Results (test split, 664 probes, B=384)
Full report: [`results/report_B384.md`](results/report_B384.md). Paper: [`paper/main.pdf`](paper/main.pdf). Poster: [`poster/poster.pdf`](poster/poster.pdf).

| Condition | Qwen2.5-7B acc. | Llama-3.1-8B acc. |
|---|---|---|
| Full history (reference) | 60.4 | 81.6 |
| Ordinary compaction | 60.1 | 73.5 |
| Constraint pinning | 64.2 | 66.4 |
| Chronological event ledger | 69.9 | **77.0** |
| Typed ledger, LLM transitions | 69.1 | 69.4 |
| **Lifecycle ledger (ours)** | **76.4** | 71.1 |
| Ours, gold events | 83.1 | 81.5 |
| Ours, strict hedging (post hoc) | 76.1 | 76.8 |

## Setup
```bash
conda activate index            # or: pip install -r requirements.txt  (Python 3.10+)
python -m pytest -q tests       # reducer / generator / registry unit tests
```

## Reproduce (local, 2 GPUs)
```bash
scripts/serve_vllm.sh Qwen/Qwen2.5-7B-Instruct 0 8000           # terminal 1
scripts/serve_vllm.sh meta-llama/Llama-3.1-8B-Instruct 1 8001   # terminal 2
scripts/run_all.sh        # data -> paraphrase -> tests -> runs (B=384, sweep 256/768) -> analysis
```
On PACE-ICE: `sbatch scripts/pace_run.sbatch configs/qwen7b.yaml Qwen/Qwen2.5-7B-Instruct`.
All LLM calls are cached in `cache/*.sqlite` (temperature 0, seed 0), so re-running analysis is free.

Individual steps:
| Step | Command |
|---|---|
| Gold timelines + dialogues | `python -m src.generation.build --out data --n-timelines 48` |
| Paraphrase (+ judge) | `python -m src.generation.paraphrase` |
| Run conditions | `python -m src.eval.run --config configs/qwen7b.yaml [--conditions summary,lifecycle] [--limit 5] [--budget 256]` |
| Extraction quality | `python -m src.eval.extraction_eval --extractions results/runs/<run>/extractions.jsonl` |
| Tables + figures | `python -m src.eval.analyze --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b` |
| Budget sweep | `python -m src.eval.budget_sweep --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b` |

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
results/     runs/ (raw probe outputs), tables/, figures/, report_B*.md
paper/ poster/
```
