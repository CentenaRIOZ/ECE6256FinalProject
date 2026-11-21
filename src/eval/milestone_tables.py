"""Milestone tables from the PACE-ICE hard-cap runs.

python -m src.eval.milestone_tables --budget 384 --out paper/tables

Test is the original test split. Fresh is the set of 52 new timelines balanced over primary families.
"Exec." is a post-hoc sensitivity metric: accuracy of the binary execute / do-not-execute decision,
obtained by merging wait, clarify and decline in both predictions and gold labels.
Stars mark Holm-corrected p < 0.05 over the 12 tests of one split and metric.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.robustness import REPS, binary, holm, load

RUNS = {"Qwen2.5-7B": "qwen2.5-7b", "Llama-3.1-8B": "llama3.1-8b"}
ROWS = [("full", "Full history (no compaction)"), ("summary", "Ordinary compaction"),
        ("pinning", "Constraint pinning"), ("chrono", "Chronological event ledger"),
        ("typed_llm", "Typed ledger, LLM transitions"), ("lifecycle", r"\textbf{LADL (ours)}"),
        ("lifecycle_nohint", "LADL without action hints"), ("lifecycle_strict", "LADL, strict hedging (post hoc)"),
        ("lifecycle_gold", "LADL, gold events")]
PAIRS = [("lifecycle", "summary", "LADL $-$ ordinary compaction"), ("lifecycle", "pinning", "LADL $-$ pinning"),
         ("lifecycle", "chrono", "LADL $-$ chronological ledger"), ("lifecycle", "typed_llm", "LADL $-$ LLM transitions"),
         ("lifecycle", "lifecycle_nohint", "LADL $-$ LADL without hints"),
         ("lifecycle_strict", "lifecycle", "Strict hedging $-$ LADL")]
FLOOR = 2 / (REPS + 1)


def read(suffix: str, budget: int) -> dict[str, pd.DataFrame]:
    return {label: load(f"results/runs/{run}{suffix}", budget) for label, run in RUNS.items()}


def ci_cell(d: pd.DataFrame) -> str:
    acc, lo, hi = cluster_boot(d, "accuracy")
    return f"{acc * 100:.1f} [{lo * 100:.1f}, {hi * 100:.1f}]"


def main_table(test: dict[str, pd.DataFrame], fresh: dict[str, pd.DataFrame]) -> str:
    lines = [r"\begin{tabular}{lccrrccrr}", r"\toprule",
             r" & \multicolumn{4}{c}{Qwen2.5-7B} & \multicolumn{4}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
             r"Condition & Test acc. & Fresh acc. & Exec. & Tok. & Test acc. & Fresh acc. & Exec. & Tok. \\",
             r"\midrule"]
    for cond, name in ROWS:
        cells = [name]
        for label in RUNS:
            t, f = test[label], fresh[label]
            t, f = t[t.condition == cond], f[f.condition == cond]
            execute = cluster_boot(binary(f), "accuracy")[0]
            tokens = t[t.compactions_before_probe > 0].memory_tokens.mean()
            cells += [ci_cell(t), ci_cell(f), f"{execute * 100:.1f}", "--" if cond == "full" else f"{tokens:.0f}"]
        if cond == "lifecycle_nohint":
            lines.append(r"\midrule")
        lines.append(" & ".join(cells) + r" \\")
    return "\n".join(lines + [r"\bottomrule", r"\end{tabular}", ""])


def family_cells(frames: dict[str, pd.DataFrame], with_ci: bool) -> dict[tuple, str]:
    results = []
    for label in RUNS:
        for a, b, _ in PAIRS:
            diff, lo, hi, p = paired_diff(frames[label], a, b, "accuracy", reps=REPS)
            results.append(((label, a, b), diff, lo, hi, max(p, FLOOR)))
    adjusted = holm(np.array([r[4] for r in results]))
    cells = {}
    for (key, diff, lo, hi, _), p_holm in zip(results, adjusted):
        star = "$^{*}$" if p_holm < 0.05 else ""
        text = f"{diff * 100:+.1f}{star}"
        if with_ci:
            text += f" [{lo * 100:+.1f}, {hi * 100:+.1f}]"
        cells[key] = text.replace("-", "$-$")
    return cells


def paired_table(test: dict[str, pd.DataFrame], fresh: dict[str, pd.DataFrame]) -> str:
    test_cells = family_cells(test, with_ci=True)
    fresh_cells = family_cells(fresh, with_ci=True)
    execute_cells = family_cells({label: binary(d) for label, d in fresh.items()}, with_ci=False)
    lines = [r"\begin{tabular}{lccrccr}", r"\toprule",
             r" & \multicolumn{3}{c}{Qwen2.5-7B} & \multicolumn{3}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
             r"Comparison & Test $\Delta$Acc. & Fresh $\Delta$Acc. & $\Delta$Exec. & "
             r"Test $\Delta$Acc. & Fresh $\Delta$Acc. & $\Delta$Exec. \\", r"\midrule"]
    for a, b, name in PAIRS:
        cells = [name]
        for label in RUNS:
            key = (label, a, b)
            cells += [test_cells[key], fresh_cells[key], execute_cells[key]]
        lines.append(" & ".join(cells) + r" \\")
    return "\n".join(lines + [r"\bottomrule", r"\end{tabular}", ""])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--out", default="paper/tables")
    a = ap.parse_args()
    test_runs = read("-pace-hardcap", a.budget)
    fresh_runs = read("-pace-fresh-spread", a.budget)
    out = Path(a.out)
    (out / "milestone_main.tex").write_text(main_table(test_runs, fresh_runs))
    (out / "milestone_paired.tex").write_text(paired_table(test_runs, fresh_runs))
