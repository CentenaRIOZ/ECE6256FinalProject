"""Run settings of the follow-up experiments in docs/followup_experiments_plan.md, shared by the job script and reports.

python -m src.eval.followup_settings noise qwen2.5-7b   # one "<suffix> <gold-noise spec>" line per noise setting
python -m src.eval.followup_settings swap qwen2.5-7b    # one "<suffix> <extractor run> <version>" line per swap cell
"""
from __future__ import annotations

import sys

RUNS = ["qwen2.5-7b", "llama3.1-8b", "mistral-7b-v0.3"]
CONDITIONS = ["lifecycle", "lifecycle_nohint", "chrono", "chrono_hint"]
LATENCY_CONDITIONS = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle"]
# Event precision and recall of each model's own Confirm extraction (docs/post_milestone_results.md).
MATCHED = {"qwen2.5-7b": {"v1": (0.884, 0.843), "v2": (0.905, 0.871)},
           "llama3.1-8b": {"v1": (0.857, 0.870), "v2": (0.912, 0.935)},
           "mistral-7b-v0.3": {"v1": (0.519, 0.814), "v2": (0.426, 0.826)}}
PRECISIONS = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
RECALLS = [0.9, 0.8, 0.7, 0.6, 0.5]


def suffix(precision: float, recall: float, seed: int = 0) -> str:
    return f"p{round(precision * 1000)}-r{round(recall * 1000)}-s{seed}"


def spec(precision: float, recall: float, seed: int = 0) -> str:
    return f"precision={precision},recall={recall},seed={seed}"


def noise_settings(run: str) -> list[tuple[float, float, int, str]]:
    """(precision, recall, seed, kind) for the 15 planned settings of one model."""
    rows = [(1.0, 1.0, 0, "perfect")]
    rows += [(p, 1.0, 0, "false events") for p in PRECISIONS]
    rows += [(1.0, r, 0, "missed events") for r in RECALLS]
    rows += [(p, r, 0, f"matched {v}") for v, (p, r) in MATCHED[run].items()]
    rows.append((0.5, 1.0, 1, "seed check"))
    return rows


def swap_cells(run: str) -> list[tuple[str, str]]:
    """(extractor run, extraction version) for the four new cells where this model decides."""
    return [(other, v) for other in RUNS if other != run for v in ("v1", "v2")]


def main():
    what, run = sys.argv[1], sys.argv[2]
    if what == "noise":
        for p, r, seed, _ in noise_settings(run):
            print(suffix(p, r, seed), spec(p, r, seed))
    elif what == "swap":
        for other, v in swap_cells(run):
            print(f"{other}-{v}", other, v)
    else:
        raise SystemExit(f"unknown setting list {what}")


if __name__ == "__main__":
    main()
