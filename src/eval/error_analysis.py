"""Error attribution and approval-extraction statistics for the PACE-ICE hard-cap runs.

python -m src.eval.error_analysis --out results/extended

Writes error_analysis.csv (shares as fractions) and error_analysis.md (shares as percentages).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.eval.analyze import attribute, rate
from src.eval.extraction_eval import evaluate

MODELS = {"Qwen2.5-7B-Instruct": ("Qwen", "qwen2.5-7b"), "Llama-3.1-8B-Instruct": ("Llama", "llama3.1-8b")}
SPLITS = {"Test": ("-pace-hardcap", "data/dialogues/dialogues.jsonl"),
          "Fresh": ("-pace-fresh-spread", "data/fresh/dialogues_spread.jsonl")}
BAD_EXTRACTION = "bad extraction"
WRONG_ACTION = "wrong action | correct state"
METRICS = [
    ("probes", "Probes per condition", "count"),
    ("state_recall_ordinary", "State recall, ordinary compaction", "share"),
    ("state_recall_ladl", "State recall, LADL", "share"),
    ("state_recall_gold", "State recall, LADL with gold events", "share"),
    ("extraction_f1", "Event extraction F1", "f1"),
    ("approve_f1", "Approval extraction F1", "f1"),
    ("ladl_bad_extraction", "LADL errors from bad extraction", "share"),
    ("ladl_wrong_action", "LADL errors despite correct state", "share"),
    ("strict_bad_extraction", "Strict hedging errors from bad extraction", "share"),
    ("strict_wrong_action", "Strict hedging errors despite correct state", "share"),
    ("gold_error_rate", "Decision error rate with gold events", "share"),
    ("gold_errors", "Decision errors with gold events", "count"),
    ("gold_unneeded_clarify", "Gold-event errors that ask for clarification", "count"),
    ("gold_withheld_action", "Gold-event errors that withhold a permitted action", "count"),
    ("gold_acted_when_not_allowed", "Gold-event errors that act when not allowed", "count"),
    ("guard_unmet", "LADL probes with an unmet guard", "count"),
    ("guard_wait", "Unmet guard: wait (correct)", "count"),
    ("guard_clarify", "Unmet guard: clarify", "count"),
    ("guard_decline", "Unmet guard: decline", "count"),
    ("guard_act", "Unmet guard: act", "count"),
    ("guard_clarify_unclear", "Unmet guard: clarify with ledger marked unclear", "count"),
    ("guard_clarify_nonexplicit", "Unmet guard: unclear flag from a non-explicit approval", "count"),
]


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f]


def attribution_shares(df: pd.DataFrame, condition: str, dialogues: dict, extracted: dict) -> pd.Series:
    rows = df[df.condition == condition]
    labels = [attribute(r, dialogues[r.dialogue_id], extracted[r.dialogue_id]) for _, r in rows.iterrows()]
    return pd.Series(labels).value_counts(normalize=True)


def guard_counts(ladl: pd.DataFrame) -> dict:
    guard = ladl[ladl.gold_reason == "guard_unmet"]
    clarify = guard[guard.pred_decision == "clarify"]
    unclear = clarify[clarify.ledger_item.map(lambda item: bool(item and item.get("unclear")))]
    nonexplicit = sum("non-explicit" in item["history"][-1][4] for item in unclear.ledger_item)
    return dict(guard_unmet=len(guard), guard_wait=int((guard.pred_decision == "wait").sum()),
                guard_clarify=len(clarify), guard_decline=int((guard.pred_decision == "decline").sum()),
                guard_act=int((guard.pred_decision == "act").sum()), guard_clarify_unclear=len(unclear),
                guard_clarify_nonexplicit=nonexplicit)


def gold_error_counts(df: pd.DataFrame) -> dict:
    gold = df[df.condition == "lifecycle_gold"]
    wrong = gold[gold.pred_decision != gold.gold_decision]
    return dict(gold_error_rate=len(wrong) / len(gold), gold_errors=len(wrong),
                gold_unneeded_clarify=int((wrong.pred_decision == "clarify").sum()),
                gold_withheld_action=int((wrong.gold_decision == "act").sum()),
                gold_acted_when_not_allowed=int((wrong.pred_decision == "act").sum()))


def analyze_run(split: str, model: str, run: str, suffix: str, dialogues: dict) -> dict:
    path = Path("results/runs") / f"{run}{suffix}"
    df = pd.DataFrame(read_jsonl(path / "probes_B384.jsonl"))
    extracted = {r["dialogue_id"]: r["events"] for r in read_jsonl(path / "extractions.jsonl")}
    quality = evaluate({k: dialogues[k] for k in extracted},
                       [dict(dialogue_id=k, events=v) for k, v in extracted.items()])
    ladl_att = attribution_shares(df, "lifecycle", dialogues, extracted)
    strict_att = attribution_shares(df, "lifecycle_strict", dialogues, extracted)
    return dict(split=split, model=model, probes=len(df[df.condition == "lifecycle"]),
                state_recall_ordinary=rate(df[df.condition == "summary"], "state_recall"),
                state_recall_ladl=rate(df[df.condition == "lifecycle"], "state_recall"),
                state_recall_gold=rate(df[df.condition == "lifecycle_gold"], "state_recall"),
                extraction_f1=quality["f1"], approve_f1=quality["per_op"]["approve"]["f1"],
                ladl_bad_extraction=ladl_att.get(BAD_EXTRACTION, 0.0), ladl_wrong_action=ladl_att.get(WRONG_ACTION, 0.0),
                strict_bad_extraction=strict_att.get(BAD_EXTRACTION, 0.0),
                strict_wrong_action=strict_att.get(WRONG_ACTION, 0.0),
                **gold_error_counts(df), **guard_counts(df[df.condition == "lifecycle"]))


def fmt(value: float, kind: str) -> str:
    return {"count": f"{int(value)}", "share": f"{value * 100:.1f}%", "f1": f"{value:.2f}"}[kind]


def markdown(table: pd.DataFrame) -> str:
    columns = [(s, m) for s in SPLITS for m in ("Qwen", "Llama")]
    indexed = table.set_index(["split", "model"])
    lines = ["# Error analysis (PACE-ICE, B=384, hard cap)", "",
             "Generated by `python -m src.eval.error_analysis --out results/extended`.", "",
             "| Metric | " + " | ".join(f"{m} {s}" for s, m in columns) + " |",
             "|---|" + "---:|" * len(columns)]
    for key, label, kind in METRICS:
        cells = [fmt(indexed.loc[column, key], kind) for column in columns]
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results/extended")
    a = ap.parse_args()
    rows = []
    for split, (suffix, data) in SPLITS.items():
        dialogues = {r["dialogue_id"]: r for r in read_jsonl(Path(data))}
        for _, (model, run) in MODELS.items():
            rows.append(analyze_run(split, model, run, suffix, dialogues))
    table = pd.DataFrame(rows)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    table.to_csv(out / "error_analysis.csv", index=False)
    text = markdown(table)
    (out / "error_analysis.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
