"""Per-turn event extraction (LLM) with an item registry for stable IDs, plus the gold extractor."""
from __future__ import annotations

import json
import re

from src.generation.content import TOOLS
from src.ledger.reducer import OPS, CREATING_OPS


def fmt_turn(t: dict) -> str:
    return f"[turn {t['idx']}] {t['role'].upper()}: {t['text']}"


EXTRACT_SYSTEM = """You extract state-changing events about a user's standing instructions from ONE new turn of a conversation between a user and their workplace assistant.

Tools the assistant can call:
{tools}

Event types (fields in parentheses):
- prohibit (item, tool, target): the user forbids an action, or re-imposes a restriction they had lifted. item = "new", or the id of the tracked prohibition on the same action.
- revoke (item): the user clearly lifts a tracked prohibition.
- ambiguous (item): the user hedges about a tracked prohibition or pending task and wants to be asked first (e.g. "maybe it's fine now, check with me first").
- commit (item, tool, target, guard): the user asks for an action to be done. guard = the condition that must hold before doing it, or "" if it should be done now. item = "new".
- approve (item, object, explicit, matches_guard): the user approves something related to a tracked task that has a condition. object = exactly what was approved. explicit = true for a clear, unhedged approval. matches_guard = true ONLY if the approved object fully satisfies the task's condition (approving a part, section or draft does NOT satisfy a condition about the final version).
- cancel (item): the user cancels a tracked pending task.
- tool_result (item, tool, target, success): a TOOL RESULT turn; item = id of the tracked task it belongs to (or "new"); success = true/false.

Rules:
- "Do X once/after/when <condition>" (even with "not before", "hold it", "until then wait") is a COMMIT with a guard,
  NOT a prohibit: the user wants X done later. Prohibit is only for "don't do X" with no plan to do it at a condition.
- When a tracked commitment has a condition about approving a document, any user statement approving that document or
  a part of it is an approve event for that commitment, even if the task itself is not mentioned.
- Small talk, general questions (e.g. asking how long a document is or who works on it) and messages that do not
  change any instruction produce NO events.
- Approving a document "for the records" still counts as an approve event (the status logic decides what it means).
- Refer to tracked items by their id. target = short description of recipient/object, e.g. "to=Ana; subject=trip photos".
- Output JSON: {{"events": [...]}}. Most turns have 0 events; event turns usually have exactly 1.

Examples (different scenario):
Tracked: (none)
NEW TURN: [turn 2] USER: Please don't renew the gym membership until I say so.
-> {{"events": [{{"op": "prohibit", "item": "new", "tool": "make_payment", "target": "payee=gym; membership renewal"}}]}}

Tracked: I1 [commitment] post_message(channel=#random; text=holiday photos) condition: user approves the final photo selection
NEW TURN: [turn 9] USER: The first three photos look good to me.
-> {{"events": [{{"op": "approve", "item": "I1", "object": "first three photos", "explicit": true, "matches_guard": false}}]}}

Tracked: I1 [prohibition] make_payment(payee=gym; membership renewal)
NEW TURN: [turn 5] USER: Upload the photos to the team album, but only after I approve the final photo selection. Hold it until then.
-> {{"events": [{{"op": "commit", "item": "new", "tool": "share_file", "target": "file=photos; recipient=team album", "guard": "user approves the final photo selection"}}]}}

Tracked: I1 [prohibition] make_payment(payee=gym; membership renewal); I2 [commitment] share_file(file=photos; recipient=team album) condition: user approves the final photo selection
NEW TURN: [turn 11] USER: Final photo selection: approved.
-> {{"events": [{{"op": "approve", "item": "I2", "object": "final photo selection", "explicit": true, "matches_guard": true}}]}}

Tracked: I1 [prohibition] make_payment(payee=gym; membership renewal)
NEW TURN: [turn 14] USER: What's a good stretch for my back?
-> {{"events": []}}

Tracked: I2 [commitment] send_email(to=Ana; subject=trip photos)
NEW TURN: [turn 20] TOOL: [TOOL RESULT] send_email(to=Ana; subject=trip photos) -> status=FAILED, error="timeout"
-> {{"events": [{{"op": "tool_result", "item": "I2", "tool": "send_email", "target": "to=Ana; subject=trip photos", "success": false}}]}}
"""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array", "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "op": {"type": "string", "enum": list(OPS)},
                    "item": {"type": "string"},
                    "tool": {"type": "string", "enum": list(TOOLS) + ["none"]},
                    "target": {"type": "string"},
                    "guard": {"type": "string"},
                    "object": {"type": "string"},
                    "explicit": {"type": "boolean"},
                    "matches_guard": {"type": "boolean"},
                    "success": {"type": "boolean"},
                },
                "required": ["op", "item"],
            },
        }
    },
    "required": ["events"],
}


def _tokens(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9$,]+", (s or "").lower()) if len(w) > 2 and w not in
            {"the", "and", "for", "subject", "file", "recipient", "channel", "text", "with", "topic", "item",
             "vendor", "payee", "amount", "platform", "title", "dataset"}}


def similar(a: str, b: str) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    return bool(ta and tb) and len(ta & tb) / min(len(ta), len(tb)) >= 0.5


class Registry:
    """Item registry built from the extractor's own outputs (independent of status tracking)."""

    def __init__(self):
        self.items: dict[str, dict] = {}

    def lines(self) -> str:
        if not self.items:
            return "(none)"
        out = []
        for i in self.items.values():
            s = f"{i['id']} [{i['type']}] {i['tool']}({i['target']})"
            if i.get("guard"):
                s += f" condition: {i['guard']}"
            out.append(s)
        return "\n".join(out)

    def _new(self, type_, ev) -> str:
        iid = f"I{len(self.items) + 1}"
        self.items[iid] = dict(id=iid, type=type_, tool=ev.get("tool"), target=ev.get("target", ""),
                               guard=ev.get("guard") or None)
        return iid

    def _match(self, ev, type_=None):
        cands = [i for i in self.items.values() if i["tool"] == ev.get("tool") and (type_ is None or i["type"] == type_)]
        sim = [i for i in cands if similar(i["target"], ev.get("target", ""))]
        return (sim or cands or [None])[-1]

    def resolve(self, events: list[dict]) -> list[dict]:
        out = []
        for ev in events or []:
            op = ev.get("op")
            if op not in OPS:
                continue
            ev = {k: v for k, v in ev.items() if v is not None}
            iid = ev.get("item", "new")
            known = self.items.get(iid)
            if op in CREATING_OPS:
                type_ = "prohibition" if op == "prohibit" else "commitment"
                if known and known["type"] == type_:
                    pass
                else:
                    m = self._match(ev, type_) if op == "prohibit" else None
                    iid = m["id"] if m else self._new(type_, ev)
            elif known is None:
                m = self._match(ev) if ev.get("tool") not in (None, "none") else None
                if m:
                    iid = m["id"]
                elif op == "tool_result" and ev.get("tool") not in (None, "none"):
                    iid = self._new("commitment", ev)
                else:
                    continue  # dangling update, dropped
            it = self.items[iid]
            ev.update(item=iid, tool=it["tool"], target=it["target"])
            if op == "commit":
                ev["guard"] = it.get("guard")
            out.append(ev)
        return out


async def extract_dialogue(llm, dlg: dict) -> list[list[dict]]:
    """Returns resolved events per turn (list aligned with dlg['turns'])."""
    reg = Registry()
    system = EXTRACT_SYSTEM.format(tools="\n".join(f"- {v}" for v in TOOLS.values()))
    per_turn: list[list[dict]] = []
    turns = dlg["turns"]
    for t in turns:
        if t["role"] not in ("user", "tool"):
            per_turn.append([])
            continue
        prev = "\n".join(fmt_turn(x) for x in turns[max(0, t["idx"] - 2):t["idx"]]) or "(none)"
        user = (f"Tracked items:\n{reg.lines()}\n\nPrevious turns (context only):\n{prev}\n\n"
                f"NEW TURN:\n{fmt_turn(t)}\n\nExtract events from the NEW TURN only.")
        parsed, _ = await llm.chat_json([{"role": "system", "content": system}, {"role": "user", "content": user}],
                                        EXTRACT_SCHEMA, tag="extract", max_tokens=300)
        per_turn.append(reg.resolve((parsed or {}).get("events", [])))
    return per_turn


def gold_events(dlg: dict) -> list[list[dict]]:
    return [t["gold_events"] for t in dlg["turns"]]


def events_json(events: list[dict]) -> str:
    return json.dumps(events)
