"""Sample real failure examples from the Confirm runs with a fixed random seed.

python -m src.eval.error_examples --out results/confirm/error_examples.md
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd

from src.eval.analyze import attribute
from src.eval.error_analysis import read_jsonl

MODELS = {"Qwen": "qwen2.5-7b", "Llama": "llama3.1-8b"}
DATA = "data/confirm/dialogues.jsonl"
SEED = 20261123
CATEGORIES = {
    "nonexplicit_approval": ("Partial approval extracted as non-explicit",
                             "The ledger asks for clarification because extraction marked a clear partial approval as non-explicit."),
    "other_extraction": ("Other extraction failure", "A wrong or missing extracted event leaves the ledger in the wrong state."),
    "gold_clarify": ("Unneeded clarification with gold state", "The ledger is correct, but the policy still asks the user."),
    "reducer_helps": ("Approval after cancellation: LADL correct, event-local hints wrong",
                      "The latest event is an approval, but the reducer keeps the cancelled task cancelled."),
    "ladl_loses": ("LADL wrong, chronological ledger correct", "A failure case for the proposed method."),
    "duplicate": ("Duplicate action after verified completion", "The policy acts even though the task already succeeded."),
}


def is_nonexplicit(item) -> bool:
    return bool(item and item.get("unclear") and item.get("history") and "non-explicit" in item["history"][-1][4])


def approved_after_cancel(events: list[list[dict]], tool: str, after_turn: int) -> bool:
    ops = [e["op"] for turn in events[:after_turn + 1] for e in turn if e.get("tool") == tool]
    return "cancel" in ops and "approve" in ops[ops.index("cancel") + 1:]


def category_ids(v1: pd.DataFrame, dialogues: dict, extracted: dict) -> dict[str, list[str]]:
    by = {c: d.set_index("probe_id") for c, d in v1.groupby("condition")}
    ladl, gold, chrono, hinted = by["lifecycle"], by["lifecycle_gold"], by["chrono"], by["chrono_hint"]
    ok = lambda d: d.pred_decision == d.gold_decision
    nonexplicit = ladl[(ladl.gold_reason == "guard_unmet") & (ladl.pred_decision == "clarify")
                       & ladl.ledger_item.map(is_nonexplicit)].index
    labels = pd.Series({pid: attribute(r, dialogues[r.dialogue_id], extracted[r.dialogue_id]) for pid, r in ladl.iterrows()})
    hint_wrong = ladl.index[ok(ladl) & ~ok(hinted.reindex(ladl.index)) & (ladl.gold_reason == "cancelled")]
    reducer_helps = [pid for pid in hint_wrong
                     if approved_after_cancel(extracted[ladl.loc[pid].dialogue_id], ladl.loc[pid].tool,
                                              int(ladl.loc[pid].after_turn))]
    return {
        "nonexplicit_approval": sorted(nonexplicit),
        "other_extraction": sorted(set(labels[labels == "bad extraction"].index) - set(nonexplicit)),
        "gold_clarify": sorted(gold[(gold.pred_decision == "clarify") & (gold.gold_decision != "clarify")].index),
        "reducer_helps": sorted(reducer_helps),
        "ladl_loses": sorted(ladl.index[~ok(ladl) & ok(chrono.reindex(ladl.index))]),
        "duplicate": sorted(ladl[(ladl.gold_reason == "completed") & (ladl.pred_decision == "act")].index),
    }


def dialogue_lines(dialogue: dict, probe: pd.Series) -> list[str]:
    lines = []
    for turn in dialogue["turns"][:int(probe.after_turn) + 1]:
        if turn.get("item") == probe["item"] and turn["kind"] in ("event", "tool"):
            lines.append(f"  - Turn {turn['idx']} ({turn['role']}): {turn['text']}")
    return lines


def extracted_lines(events: list[list[dict]], tool: str, after_turn: int) -> list[str]:
    lines = []
    for turn, turn_events in enumerate(events[:after_turn + 1]):
        for event in turn_events:
            if event.get("tool") == tool:
                keys = ("op", "object", "explicit", "matches_guard", "success")
                lines.append(f"  - Turn {turn}: " + ", ".join(f"{k}={event[k]}" for k in keys if k in event))
    return lines


def render(model: str, category: str, pid: str, frames: dict, dialogues: dict, extracted: dict, v2: pd.DataFrame) -> str:
    title, why = CATEGORIES[category]
    condition = {"gold_clarify": "lifecycle_gold"}.get(category, "lifecycle")
    probe = frames[condition].loc[pid]
    dialogue = dialogues[probe.dialogue_id]
    out = [f"### {title} ({model}, `{pid}`)", "", why, "",
           f"- Probe: {probe.text}", f"- Gold: `{probe.gold_decision}` ({probe.gold_reason}). Prediction: `{probe.pred_decision}`.",
           f"- Compactions before probe: {int(probe.compactions_before_probe)}", "- Dialogue evidence:"]
    out += dialogue_lines(dialogue, probe) or ["  - No item-specific event before this probe."]
    if condition == "lifecycle":
        out += ["- Extracted events:"] + (extracted_lines(extracted[probe.dialogue_id], probe.tool, int(probe.after_turn))
                                         or ["  - None for this tool."])
    item = probe.ledger_item
    if item:
        out.append(f"- Ledger state: `{item.get('status')}`, unclear={item.get('unclear')}, failed attempts={item.get('failed_attempts')}")
    if category == "reducer_helps":
        hinted = frames["chrono_hint"].loc[pid]
        out.append(f"- Chronological ledger with hints predicted `{hinted.pred_decision}`.")
    if category == "ladl_loses":
        out.append(f"- Chronological ledger predicted `{frames['chrono'].loc[pid].pred_decision}`.")
    if category == "nonexplicit_approval":
        rerun = v2[(v2.condition == "lifecycle") & (v2.probe_id == pid)]
        if len(rerun):
            out.append(f"- LADL with extraction v2 predicted `{rerun.iloc[0].pred_decision}`.")
    reason = " ".join(str(probe.pred_reason).split())
    out += [f"- Policy rationale: {reason[:300]}", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/confirm/error_examples.md")
    ap.add_argument("--per-category", type=int, default=1)
    a = ap.parse_args()
    dialogues = {r["dialogue_id"]: r for r in read_jsonl(Path(DATA))}
    rng = random.Random(SEED)
    counts, sections = [], []
    for model, run in MODELS.items():
        root = Path(a.runs)
        v1 = pd.DataFrame(read_jsonl(root / f"{run}-pace-confirm-v1" / "probes_B384.jsonl"))
        v2 = pd.DataFrame(read_jsonl(root / f"{run}-pace-confirm-v2" / "probes_B384.jsonl"))
        extracted = {r["dialogue_id"]: r["events"] for r in read_jsonl(root / f"{run}-pace-confirm-v1" / "extractions.jsonl")}
        frames = {c: d.set_index("probe_id") for c, d in v1.groupby("condition")}
        ids = category_ids(v1, dialogues, extracted)
        for category, pids in ids.items():
            counts.append(dict(model=model, category=CATEGORIES[category][0], probes=len(pids)))
            for pid in rng.sample(pids, min(a.per_category, len(pids))):
                sections.append(render(model, category, pid, frames, dialogues, extracted, v2))
    table = pd.DataFrame(counts).pivot(index="category", columns="model", values="probes").reset_index()
    table = table.rename(columns={"category": "Failure type"})[["Failure type", "Qwen", "Llama"]]
    text = ["# Real error examples from the Confirm set", "",
            f"Examples are sampled with random seed {SEED} from the 916 Confirm probes. Counts are numbers of probes.", "",
            table.to_markdown(index=False), "", *sections]
    Path(a.out).write_text("\n".join(text))
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
