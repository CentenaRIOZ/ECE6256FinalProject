"""Accuracy and extraction quality for all three models on Test, Fresh, and Confirm.

python -m src.eval.three_model_report --out results/confirm

Descriptive only. The planned Mistral tests are in confirm_report.py and follow docs/third_model_plan.md.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.eval.analyze import cluster_boot
from src.eval.error_analysis import attribution_shares, read_jsonl
from src.eval.extraction_eval import evaluate
from src.eval.models import available
from src.eval.replication_report import read_dataset
from src.eval.robustness import binary

DATASETS = {
    "Test": ("-pace-hardcap", "-pace-replicate-test-hints", "-pace-replicate-test-v2", "data/dialogues/dialogues.jsonl"),
    "Fresh": ("-pace-fresh-spread", "-pace-replicate-fresh-hints", "-pace-replicate-fresh-v2",
              "data/fresh/dialogues_spread.jsonl"),
    "Confirm": ("-pace-confirm-v1", None, "-pace-confirm-v2", "data/confirm/dialogues.jsonl"),
}
CONDITIONS = {
    "full": "Full history (no compaction)",
    "summary": "Ordinary compaction",
    "summary_hint": "Ordinary compaction + hints",
    "pinning": "Constraint pinning",
    "pinning_hint": "Pinning + hints",
    "chrono_v2": "Chronological ledger",
    "chrono_hint_v2": "Chronological ledger + hints",
    "typed_llm_v2": "Typed ledger, LLM transitions",
    "lifecycle": "LADL, extraction v1",
    "lifecycle_v2": "LADL, extraction v2",
    "lifecycle_nohint_v2": "LADL v2 without hints",
    "lifecycle_strict_v2": "LADL v2, strict hedging",
    "lifecycle_gold": "LADL, gold events",
}
BASELINES = ["summary", "summary_hint", "pinning", "pinning_hint", "chrono_v2", "chrono_hint_v2", "typed_llm_v2"]


def accuracy(root: Path) -> pd.DataFrame:
    rows = []
    for dataset, (base, hints, v2, _) in DATASETS.items():
        for model, run in available(root, [s for s in (base, hints, v2) if s]).items():
            d = read_dataset(root, run, base, hints, v2)
            for condition in CONDITIONS:
                sub = d[d.condition == condition]
                acc, lo, hi = cluster_boot(sub, "accuracy")
                rows.append(dict(dataset=dataset, model=model, condition=condition, n=len(sub), accuracy=acc, lo=lo, hi=hi,
                                 execute=cluster_boot(binary(sub), "accuracy")[0],
                                 invalid=(sub.pred_decision == "invalid").mean()))
    return pd.DataFrame(rows)


def extraction(root: Path) -> pd.DataFrame:
    rows = []
    for dataset, (base, _, v2, data) in DATASETS.items():
        dialogues = {r["dialogue_id"]: r for r in read_jsonl(Path(data))}
        for model, run in available(root, [base, v2]).items():
            for version, suffix, condition in (("v1", base, "lifecycle"), ("v2", v2, "lifecycle")):
                path = root / f"{run}{suffix}"
                extracted = {r["dialogue_id"]: r["events"] for r in read_jsonl(path / "extractions.jsonl")}
                quality = evaluate({k: dialogues[k] for k in extracted},
                                   [dict(dialogue_id=k, events=v) for k, v in extracted.items()])
                probes = pd.DataFrame(read_jsonl(path / "probes_B384.jsonl"))
                shares = attribution_shares(probes, condition, dialogues, extracted)
                rows.append(dict(dataset=dataset, model=model, extraction=version, f1=quality["f1"],
                                 approve_f1=quality["per_op"]["approve"]["f1"],
                                 ladl_bad_extraction=shares.get("bad extraction", 0.0),
                                 ladl_wrong_action=shares.get("wrong action | correct state", 0.0)))
    return pd.DataFrame(rows)


def wide(acc: pd.DataFrame) -> pd.DataFrame:
    acc = acc.assign(column=acc.model + " " + acc.dataset, value=(acc.accuracy * 100).round(1))
    columns = [f"{m} {d}" for m in acc.model.unique() for d in DATASETS if f"{m} {d}" in set(acc.column)]
    table = acc.pivot(index="condition", columns="column", values="value").reindex(list(CONDITIONS))[columns]
    best = acc[acc.condition.isin(BASELINES)].groupby("column").value.max()
    table.loc["Best baseline"] = best[columns]
    table.index = [CONDITIONS.get(c, c) for c in table.index]
    return table.reset_index(names="Condition")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/confirm")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    acc, ext = accuracy(root), extraction(root)
    acc.to_csv(out / "three_model_accuracy.csv", index=False)
    ext.to_csv(out / "three_model_extraction.csv", index=False)
    ext_view = ext.copy()
    ext_view[["ladl_bad_extraction", "ladl_wrong_action"]] = (ext_view[["ladl_bad_extraction", "ladl_wrong_action"]] * 100).round(1)
    ext_view[["f1", "approve_f1"]] = ext_view[["f1", "approve_f1"]].round(3)
    invalid = acc.groupby(["dataset", "model"]).invalid.max().mul(100).round(2).reset_index()
    text = ["# Three-model accuracy and extraction", "",
            "Four-way accuracy (%) under the hard cap at B=384. Baselines that use extraction use v2. "
            "`Best baseline` is the highest of the seven compacted baselines and is chosen after seeing results.", "",
            wide(acc).to_markdown(index=False), "",
            "## Extraction quality and LADL error attribution", "",
            "`ladl_bad_extraction` and `ladl_wrong_action` are shares of all LADL probes.", "",
            ext_view.to_markdown(index=False), "",
            "## Largest share of invalid policy outputs in any condition (%)", "",
            invalid.to_markdown(index=False), ""]
    (out / "three_model.md").write_text("\n".join(text))
    print("\n".join(text))


if __name__ == "__main__":
    main()
