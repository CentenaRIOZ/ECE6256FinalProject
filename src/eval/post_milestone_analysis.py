"""Exploratory robustness, disaggregation, and RQ1 tables for extraction v2.

python -m src.eval.post_milestone_analysis --out results/confirm
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.models import available
from src.eval.robustness import REPS, load, rq1_table

BASELINES = ["summary", "pinning", "chrono_v2", "typed_llm_v2"]
GROUP_CONDITIONS = ["summary", "pinning", "chrono_v2", "typed_llm_v2", "lifecycle", "lifecycle_v2"]
GROUPS = {"category": "Category", "gold_reason": "Gold reason", "n_compactions": "Compactions", "kind": "Probe source"}
FLOOR = 2 / (REPS + 1)


def combined(root: Path, run: str, base: str, v2: str, budget: int = 384) -> pd.DataFrame:
    first = load(str(root / f"{run}{base}"), budget)
    second = load(str(root / f"{run}{v2}"), budget)
    second["condition"] = second.condition + "_v2"
    return pd.concat([first, second], ignore_index=True)


def robustness_rows(d: pd.DataFrame, setting: str, value: str, model: str) -> list[dict]:
    rows = []
    ladl = cluster_boot(d[d.condition == "lifecycle_v2"], "accuracy")
    for baseline in BASELINES:
        diff, lo, hi, p = paired_diff(d, "lifecycle_v2", baseline, "accuracy", reps=REPS)
        rows.append(dict(setting=setting, value=value, model=model, ladl_v2=ladl[0], baseline=baseline,
                         baseline_accuracy=cluster_boot(d[d.condition == baseline], "accuracy")[0], diff=diff, lo=lo, hi=hi,
                         p=max(p, FLOOR)))
    return rows


def robustness(root: Path) -> pd.DataFrame:
    rows = []
    for model, run in available(root, ["-pace-hardcap", "-pace-replicate-test-v2", "-pace-replicate-fresh-v2",
                                       "-pace-replicate-fresh-early-v2", "-pace-replicate-fresh-late-v2"]).items():
        for budget in (256, 384, 768):
            d = combined(root, run, "-pace-hardcap", "-pace-replicate-test-v2", budget)
            rows += robustness_rows(d, "Test budget", str(budget), model)
        for placement, v2 in (("early", "-pace-replicate-fresh-early-v2"), ("spread", "-pace-replicate-fresh-v2"),
                              ("late", "-pace-replicate-fresh-late-v2")):
            d = combined(root, run, f"-pace-fresh-{placement}", v2)
            rows += robustness_rows(d, "Fresh placement", placement, model)
    return pd.DataFrame(rows)


def disaggregated(root: Path) -> pd.DataFrame:
    rows = []
    for model, run in available(root, ["-pace-confirm-v1", "-pace-confirm-v2"]).items():
        d = combined(root, run, "-pace-confirm-v1", "-pace-confirm-v2")
        for column, label in GROUPS.items():
            for value, group in d.groupby(column):
                row = dict(model=model, group=label, value=str(value), probes=int((group.condition == "lifecycle").sum()))
                for condition in GROUP_CONDITIONS:
                    row[condition] = cluster_boot(group[group.condition == condition], "accuracy")[0]
                rows.append(row)
    return pd.DataFrame(rows)


def rq1(root: Path) -> pd.DataFrame:
    frames = [load(str(root / f"{run}-pace-confirm-v1"), 384) for run in available(root, ["-pace-confirm-v1"]).values()]
    return rq1_table(pd.concat(frames, ignore_index=True))


def percent(table: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = table.copy()
    out[columns] = (out[columns].astype(float) * 100).round(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/confirm")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    robust, groups, stale = robustness(root), disaggregated(root), rq1(root)
    robust.to_csv(out / "v2_robustness.csv", index=False)
    groups.to_csv(out / "disaggregated.csv", index=False)
    stale.to_csv(out / "rq1.csv", index=False)
    robust_view = percent(robust, ["ladl_v2", "baseline_accuracy", "diff", "lo", "hi"]).round({"p": 4})
    group_view = percent(groups, GROUP_CONDITIONS)
    rq1_cols = ["wrong", "stale", "missing", "other", "stale_share_of_wrong", "chance_share_of_wrong", "excess", "excess_lo", "excess_hi"]
    rq1_view = percent(stale[["model", "condition", "n", *rq1_cols]], rq1_cols)
    text = ["# Exploratory post-milestone analyses", "", "P-values are uncorrected.", "",
            "## Extraction v2 across budgets and compaction placements", "", robust_view.to_markdown(index=False), "",
            "## Confirm accuracy by group", "", group_view.to_markdown(index=False), "",
            "## RQ1 on Confirm", "", rq1_view.to_markdown(index=False), ""]
    (out / "exploratory.md").write_text("\n".join(text))
    print(robust_view.to_string(index=False))
    print(group_view.to_string(index=False))
    print(rq1_view.to_string(index=False))


if __name__ == "__main__":
    main()
