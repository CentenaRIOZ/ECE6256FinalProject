"""Fresh-timeline confirmation, hard-cap budget sweep, and compaction-placement analysis.

python -m src.eval.extended_report --out results/extended

Confirmation rule, fixed before the fresh-timeline runs:
- Data: 52 new timelines (4 per primary family), held-out template pool, no paraphrases, spread compaction,
  B=384, hard cap.
- Primary metric: four-way accuracy. Secondary metric: execute versus do-not-execute accuracy.
- Tests per model: LADL minus ordinary compaction, pinning, chronological ledger, and LLM transitions;
  LADL minus LADL without action hints; strict hedging minus LADL.
- Holm correction runs over all 12 tests within a metric.
- An effect is confirmed only if it has the same sign as on the original test split and Holm p < 0.05.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.robustness import REPS, binary, holm, load

MODELS = {"Qwen2.5-7B-Instruct": "qwen2.5-7b", "Llama-3.1-8B-Instruct": "llama3.1-8b"}
TESTS = [("lifecycle", "summary"), ("lifecycle", "pinning"), ("lifecycle", "chrono"), ("lifecycle", "typed_llm"),
         ("lifecycle", "lifecycle_nohint"), ("lifecycle_strict", "lifecycle")]
COMPACTED = ["summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_nohint", "lifecycle_strict"]
PLACEMENTS = ("spread", "early", "late")
BUDGETS = (256, 384, 768)
FLOOR = 2 / (REPS + 1)


ROOT = Path("results/runs")


def read(suffix: str, budget: int = 384) -> pd.DataFrame:
    return pd.concat([load(str(ROOT / f"{run}{suffix}"), budget) for run in MODELS.values()], ignore_index=True)


def accuracy_rows(df: pd.DataFrame, **labels) -> list[dict]:
    rows = []
    for (model, cond), d in df.groupby(["model", "condition"]):
        acc, lo, hi = cluster_boot(d, "accuracy")
        ex, ex_lo, ex_hi = cluster_boot(binary(d), "accuracy")
        compacted = d[d.compactions_before_probe > 0]
        rows.append(dict(**labels, model=model, condition=cond, n=len(d), accuracy=acc, lo=lo, hi=hi, execute=ex,
                         execute_lo=ex_lo, execute_hi=ex_hi, memory_tokens=compacted.memory_tokens.mean(),
                         max_tokens=compacted.memory_tokens.max()))
    return rows


def confirmation(fresh: pd.DataFrame, original: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric, new, old in (("four_way", fresh, original), ("execute", binary(fresh), binary(original))):
        family = []
        for model in MODELS:
            n, o = new[new.model == model], old[old.model == model]
            for a, b in TESTS:
                diff, lo, hi, p = paired_diff(n, a, b, "accuracy", reps=REPS)
                before = paired_diff(o, a, b, "accuracy", reps=REPS)[0]
                family.append(dict(metric=metric, model=model, a=a, b=b, original_diff=before, diff=diff, lo=lo, hi=hi,
                                   p=max(p, FLOOR)))
        for row, adjusted in zip(family, holm(np.array([r["p"] for r in family]))):
            same_sign = np.sign(row["diff"]) == np.sign(row["original_diff"])
            rows.append({**row, "p_holm": adjusted, "confirmed": bool(same_sign and adjusted < 0.05)})
    return pd.DataFrame(rows)


def contrast_rows(df: pd.DataFrame, label: dict) -> list[dict]:
    rows = []
    for model, d in df.groupby("model"):
        for base in ("summary", "pinning", "chrono", "typed_llm", "lifecycle_nohint"):
            diff, lo, hi, p = paired_diff(d, "lifecycle", base, "accuracy", reps=REPS)
            rows.append(dict(**label, model=model, baseline=base, diff=diff, lo=lo, hi=hi, p=max(p, FLOOR)))
    return rows


def by_category(df: pd.DataFrame) -> pd.DataFrame:
    frame = df[df.condition.isin(["full", *COMPACTED, "lifecycle_gold"])].copy()
    frame["ok"] = frame.pred_decision == frame.gold_decision
    return frame.groupby(["model", "condition", "category"]).ok.mean().unstack("category").reset_index()


def pct(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    out[columns] = (out[columns].astype(float) * 100).round(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/extended")
    ap.add_argument("--runs", default="results/runs")
    a = ap.parse_args()
    global ROOT
    ROOT = Path(a.runs)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    original = read("-pace-hardcap")
    placements = {p: read(f"-pace-fresh-{p}") for p in PLACEMENTS}
    fresh = placements["spread"]
    confirmed = confirmation(fresh, original)

    fresh_acc = pd.DataFrame(accuracy_rows(fresh, data="fresh"))
    budget = pd.DataFrame([r for b in BUDGETS for r in accuracy_rows(read("-pace-hardcap", b), budget=b)])
    budget_contrasts = pd.DataFrame([r for b in BUDGETS for r in contrast_rows(read("-pace-hardcap", b), dict(budget=b))])
    place = pd.DataFrame([r for p, d in placements.items() for r in accuracy_rows(d, placement=p)])
    place_contrasts = pd.DataFrame([r for p, d in placements.items() for r in contrast_rows(d, dict(placement=p))])
    categories = by_category(fresh)

    tables = dict(fresh_accuracy=fresh_acc, confirmation=confirmed, budget_accuracy=budget,
                  budget_contrasts=budget_contrasts, placement_accuracy=place, placement_contrasts=place_contrasts,
                  fresh_by_category=categories)
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)

    acc_cols = ["accuracy", "lo", "hi", "execute", "execute_lo", "execute_hi"]
    cat_cols = [c for c in categories.columns if c not in ("model", "condition")]
    sections = [
        ("Fresh timelines: accuracy", pct(fresh_acc, acc_cols).round({"memory_tokens": 0})),
        ("Fresh timelines: confirmation tests", pct(confirmed, ["original_diff", "diff", "lo", "hi"]).round(4)),
        ("Fresh timelines: accuracy by category", pct(categories, cat_cols)),
        ("Hard-cap budget sweep: accuracy", pct(budget, acc_cols).round({"memory_tokens": 0})),
        ("Hard-cap budget sweep: LADL minus baseline", pct(budget_contrasts, ["diff", "lo", "hi"]).round(4)),
        ("Compaction placement: accuracy", pct(place, acc_cols).round({"memory_tokens": 0})),
        ("Compaction placement: LADL minus baseline", pct(place_contrasts, ["diff", "lo", "hi"]).round(4)),
    ]
    text = ["# Extended experiments (PACE-ICE, hard cap)\n"]
    for title, table in sections:
        text += [f"## {title}\n", table.to_markdown(index=False), ""]
    (out / "report.md").write_text("\n".join(text))

    print(pct(confirmed, ["original_diff", "diff", "lo", "hi"]).round(4).to_string(index=False))
    print(pct(fresh_acc, acc_cols)[["model", "condition", "n", "accuracy", "lo", "hi", "execute", "max_tokens"]].to_string(index=False))
    print(pct(budget, ["accuracy"]).pivot_table(index=["model", "condition"], columns="budget", values="accuracy").to_string())
    print(pct(budget_contrasts, ["diff"]).pivot_table(index=["model", "baseline"], columns="budget", values="diff").to_string())
    print(pct(place, ["accuracy"]).pivot_table(index=["model", "condition"], columns="placement", values="accuracy").to_string())
    print(pct(place_contrasts, ["diff"]).pivot_table(index=["model", "baseline"], columns="placement", values="diff").to_string())


if __name__ == "__main__":
    main()
