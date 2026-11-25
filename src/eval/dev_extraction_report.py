"""Compare extraction prompt versions on the dev split only.

python -m src.eval.dev_extraction_report --runs results/runs
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.eval.analyze import rate
from src.eval.error_analysis import guard_counts, read_jsonl
from src.eval.extraction_eval import evaluate

MODELS = {"Qwen": "qwen2.5-7b", "Llama": "llama3.1-8b"}
DATA = "data/dialogues/dialogues.jsonl"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    a = ap.parse_args()
    dialogues = {r["dialogue_id"]: r for r in read_jsonl(Path(DATA)) if r["split"] == "dev"}
    rows = []
    for label, run in MODELS.items():
        for version in ("v1", "v2"):
            path = Path(a.runs) / f"{run}-pace-dev-{version}"
            extracted = {r["dialogue_id"]: r["events"] for r in read_jsonl(path / "extractions.jsonl")}
            assert set(extracted) == set(dialogues)
            quality = evaluate(dialogues, [dict(dialogue_id=k, events=v) for k, v in extracted.items()])
            probes = pd.DataFrame(read_jsonl(path / "probes_B384.jsonl"))
            ladl = probes[probes.condition == "lifecycle"]
            guards = guard_counts(ladl)
            rows.append(dict(model=label, version=version, probes=len(ladl), extraction_f1=quality["f1"],
                             approve_f1=quality["per_op"].get("approve", {}).get("f1"),
                             ambiguous_f1=quality["per_op"].get("ambiguous", {}).get("f1"),
                             ladl_accuracy=rate(ladl, "accuracy"), guard_wait=guards["guard_wait"],
                             guard_clarify=guards["guard_clarify"], guard_unmet=guards["guard_unmet"],
                             non_explicit_flags=guards["guard_clarify_nonexplicit"]))
    print(pd.DataFrame(rows).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
