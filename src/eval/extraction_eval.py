"""Turn-level extraction quality vs. gold events (item alignment by tool; op + key flags must match)."""
from __future__ import annotations

import argparse
import collections
import json


def ev_key(ev: dict, tool: str | None) -> tuple:
    op = ev["op"]
    k = (op, tool)
    if op == "approve":
        k += (bool(ev.get("explicit", True)), bool(ev.get("matches_guard", True)))
    if op == "tool_result":
        k += (bool(ev.get("success")),)
    if op == "commit":
        k += (bool(ev.get("guard")),)
    return k


def evaluate(dialogues: dict, extractions: list[dict]) -> dict:
    tp = fp = fn = 0
    per_op = collections.defaultdict(lambda: [0, 0, 0])
    errors = collections.Counter()
    for ex in extractions:
        d = dialogues[ex["dialogue_id"]]
        for t, pred in zip(d["turns"], ex["events"]):
            gold = collections.Counter(ev_key(e, d["items"][e["item"]]["tool"]) for e in t["gold_events"])
            pk = collections.Counter(ev_key(e, e.get("tool")) for e in pred)
            for k in gold | pk:
                m = min(gold[k], pk[k])
                tp += m
                fp += pk[k] - m
                fn += gold[k] - m
                per_op[k[0]][0] += m
                per_op[k[0]][1] += pk[k] - m
                per_op[k[0]][2] += gold[k] - m
            if gold != pk:
                errors[(t["kind"], tuple(sorted(k[0] for k in gold.elements())),
                        tuple(sorted(k[0] for k in pk.elements())))] += 1
    f1 = lambda a, b, c: 2 * a / max(1, 2 * a + b + c)
    return dict(precision=tp / max(1, tp + fp), recall=tp / max(1, tp + fn), f1=f1(tp, fp, fn),
                per_op={k: dict(tp=v[0], fp=v[1], fn=v[2], f1=round(f1(*v), 3)) for k, v in per_op.items()},
                top_errors=[(list(k), n) for k, n in errors.most_common(12)])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dialogues/dialogues.jsonl")
    ap.add_argument("--extractions", required=True)
    a = ap.parse_args()
    ds = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open(a.data)}
    ex = [json.loads(l) for l in open(a.extractions)]
    print(json.dumps(evaluate(ds, ex), indent=1))


if __name__ == "__main__":
    main()
