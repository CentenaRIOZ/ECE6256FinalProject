"""Robustness checks: RQ1 error composition against a chance baseline, and Holm-corrected paired tests.

python -m src.eval.robustness --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b --budget 384 --out results/robustness

Chance baseline for "stale": if a wrong state answer were drawn uniformly from the seven non-gold labels,
the probability of naming an earlier status is |earlier statuses other than gold| / 7.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import paired_diff, recall_error_type

BASELINES = ["summary", "pinning", "chrono", "typed_llm"]
RQ1_CONDITIONS = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_nohint"]
REPS = 2000
N_WRONG_LABELS = 7


def load(run: str, budget: int) -> pd.DataFrame:
    path = Path(run)
    model = json.loads((path / f"meta_B{budget}.json").read_text())["config"]["model"].split("/")[-1]
    rows = [json.loads(line) for line in open(path / f"probes_B{budget}.jsonl")]
    df = pd.DataFrame(rows).drop(columns=["ledger_item", "summary"], errors="ignore")
    df["model"] = model
    return df


def binary(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in ("pred_decision", "gold_decision"):
        out[col] = out[col].where(out[col] == "act", "no_act")
    return out


def ratio_ci(frame: pd.DataFrame, num: str, den: str, seed: int = 0) -> tuple[float, float, float]:
    agg = frame.groupby("timeline_id")[[num, den]].sum()
    n, d = agg[num].to_numpy(float), agg[den].to_numpy(float)
    if d.sum() == 0:
        return np.nan, np.nan, np.nan
    idx = np.random.default_rng(seed).integers(0, len(n), size=(REPS, len(n)))
    with np.errstate(invalid="ignore", divide="ignore"):
        boot = n[idx].sum(1) / d[idx].sum(1)
    return n.sum() / d.sum(), *np.percentile(boot[~np.isnan(boot)], [2.5, 97.5])


def rq1_table(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df.item_mutable & (df.compactions_since_creation >= 1) & df.condition.isin(RQ1_CONDITIONS)].copy()
    sub["error_type"] = [recall_error_type(r) for r in sub.itertuples()]
    sub["one"] = 1.0
    sub["wrong"] = (sub.error_type != "correct").astype(float)
    for kind in ("stale", "missing", "other"):
        sub[kind] = (sub.error_type == kind).astype(float)
    sub["chance_stale"] = [w * len(set(p or []) - {g}) / N_WRONG_LABELS
                           for w, p, g in zip(sub.wrong, sub.prior_labels, sub.gold_label)]
    sub["excess_stale"] = sub.stale - sub.chance_stale
    rows = []
    for (model, cond), d in sub.groupby(["model", "condition"]):
        row = dict(model=model, condition=cond, n=len(d))
        for kind in ("wrong", "stale", "missing", "other"):
            row[kind], row[f"{kind}_lo"], row[f"{kind}_hi"] = ratio_ci(d, kind, "one")
        row["stale_share_of_wrong"] = ratio_ci(d, "stale", "wrong")[0]
        row["chance_share_of_wrong"] = ratio_ci(d, "chance_stale", "wrong")[0]
        row["excess"], row["excess_lo"], row["excess_hi"] = ratio_ci(d, "excess_stale", "wrong")
        rows.append(row)
    return pd.DataFrame(rows)


def holm(p: np.ndarray) -> np.ndarray:
    order = np.argsort(p)
    adjusted = np.empty(len(p))
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p) - rank) * p[i]))
        adjusted[i] = running
    return adjusted


def paired_table(df: pd.DataFrame) -> pd.DataFrame:
    floor = 2 / (REPS + 1)  # smallest two-sided p a bootstrap of this size can resolve
    rows = []
    for metric, frame in (("four_way", df), ("execute", binary(df))):
        family = []
        for model, d in frame.groupby("model"):
            for base in BASELINES:
                diff, lo, hi, p = paired_diff(d, "lifecycle", base, "accuracy", reps=REPS)
                family.append(dict(metric=metric, model=model, baseline=base, diff=diff, lo=lo, hi=hi,
                                   p=max(p, floor)))
        adjusted = holm(np.array([r["p"] for r in family]))
        for r, a in zip(family, adjusted):
            rows.append({**r, "p_holm": a, "significant_holm": a < 0.05})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--out", default="results/robustness")
    a = ap.parse_args()
    df = pd.concat([load(r, a.budget) for r in a.runs], ignore_index=True)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rq1 = rq1_table(df)
    paired = paired_table(df)
    rq1.to_csv(out / f"rq1_chance_B{a.budget}.csv", index=False)
    paired.to_csv(out / f"paired_holm_B{a.budget}.csv", index=False)
    view = rq1[["model", "condition", "n", "wrong", "stale", "missing", "other", "stale_share_of_wrong",
                "chance_share_of_wrong", "excess", "excess_lo", "excess_hi"]].copy()
    view.iloc[:, 3:] = (view.iloc[:, 3:] * 100).round(1)
    print(view.to_string(index=False))
    show = paired.copy()
    show[["diff", "lo", "hi"]] = (show[["diff", "lo", "hi"]] * 100).round(1)
    print(show.round({"p": 4, "p_holm": 4}).to_string(index=False))


if __name__ == "__main__":
    main()
