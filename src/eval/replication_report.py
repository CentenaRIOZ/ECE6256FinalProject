"""Exploratory comparison of LADL and its strongest baselines across Test, Fresh, and Confirm.

python -m src.eval.replication_report --out results/confirm

The planned confirmation tests are in confirm_report.py. Everything here is descriptive. The best baseline is chosen
after seeing each dataset's accuracy, so its confidence intervals do not account for that selection.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.models import available
from src.eval.robustness import REPS, load

SOURCES = {
    "Test": ("-pace-hardcap", "-pace-replicate-test-hints", "-pace-replicate-test-v2"),
    "Fresh": ("-pace-fresh-spread", "-pace-replicate-fresh-hints", "-pace-replicate-fresh-v2"),
    "Confirm": ("-pace-confirm-v1", None, "-pace-confirm-v2"),
}
V1_BASELINES = ["summary", "summary_hint", "pinning", "pinning_hint", "chrono", "chrono_hint", "typed_llm"]
V2_BASELINES = ["summary", "summary_hint", "pinning", "pinning_hint", "chrono_v2", "chrono_hint_v2", "typed_llm_v2"]
FLOOR = 2 / (REPS + 1)


def read_dataset(root: Path, run: str, base: str, hints: str | None, v2: str) -> pd.DataFrame:
    frames = [load(str(root / f"{run}{base}"), 384)]
    if hints:
        frames.append(load(str(root / f"{run}{hints}"), 384))
    extracted = load(str(root / f"{run}{v2}"), 384)
    extracted["condition"] = extracted.condition + "_v2"
    return pd.concat(frames + [extracted], ignore_index=True)


def contrast(d: pd.DataFrame, dataset: str, model: str, kind: str, a: str, b: str) -> dict:
    diff, lo, hi, p = paired_diff(d, a, b, "accuracy", reps=REPS)
    return dict(dataset=dataset, model=model, kind=kind, a=a, b=b, diff=diff, lo=lo, hi=hi, p=max(p, FLOOR))


def analyze(d: pd.DataFrame, dataset: str, model: str) -> tuple[list[dict], list[dict]]:
    accuracy = {c: cluster_boot(x, "accuracy") for c, x in d.groupby("condition")}
    best_v1 = max(V1_BASELINES, key=lambda c: accuracy[c][0])
    best_v2 = max(V2_BASELINES, key=lambda c: accuracy[c][0])
    summary = [dict(dataset=dataset, model=model, extraction=name, ladl=accuracy[ladl][0], ladl_lo=accuracy[ladl][1],
                    ladl_hi=accuracy[ladl][2], best_baseline=best, best_accuracy=accuracy[best][0])
               for name, ladl, best in (("v1", "lifecycle", best_v1), ("v2", "lifecycle_v2", best_v2))]
    tests = [contrast(d, dataset, model, "extraction v2", "lifecycle_v2", "lifecycle"),
             contrast(d, dataset, model, "best baseline v1", "lifecycle", best_v1),
             contrast(d, dataset, model, "best baseline v2", "lifecycle_v2", best_v2),
             contrast(d, dataset, model, "no hints versus log v1", "lifecycle_nohint", "chrono"),
             contrast(d, dataset, model, "no hints versus log v2", "lifecycle_nohint_v2", "chrono_v2")]
    tests += [contrast(d, dataset, model, "LADL v2 versus baseline", "lifecycle_v2", b) for b in V2_BASELINES]
    return summary, tests


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/confirm")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    summaries, tests = [], []
    for dataset, (base, hints, v2) in SOURCES.items():
        for model, run in available(root, [s for s in (base, hints, v2) if s]).items():
            s, t = analyze(read_dataset(root, run, base, hints, v2), dataset, model)
            summaries += s
            tests += t
    summary, contrasts = pd.DataFrame(summaries), pd.DataFrame(tests)
    summary.to_csv(out / "replication_summary.csv", index=False)
    contrasts.to_csv(out / "replication_contrasts.csv", index=False)
    show_s = summary.copy()
    show_s[["ladl", "ladl_lo", "ladl_hi", "best_accuracy"]] = (show_s[["ladl", "ladl_lo", "ladl_hi", "best_accuracy"]] * 100).round(1)
    show_t = contrasts.copy()
    show_t[["diff", "lo", "hi"]] = (show_t[["diff", "lo", "hi"]] * 100).round(1)
    show_t["p"] = show_t.p.round(4)
    text = ["# Exploratory replication across datasets", "",
            "Best baselines are selected after seeing accuracy. P-values are uncorrected.", "",
            "## LADL and strongest baseline", "", show_s.to_markdown(index=False), "",
            "## Contrasts", "", show_t.to_markdown(index=False), ""]
    (out / "replication.md").write_text("\n".join(text))
    print(show_s.to_string(index=False))
    print(show_t[show_t.kind != "LADL v2 versus baseline"].to_string(index=False))
    print(show_t[show_t.kind == "LADL v2 versus baseline"].to_string(index=False))


if __name__ == "__main__":
    main()
