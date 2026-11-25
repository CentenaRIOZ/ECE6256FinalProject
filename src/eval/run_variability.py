"""Compare the planned Confirm tests across independent runs of the same experiment.

python -m src.eval.tagged_runs --tag=-rerun1 --out results/runs_rerun1
python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det
python -m src.eval.run_variability --run original=results/runs --run rerun=results/runs_rerun1 \
    --run deterministic=results/runs_det --out results/det/variability

Each --run names a folder that holds the Confirm runs under their standard names. The tests are the planned four-way
tests from confirm_report.py. A test is stable if every run reaches the same conclusion.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.eval.confirm_report import planned_tests

KEY = ["family", "model", "a", "b"]


def collect(runs: dict[str, Path]) -> tuple[pd.DataFrame, pd.DataFrame]:
    tests, accuracy = [], []
    for label, root in runs.items():
        t, df = planned_tests(root)
        t = t[(t.metric == "four_way") & t.planned].assign(run=label)
        tests.append(t[KEY + ["run", "diff", "lo", "hi", "p_holm", "confirmed"]])
        df = df.assign(correct=(df.pred_decision == df.gold_decision).astype(float))
        accuracy.append(df.groupby(["model", "condition"]).correct.mean().rename(label))
    return pd.concat(tests, ignore_index=True), pd.concat(accuracy, axis=1).reset_index()


def summarize(tests: pd.DataFrame, labels: list[str]) -> pd.DataFrame:
    wide = tests.pivot_table(index=KEY, columns="run", values=["diff", "confirmed"], aggfunc="first")
    out = pd.DataFrame(index=wide.index)
    for label in labels:
        out[f"diff_{label}"] = (wide[("diff", label)] * 100).round(1)
        out[f"confirmed_{label}"] = wide[("confirmed", label)].astype(bool)
    out["stable"] = out[[f"confirmed_{l}" for l in labels]].nunique(axis=1) == 1
    out["diff_range"] = (out[[f"diff_{l}" for l in labels]].max(axis=1) - out[[f"diff_{l}" for l in labels]].min(axis=1)).round(1)
    return out.reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="label=folder, in the order to report")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = {k: Path(v) for k, v in (item.split("=", 1) for item in a.run)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tests, accuracy = collect(runs)
    table = summarize(tests, list(runs))
    labels = list(runs)
    accuracy["range"] = accuracy[labels].max(axis=1) - accuracy[labels].min(axis=1)
    table.to_csv(out / "planned_tests_by_run.csv", index=False)
    accuracy.to_csv(out / "accuracy_by_run.csv", index=False)
    acc_view = accuracy.copy()
    acc_view[labels + ["range"]] = (acc_view[labels + ["range"]] * 100).round(1)
    text = ["# Run-to-run variability on Confirm", "",
            f"Runs: {', '.join(f'{k} ({v})' for k, v in runs.items())}. Four-way accuracy differences in points.", "",
            f"Planned tests with the same conclusion in every run: {int(table.stable.sum())} of {len(table)}.", "",
            "## Planned tests", "", table.to_markdown(index=False), "",
            "## Condition accuracy", "",
            f"Largest range across runs: {acc_view['range'].max():.1f} points.", "", acc_view.to_markdown(index=False), ""]
    (out / "report.md").write_text("\n".join(text))
    print("\n".join(text[:6]))
    print(table[~table.stable].to_string(index=False))


if __name__ == "__main__":
    main()
