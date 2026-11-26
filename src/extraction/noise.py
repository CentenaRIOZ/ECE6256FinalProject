"""Gold events as a perfect extractor would write them, optionally with controlled extraction errors.

Used by experiment B in docs/followup_experiments_plan.md. Missed events drop gold events; false events are added on
user turns without gold events. The type mix and attribute rates of false events come from the false events of the
three extractors on the Test split (v1 and v2 pooled, 2,541 events), not from Confirm.

Every random choice comes from a generator seeded by (seed, dialogue, stream), so the output is the same in every
process, and levels are nested: the false events at precision 0.6 include those at 0.7, and the events dropped at
recall 0.7 include those dropped at 0.8.
"""
from __future__ import annotations

import hashlib
import math
import random
import re

from src.generation.content import TOOLS

FALSE_OPS = {"commit": 0.36, "ambiguous": 0.34, "approve": 0.11, "tool_result": 0.07, "prohibit": 0.06, "revoke": 0.05,
             "cancel": 0.01}
SAME_TOOL = 0.63         # a false commit or prohibition uses a tool of the dialogue's gold items
GUARDED_COMMIT = 0.21    # a false commit has a condition
EXPLICIT_APPROVE = 0.74  # a false approval is explicit
MATCHING_APPROVE = 0.42  # a false approval satisfies the condition
TOOL_SUCCESS = 0.26      # a false tool result reports success
NEEDS = {"ambiguous": None, "approve": "commitment", "tool_result": "commitment", "revoke": "prohibition",
         "cancel": "commitment"}  # item type a false event refers to (None: any item)


def _rng(seed: int, dialogue_id: str, stream: str) -> random.Random:
    digest = hashlib.sha256(f"{seed}:{dialogue_id}:{stream}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


# Only random() is used: its sequence is fixed for a given seed, while helpers such as sample() may change between
# Python versions.
def _pick(rng: random.Random, seq: list):
    return seq[int(rng.random() * len(seq))]


def _shuffled(rng: random.Random, seq: list) -> list:
    out = list(seq)
    for i in range(len(out) - 1, 0, -1):
        j = int(rng.random() * (i + 1))
        out[i], out[j] = out[j], out[i]
    return out


def _weighted(rng: random.Random, weights: dict) -> str:
    x, total = rng.random() * sum(weights.values()), 0.0
    for key, w in weights.items():
        total += w
        if x < total:
            return key
    return key


def parse_spec(spec: str) -> dict:
    """'precision=0.7,recall=1,seed=0' -> dict(precision=0.7, recall=1.0, seed=0)."""
    out = dict(precision=1.0, recall=1.0, seed=0)
    for part in filter(None, spec.split(",")):
        key, value = part.split("=", 1)
        assert key in out, f"unknown noise setting {key}"
        out[key] = int(value) if key == "seed" else float(value)
    assert 0 < out["precision"] <= 1 and 0 < out["recall"] <= 1, out
    return out


def _filled(ev: dict, items: dict) -> dict:
    """A gold event with the fields the extractor's registry adds: tool, target and, for commits, the guard."""
    it = items[ev["item"]]
    out = {k: v for k, v in ev.items() if k != "text"}
    out.update(tool=it["tool"], target=it["target"])
    if ev["op"] == "commit":
        out["guard"] = ev.get("guard")
    return out


def _false_events(dlg: dict, seed: int, n_max: int) -> list[tuple[int, dict]]:
    """A fixed sequence of false events; a setting uses a prefix of it."""
    rng = _rng(seed, dlg["dialogue_id"], "false")
    turns = [t["idx"] for t in dlg["turns"] if t["role"] in ("user", "tool") and not t["gold_events"]]
    if not turns:
        return []
    order = _shuffled(rng, turns)
    created = {}  # gold item -> turn of its first creating event
    for t in dlg["turns"]:
        for ev in t["gold_events"]:
            if ev["op"] in ("prohibit", "commit"):
                created.setdefault(ev["item"], t["idx"])
    gold_tools = sorted({it["tool"] for it in dlg["items"].values()})
    other_tools = sorted(set(TOOLS) - set(gold_tools)) or sorted(TOOLS)
    artifacts = sorted({it["artifact"] for it in dlg["items"].values()})
    out = []
    for i in range(n_max):
        turn = order[i % len(order)]
        op = _weighted(rng, FALSE_OPS)
        pool = sorted(k for k, t in created.items() if t < turn
                      and (NEEDS.get(op) is None or dlg["items"][k]["type"] == NEEDS[op]))
        if op in NEEDS and not pool:
            op = "commit"
        if op in ("commit", "prohibit"):
            tool = _pick(rng, gold_tools) if rng.random() < SAME_TOOL else _pick(rng, other_tools)
            words = re.findall(r"[A-Za-z0-9$']+", dlg["turns"][turn]["text"])[:6]
            ev = dict(op=op, item=f"X{i}", tool=tool, target="request=" + " ".join(words))
            if op == "commit":
                ev["guard"] = (f"user approves the final {_pick(rng, artifacts)}"
                               if rng.random() < GUARDED_COMMIT else None)
        else:
            item = _pick(rng, pool)
            ev = dict(op=op, item=item, tool=dlg["items"][item]["tool"], target=dlg["items"][item]["target"])
            if op == "approve":
                ev.update(object=f"the {dlg['items'][item]['artifact']}", explicit=rng.random() < EXPLICIT_APPROVE,
                          matches_guard=rng.random() < MATCHING_APPROVE)
            elif op == "tool_result":
                ev["success"] = rng.random() < TOOL_SUCCESS
        out.append((turn, ev))
    return out


def false_events(dlg: dict, precision: float = 1.0, recall: float = 1.0, seed: int = 0) -> list[tuple[int, dict]]:
    """The false events of one setting as (turn, event); events name gold items by their gold id, new items X<n>."""
    n_gold = sum(len(t["gold_events"]) for t in dlg["turns"])
    # Expected true positives are n_gold * recall, so this many false events gives expected precision p.
    x = n_gold * recall * (1 - precision) / precision
    u = _rng(seed, dlg["dialogue_id"], "count").random()
    n_false = math.floor(x) + (u < x - math.floor(x))
    n_max = 2 * n_gold + 4  # covers precision 0.4 at recall 1; fixed so that levels stay nested
    assert n_false <= n_max, (dlg["dialogue_id"], n_false, n_max)
    return _false_events(dlg, seed, n_max)[:n_false]


def noisy_gold_events(dlg: dict, precision: float = 1.0, recall: float = 1.0, seed: int = 0
                      ) -> tuple[list[list[dict]], dict]:
    """Per-turn events for one dialogue, and counts of what was changed."""
    gold = [[_filled(ev, dlg["items"]) for ev in t["gold_events"]] for t in dlg["turns"]]
    n_gold = sum(map(len, gold))
    drop = _rng(seed, dlg["dialogue_id"], "drop")
    kept = [[ev for ev in evs if drop.random() >= 1 - recall] for evs in gold]
    events = [list(evs) for evs in kept]
    added = false_events(dlg, precision, recall, seed)
    for turn, ev in added:
        events[turn].append(dict(ev))
    n_false = len(added)
    # Rename items I1, I2, ... in order of first appearance, as the extractor's registry does.
    names: dict[str, str] = {}
    for evs in events:
        for ev in evs:
            ev["item"] = names.setdefault(ev["item"], f"I{len(names) + 1}")
    counts = dict(gold=n_gold, dropped=n_gold - sum(map(len, kept)), false=n_false)
    return events, counts
