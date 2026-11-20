"""Accuracy vs. memory budget B (matched across conditions).

python -m src.eval.budget_sweep --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b --out results
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd

from src.eval.analyze import COLORS, COND_NAME, MARKERS, cluster_boot, setup_mpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    rows = []
    for run in a.runs:
        for f in sorted(Path(run).glob("probes_B*.jsonl")):
            B = int(re.search(r"B(\d+)", f.name).group(1))
            mdl = json.loads((Path(run) / f"meta_B{B}.json").read_text())["config"]["model"].split("/")[-1]
            d = pd.read_json(f, lines=True)
            for c, dc in d.groupby("condition"):
                if c in ("full", "lifecycle_gold") or c.startswith("abl"):
                    continue
                v, lo, hi = cluster_boot(dc, "accuracy")
                rows.append(dict(model=mdl, budget=B, condition=c, accuracy=v, lo=lo, hi=hi,
                                 memory_tokens=dc.memory_tokens.mean()))
    t = pd.DataFrame(rows).sort_values(["model", "condition", "budget"])
    out = Path(a.out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    t.to_csv(out / "tables" / "budget_sweep.csv", index=False)
    print(t.pivot_table(index=["model", "condition"], columns="budget", values="accuracy").round(3).to_markdown())

    plt = setup_mpl()
    models = sorted(t.model.unique(), key=lambda m: not m.startswith("Qwen"))
    fig, axes = plt.subplots(1, len(models), figsize=(6.8, 3.0), sharey=True, squeeze=False)
    for ax, mdl in zip(axes[0], models):
        for c, d in t[t.model == mdl].groupby("condition"):
            ax.errorbar(d.budget, d.accuracy, yerr=[d.accuracy - d.lo, d.hi - d.accuracy], marker=MARKERS[c],
                        color=COLORS[c], lw=2, ms=6, capsize=2, label=COND_NAME[c])
        ax.set_xscale("log", base=2)
        ax.set_xticks(sorted(t.budget.unique()), [str(b) for b in sorted(t.budget.unique())])
        ax.set_xlabel("Memory budget B (tokens)")
        ax.set_title(mdl, fontsize=9)
    axes[0][0].set_ylabel("Action accuracy")
    h, l = axes[0][0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=7, loc="lower center", ncol=3, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    (out / "figures").mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "figures" / "fig_budget.pdf")
    fig.savefig(out / "figures" / "fig_budget.png", dpi=200)


if __name__ == "__main__":
    main()
