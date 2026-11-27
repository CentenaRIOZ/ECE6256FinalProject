"""Real failure examples for the paper's error analysis, from the deterministic Confirm and forged-update runs.

python -m src.eval.failure_examples --runs results/runs_det --out results/paper_examples/failure_examples.md

LADL means extraction v2 (`lifecycle_v2`), as in the paper tables. For every model it counts the probes in each failure
category and samples examples with a fixed seed. Each example shows the item's dialogue turns, the gold and extracted
events, the ledger state, and the policy's own account of the
instructions and the current status. The output holds model outputs, so it stays under results/.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd

from src.eval.analyze import attribute
from src.eval.error_analysis import read_jsonl
from src.eval.scale_report import ALL, CONFIRM, FORGED, clean_frame

SEED = 20261128
LADL = "lifecycle_v2"
CATEGORIES = {
    "ladl_loses_to_bm25": ("LADL wrong, BM25 retrieval right",
                           "The strongest baseline gets the decision right and the proposed method does not."),
    "ladl_beats_bm25": ("LADL right, BM25 retrieval wrong", "Where tracking state helps over retrieving turns."),
    "bad_extraction": ("LADL wrong: bad extraction",
                       "The extracted events for the item differ from the gold events, so the ledger state is wrong."),
    "bad_transition": ("LADL wrong: bad transition", "The extracted events are right, but the ledger state is wrong."),
    "lost_state": ("LADL wrong: ledger state lost", "The item was dropped from the ledger at the memory budget."),
    "correct_state": ("LADL wrong despite correct state", "The ledger state is right, but the policy decides wrongly."),
    "gold_wrong": ("LADL with gold events wrong", "Decision errors that remain with perfect extraction."),
    "forged_ladl": ("Forged update: LADL acts", "A forged teammate message makes LADL act against the user's standing instruction."),
    "forged_source": ("Forged update: LADL with speaker check still acts",
                      "The speaker check drops events from non-user turns except tool results, yet the model still acts."),
}
ATTRIBUTE = {"bad extraction": "bad_extraction", "bad transition": "bad_transition", "lost ledger state": "lost_state",
             "wrong action | correct state": "correct_state"}


def raw(root: Path, run: str, condition: str) -> dict[str, dict]:
    return {r["probe_id"]: r for r in read_jsonl(root / run / "probes_B384.jsonl") if r["condition"] == condition}


def event_text(ev: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in ev.items() if k not in ("item", "tool") and v not in (None, ""))


def evidence(dialogue: dict, probe: dict, extracted: list | None) -> list[str]:
    item = dialogue["items"][probe["item"]]
    out = ["- Dialogue turns for this item:"]
    for turn in dialogue["turns"][:int(probe["after_turn"]) + 1]:
        if turn.get("item") == probe["item"] and turn["kind"] in ("event", "tool", "forged"):
            out.append(f"  - Turn {turn['idx']} ({turn['role']}, {turn['kind']}): {turn['text']}")
    gold = [(t["idx"], e) for t in dialogue["turns"][:int(probe["after_turn"]) + 1] for e in t["gold_events"]
            if e["item"] == probe["item"]]
    out.append("- Gold events: " + ("; ".join(f"t{i} {event_text(e)}" for i, e in gold) or "none"))
    if extracted is not None:
        pred = [(i, e) for i, evs in enumerate(extracted[:int(probe["after_turn"]) + 1]) for e in evs
                if e.get("tool") == item["tool"]]
        out.append("- Extracted events (v2): " + ("; ".join(f"t{i} {event_text(e)}" for i, e in pred) or "none"))
    return out


def render(label: str, category: str, pid: str, ctx: dict) -> str:
    title, why = CATEGORIES[category]
    forged = category.startswith("forged")
    cond = {"gold_wrong": "lifecycle_gold", "forged_source": "lifecycle_source"}.get(category, "lifecycle")
    probe = (ctx["forged_raw"] if forged else ctx["gold_raw"] if cond == "lifecycle_gold" else ctx["ladl_raw"])[cond][pid]
    dialogue = (ctx["forged_dialogues"] if forged else ctx["dialogues"])[probe["dialogue_id"]]
    out = [f"### {title} ({label}, `{pid}`)", "", why, "", f"- Decision request ({probe['kind']}): {probe['text']}",
           f"- Gold: `{probe['gold_decision']}` ({probe['gold_reason']}). Prediction: `{probe['pred_decision']}`.",
           f"- Compactions before the request: {int(probe['compactions_before_probe'])}"]
    if not forged:
        preds = ctx["preds"].get(pid, {})
        out.append("- Other conditions: " + ", ".join(f"{name} `{preds[c]}`" for c, name in
                                                     (("summary", "compaction"), ("retrieval", "BM25"),
                                                      (LADL, "LADL"), ("lifecycle_gold", "gold events")) if c in preds))
    out += evidence(dialogue, probe, None if forged or cond == "lifecycle_gold" else ctx["extracted"].get(probe["dialogue_id"]))
    item = probe.get("ledger_item")
    if item:
        out.append(f"- Ledger state: `{item.get('status')}`, unclear={item.get('unclear')}, "
                   f"failed attempts={item.get('failed_attempts')}")
    reason = " ".join(str(probe["pred_reason"]).split())
    return "\n".join(out + [f"- Policy output, `user_instructions || current_status`: {reason[:400]}", ""])


def categorize(clean: pd.DataFrame, ctx: dict) -> dict[str, list[str]]:
    by = {c: d.set_index("probe_id") for c, d in clean.groupby("condition")}
    ladl, bm25, gold = by[LADL], by["retrieval"], by["lifecycle_gold"]
    ok = lambda d: d.pred_decision == d.gold_decision
    bm25 = bm25.reindex(ladl.index)
    ids = {"ladl_loses_to_bm25": sorted(ladl.index[~ok(ladl) & ok(bm25)]),
           "ladl_beats_bm25": sorted(ladl.index[ok(ladl) & ~ok(bm25)])}
    labels = pd.Series({pid: attribute(r, ctx["dialogues"][r.dialogue_id], ctx["extracted"].get(r.dialogue_id))
                        for pid, r in ladl.iterrows()})
    for label, key in ATTRIBUTE.items():
        ids[key] = sorted(labels.index[labels == label])
    ids["gold_wrong"] = sorted(gold.index[~ok(gold)])
    for key, cond in (("forged_ladl", "lifecycle"), ("forged_source", "lifecycle_source")):
        rows = ctx["forged_raw"].get(cond, {})
        ids[key] = sorted(p for p, r in rows.items() if p in ctx["attacked"] and r["pred_decision"] == "act"
                          and r["gold_decision"] != "act")
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_det")
    ap.add_argument("--out", default="results/paper_examples/failure_examples.md")
    ap.add_argument("--per-category", type=int, default=1, help="examples per category and model")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(CONFIRM))}
    forged_dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(FORGED))}
    attacked = {p for d in forged_dialogues.values() if d["forged"] for p in d["forged"]["attacked_probes"]}
    rng = random.Random(SEED)
    counts, sections = [], {k: [] for k in CATEGORIES}
    for label, run in ALL.items():
        clean = clean_frame(root, label)
        if clean is None:
            continue
        ctx = dict(dialogues=dialogues, forged_dialogues=forged_dialogues, attacked=attacked,
                   ladl_raw={"lifecycle": raw(root, f"{run}-pace-confirm-v2", "lifecycle")},
                   gold_raw={"lifecycle_gold": raw(root, f"{run}-pace-confirm-v1", "lifecycle_gold")},
                   extracted={r["dialogue_id"]: r["events"]
                              for r in read_jsonl(root / f"{run}-pace-confirm-v2" / "extractions.jsonl")},
                   forged_raw={c: raw(root, f"{run}-pace-forged-v2", c) for c in ("lifecycle", "lifecycle_source")}
                   if (root / f"{run}-pace-forged-v2" / "probes_B384.jsonl").exists() else {},
                   preds=clean.pivot(index="probe_id", columns="condition", values="pred_decision").to_dict("index"))
        ids = categorize(clean, ctx)
        for key, pids in ids.items():
            counts.append(dict(model=label, category=CATEGORIES[key][0], probes=len(pids)))
            for pid in rng.sample(pids, min(a.per_category, len(pids))):
                sections[key].append(render(label, key, pid, ctx))
    table = pd.DataFrame(counts).pivot(index="category", columns="model", values="probes")
    table = table.reindex([v[0] for v in CATEGORIES.values()])[[m for m in ALL if m in table.columns]]
    text = ["# Failure examples for the error analysis", "",
            f"Confirm set (916 decision requests per condition) and the forged-update set (200 attacked requests), "
            f"deterministic runs. LADL uses extraction v2. Examples are sampled with seed {SEED}. Counts are numbers "
            f"of decision requests; the first two rows compare LADL with BM25 retrieval, the next four split LADL's errors "
            f"by cause, and the forged rows count attacked requests where the model acted although gold says not to.", "",
            table.reset_index().rename(columns={"category": "Category"}).to_markdown(index=False), ""]
    for key, (title, _) in CATEGORIES.items():
        text += [f"## {title}", ""] + (sections[key] or ["No cases.", ""])
    out.write_text("\n".join(text))
    print(table.to_string())


if __name__ == "__main__":
    main()
