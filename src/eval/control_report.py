"""Compare the original runs with the PACE reruns, with and without the hard memory cap and ledger action hints.

python -m src.eval.control_report --budget 384 --out results/controls
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.robustness import REPS, binary, holm, load, paired_table, rq1_table

MODELS = {"Qwen2.5-7B-Instruct": "qwen2.5-7b", "Llama-3.1-8B-Instruct": "llama3.1-8b"}
CONDITIONS = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_nohint", "lifecycle_gold",
              "abl_noguard", "abl_noreceipt", "lifecycle_strict"]
HINT_PAIRS = [("lifecycle", "lifecycle_nohint"), ("lifecycle_nohint", "summary"), ("lifecycle_nohint", "pinning"),
              ("lifecycle_nohint", "chrono"), ("lifecycle_nohint", "typed_llm")]
FLOOR = 2 / (REPS + 1)


def accuracy_table(runs: dict[str, pd.DataFrame], budget: int) -> pd.DataFrame:
    rows = []
    for variant, df in runs.items():
        for (model, cond), d in df.groupby(["model", "condition"]):
            acc, lo, hi = cluster_boot(d, "accuracy")
            ex, ex_lo, ex_hi = cluster_boot(binary(d), "accuracy")
            compacted = d[d.compactions_before_probe > 0]
            rows.append(dict(variant=variant, model=model, condition=cond, accuracy=acc, lo=lo, hi=hi, execute=ex,
                             execute_lo=ex_lo, execute_hi=ex_hi, memory_tokens=compacted.memory_tokens.mean(),
                             over_budget=(compacted.memory_tokens > budget).mean(),
                             invalid=(d.pred_decision == "invalid").mean()))
    return pd.DataFrame(rows)


def hint_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for metric, frame in (("four_way", df), ("execute", binary(df))):
        family = []
        for model, d in frame.groupby("model"):
            for a, b in HINT_PAIRS:
                diff, lo, hi, p = paired_diff(d, a, b, "accuracy", reps=REPS)
                family.append(dict(metric=metric, model=model, a=a, b=b, diff=diff, lo=lo, hi=hi, p=max(p, FLOOR)))
        for r, adj in zip(family, holm(np.array([x["p"] for x in family]))):
            rows.append({**r, "p_holm": adj})
    return pd.DataFrame(rows)


def cap_effect(nocap: pd.DataFrame, hardcap: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODELS:
        for cond in CONDITIONS[1:]:
            a = hardcap[(hardcap.model == model) & (hardcap.condition == cond)].assign(condition="hard")
            b = nocap[(nocap.model == model) & (nocap.condition == cond)].assign(condition="none")
            diff, lo, hi, p = paired_diff(pd.concat([a, b]), "hard", "none", "accuracy", reps=REPS)
            rows.append(dict(model=model, condition=cond, diff=diff, lo=lo, hi=hi, p=max(p, FLOOR)))
    return pd.DataFrame(rows)


def replication(original: pd.DataFrame, nocap: pd.DataFrame) -> pd.DataFrame:
    keys = ["model", "condition", "probe_id"]
    merged = original[keys + ["pred_decision", "gold_decision"]].merge(nocap[keys + ["pred_decision"]], on=keys,
                                                                     suffixes=("_orig", "_pace"))
    merged["same"] = merged.pred_decision_orig == merged.pred_decision_pace
    merged["ok_orig"] = merged.pred_decision_orig == merged.gold_decision
    merged["ok_pace"] = merged.pred_decision_pace == merged.gold_decision
    out = merged.groupby(["model", "condition"])[["same", "ok_orig", "ok_pace"]].mean().reset_index()
    return out.rename(columns=dict(same="same_decision", ok_orig="accuracy_original", ok_pace="accuracy_pace"))


def pct(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = frame.copy()
    out[columns] = (out[columns] * 100).round(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--out", default="results/controls")
    ap.add_argument("--runs", default="results/runs")
    a = ap.parse_args()
    root = Path(a.runs)
    read = lambda suffix: pd.concat([load(str(root / f"{r}{suffix}"), a.budget) for r in MODELS.values()],
                                    ignore_index=True)
    original = pd.concat([read(""), read("-strict")], ignore_index=True)
    nocap, hardcap = read("-pace-nocap"), read("-pace-hardcap")

    accuracy = accuracy_table({"original": original, "pace_nocap": nocap, "pace_hardcap": hardcap}, a.budget)
    main_tests = paired_table(hardcap)
    nocap_tests = paired_table(nocap)
    hints = hint_table(hardcap)
    caps = cap_effect(nocap, hardcap)
    repl = replication(original, nocap)
    rq1 = rq1_table(hardcap)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tables = dict(accuracy=accuracy, paired_hardcap=main_tests, paired_nocap=nocap_tests, hint_control=hints,
                  cap_effect=caps, replication=repl, rq1_hardcap=rq1)
    for name, table in tables.items():
        table.to_csv(out / f"{name}_B{a.budget}.csv", index=False)

    acc_cols = ["accuracy", "lo", "hi", "execute", "execute_lo", "execute_hi", "over_budget", "invalid"]
    sections = [
        ("Accuracy", pct(accuracy, acc_cols).round({"memory_tokens": 0})),
        ("LADL minus baselines, hard cap (Holm within metric)", pct(main_tests, ["diff", "lo", "hi"]).round(4)),
        ("LADL minus baselines, PACE without cap (Holm within metric)", pct(nocap_tests, ["diff", "lo", "hi"]).round(4)),
        ("Ledger action-hint control, hard cap (Holm within metric)", pct(hints, ["diff", "lo", "hi"]).round(4)),
        ("Hard cap minus no cap", pct(caps, ["diff", "lo", "hi"]).round(4)),
        ("Original run versus PACE rerun without cap",
         pct(repl, ["same_decision", "accuracy_original", "accuracy_pace"])),
    ]
    text = [f"# Control experiments (B={a.budget}, test split)\n"]
    for title, table in sections:
        text += [f"## {title}\n", table.to_markdown(index=False), ""]
    (out / f"report_B{a.budget}.md").write_text("\n".join(text))

    view = accuracy.pivot_table(index=["model", "condition"], columns="variant", values=["accuracy", "execute"]) * 100
    print(view.round(1).to_string())
    for title, table in sections[1:5]:
        print(f"\n{title}\n{table.to_string(index=False)}")
    print("\nReplication\n", pct(repl, ["same_decision", "accuracy_original", "accuracy_pace"]).to_string(index=False))
    print("\nOver budget / tokens (hard cap)\n", pct(accuracy[accuracy.variant == "pace_hardcap"], ["over_budget"])
          [["model", "condition", "memory_tokens", "over_budget"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()
