"""Memory conditions under repeated compaction (matched memory budget B tokens).

full            full history, no compaction (diagnostic upper reference)
summary         ordinary task-focused compaction (recursive summary)
pinning         summary + LLM-maintained pinned-constraints text, updated after every user/tool turn
chrono          summary + chronological event log (extracted events, no states)
typed_llm       summary + typed ledger whose statuses are written by the LLM
lifecycle       summary + typed ledger with deterministic lifecycle reducer (ours)
lifecycle_gold  same, from gold events (gold-state intervention / extraction upper bound)
abl_noguard     lifecycle without guard logic (any approval triggers)
abl_noreceipt   lifecycle without tool-success evidence (any attempt completes)
lifecycle_strict  POST-HOC variant: hedges only from explicit `ambiguous` events (not from approval flags)
lifecycle_nohint  lifecycle state rendered without action directives such as "do NOT perform"
summary_hint    ordinary compaction whose summary records status and permitted action
pinning_hint    pinning whose rules record status and permitted action
chrono_hint     chronological log whose events carry their own action implication, without a reducer

With hard_cap=True, the summary is shortened whenever summary + persistent block would exceed B tokens.
"""
from __future__ import annotations

import json

from src.extraction.extractor import fmt_turn
from src.ledger.reducer import Reducer, ReducerConfig, render_item, status_label

CONDITIONS = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_gold",
              "abl_noguard", "abl_noreceipt", "lifecycle_strict", "lifecycle_nohint", "summary_hint", "pinning_hint",
              "chrono_hint"]
REDUCER_CONDS = {"lifecycle": ReducerConfig(), "lifecycle_gold": ReducerConfig(),
                 "abl_noguard": ReducerConfig(guard_logic=False), "abl_noreceipt": ReducerConfig(receipt_logic=False),
                 "lifecycle_strict": ReducerConfig(hedge_from_flags=False), "lifecycle_nohint": ReducerConfig()}
LEDGER_CONDS = set(REDUCER_CONDS) | {"typed_llm"}
PIN_CONDS = {"pinning", "pinning_hint"}
CHRONO_CONDS = {"chrono", "chrono_hint"}

SUMMARY_SYSTEM = ("You compress a conversation between a user and their workplace assistant so the assistant can continue "
                  "working without the original messages. Write a concise, task-focused summary: keep the user's "
                  "instructions, decisions, pending tasks and action outcomes that matter for what the assistant should "
                  "do next; drop small talk. Plain text, at most {words} words.")
PIN_SYSTEM = ("You maintain a PINNED RULES list for a workplace assistant: the user's standing prohibitions and permissions, "
              "conditions attached to pending tasks, and task outcomes that affect what the assistant may do next. Given the "
              "current list and ONE new conversation turn, output the updated list: add new rules, and edit or remove "
              "rules the user changed (lifted prohibitions, cancelled tasks, completed or failed actions, approvals). Keep "
              "each rule one short line. If nothing changes, return the list unchanged. Output only the list, at most "
              "{words} words.")
ACTION_GUIDANCE = ("For every instruction or task that still matters, state its current status and what the assistant may "
                   "do, using these phrases: ACTIVE - do NOT perform; REVOKED - restriction lifted, action allowed; WAITING - "
                   "condition not yet met; READY - condition met / requested, not yet done: perform when asked; COMPLETED - "
                   "verified success, do NOT repeat; CANCELLED - do NOT perform; UNCLEAR - ask the user before acting; FAILED - "
                   "still pending.")
SUMMARY_HINT_SYSTEM = SUMMARY_SYSTEM.replace("Plain text,", ACTION_GUIDANCE + " Plain text,")
PIN_HINT_SYSTEM = PIN_SYSTEM.replace("If nothing changes,", ACTION_GUIDANCE + " If nothing changes,")
TRANSITION_SYSTEM = """You maintain a typed state ledger of a user's prohibitions and commitments for a workplace assistant.
Statuses: prohibition -> active | revoked. commitment -> waiting (its condition is not yet met) | ready (requested or condition met, not yet successfully done) | completed (verified success) | cancelled.
Also: unclear (true if the latest relevant user statement was ambiguous and the assistant must ask before acting) and failed_attempts (number of failed tool attempts).
Given the current ledger and newly extracted events from one turn, output the updated status of EVERY item as JSON {"items": [{"id", "status", "unclear", "failed_attempts"}]}."""
TRANSITION_SCHEMA = {
    "type": "object",
    "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"},
        "status": {"type": "string", "enum": ["active", "revoked", "waiting", "ready", "completed", "cancelled"]},
        "unclear": {"type": "boolean"}, "failed_attempts": {"type": "integer"}},
        "required": ["id", "status", "unclear", "failed_attempts"]}}},
    "required": ["items"],
}


def event_hint(ev: dict) -> str:
    """Action implication of one event, read without any accumulated item state."""
    op = ev["op"]
    if op == "prohibit":
        return "ACTIVE - do NOT perform"
    if op == "revoke":
        return "REVOKED - restriction lifted, action allowed"
    if op == "ambiguous":
        return "UNCLEAR - ask the user before acting"
    if op == "commit":
        return "WAITING - condition not yet met" if ev.get("guard") else "READY - requested, not yet done: perform when asked"
    if op == "approve":
        if not ev.get("explicit", True):
            return "UNCLEAR - ask the user before acting"
        return ("READY - condition met, not yet done: perform when asked" if ev.get("matches_guard")
                else "WAITING - condition not yet met")
    if op == "cancel":
        return "CANCELLED - do NOT perform"
    if op == "tool_result":
        return "COMPLETED - verified success, do NOT repeat" if ev.get("success") else "FAILED - still pending"
    return ""


def chrono_line(t: int, ev: dict, hints: bool = False) -> str:
    line = _chrono_text(t, ev)
    return f"{line} => {event_hint(ev)}" if hints else line


def _chrono_text(t: int, ev: dict) -> str:
    a = f"[{ev['item']}] {ev.get('tool')}({ev.get('target', '')})"
    op = ev["op"]
    if op == "prohibit":
        return f"t{t}: user PROHIBITED {a}"
    if op == "revoke":
        return f"t{t}: user LIFTED the prohibition on {a}"
    if op == "ambiguous":
        return f"t{t}: user was AMBIGUOUS about {a} and wants to be asked first"
    if op == "commit":
        return f"t{t}: user REQUESTED {a}" + (f" once: {ev['guard']}" if ev.get("guard") else " now")
    if op == "approve":
        sat = "satisfies" if ev.get("matches_guard") else "does not satisfy"
        hedge = "" if ev.get("explicit", True) else ", hedged"
        return f"t{t}: user approved '{ev.get('object', '')}' (re {a}; {sat} its condition{hedge})"
    if op == "cancel":
        return f"t{t}: user CANCELLED {a}"
    if op == "tool_result":
        return f"t{t}: TOOL {a} {'SUCCEEDED' if ev.get('success') else 'FAILED'}"
    return f"t{t}: {op} {a}"


class Memory:
    def __init__(self, cond: str, dlg: dict, llm, tc, budget: int, events: list[list[dict]] | None,
                 hard_cap: bool = False):
        self.cond, self.dlg, self.llm, self.tc, self.B = cond, dlg, llm, tc, budget
        self.hard_cap = hard_cap
        self.turns = dlg["turns"]
        self.events = events  # per-turn events (extracted or gold) for ledger/chrono conditions
        self.ledger_cap = int(0.6 * budget)
        self.summary = ""
        self.last_compact = -1
        self.pinned = ""
        self.chrono: list[str] = []
        self.reducer = Reducer(REDUCER_CONDS[cond]) if cond in REDUCER_CONDS else None
        self.typed: dict[str, dict] = {}
        self.calls_failed = 0

    # ------------------------------------------------------------ per-turn updates
    async def observe(self, t: int):
        turn = self.turns[t]
        evs = self.events[t] if self.events is not None else []
        if self.cond in PIN_CONDS and turn["role"] in ("user", "tool"):
            words = int(self.ledger_cap * 0.7)
            system = PIN_HINT_SYSTEM if self.cond == "pinning_hint" else PIN_SYSTEM
            r = await self.llm.chat([
                {"role": "system", "content": system.format(words=words)},
                {"role": "user", "content": f"Current pinned list:\n{self.pinned or '(empty)'}\n\nNew turn:\n{fmt_turn(turn)}"
                                            f"\n\nUpdated pinned list:"}], tag="pin", max_tokens=self.ledger_cap)
            self.pinned = self.tc.truncate(r["text"].strip(), self.ledger_cap)
        elif self.cond in CHRONO_CONDS:
            self.chrono += [chrono_line(t, e, hints=self.cond == "chrono_hint") for e in evs]
        elif self.reducer is not None:
            self.reducer.apply_all(evs, t)
        elif self.cond == "typed_llm" and evs:
            await self._llm_transition(t, evs)

    async def _llm_transition(self, t: int, evs: list[dict]):
        for e in evs:  # item creation is bookkeeping; the status itself is written by the LLM
            if e["item"] not in self.typed:
                self.typed[e["item"]] = dict(id=e["item"], type="prohibition" if e["op"] == "prohibit" else "commitment",
                                             tool=e.get("tool"), target=e.get("target", ""), guard=e.get("guard"),
                                             status="(new)", unclear=False, failed_attempts=0, created_turn=t,
                                             updated_turn=t, history=[])
        view = [{k: v for k, v in i.items() if k not in ("history", "created_turn", "updated_turn")}
                for i in self.typed.values()]
        parsed, _ = await self.llm.chat_json([
            {"role": "system", "content": TRANSITION_SYSTEM},
            {"role": "user", "content": f"Current ledger:\n{json.dumps(view, indent=1)}\n\nTurn text: {fmt_turn(self.turns[t])}"
                                        f"\n\nNew events (turn {t}):\n{json.dumps(evs)}\n\nUpdated ledger:"}],
            TRANSITION_SCHEMA, tag="transition", max_tokens=400)
        if not parsed:
            self.calls_failed += 1
            return
        for row in parsed.get("items", []):
            it = self.typed.get(row.get("id"))
            if it is None:
                continue
            new = (row["status"], bool(row["unclear"]), int(row["failed_attempts"]))
            if new != (it["status"], it["unclear"], it["failed_attempts"]):
                it["history"].append([t, "llm", it["status"], row["status"], ""])
                it["status"], it["unclear"], it["failed_attempts"] = new
                it["updated_turn"] = t
        for it in self.typed.values():  # never-assigned new items default to their creation status
            if it["status"] == "(new)":
                it["status"] = "active" if it["type"] == "prohibition" else ("waiting" if it["guard"] else "ready")

    # ------------------------------------------------------------ ledger views
    def ledger_items(self) -> dict[str, dict] | None:
        if self.reducer is not None:
            return self.reducer.snapshot()
        if self.cond == "typed_llm":
            return {k: dict(v) for k, v in self.typed.items()}
        return None

    def block(self) -> tuple[str, bool]:
        """Persistent block kept alongside the summary; returns (text, truncated?)."""
        if self.cond in PIN_CONDS:
            return (f"PINNED RULES:\n{self.pinned}" if self.pinned else ""), False
        if self.cond in CHRONO_CONDS:
            if not self.chrono:
                return "EVENT LOG: (no events)", False
            header = ("EVENT LOG (chronological extracted events, each with its own action implication):"
                      if self.cond == "chrono_hint" else "EVENT LOG (chronological extracted events; no derived status):")
            txt = self.tc.keep_lines_within(self.chrono, self.ledger_cap, header=header)
            return txt, "older entries dropped" in txt
        items = self.ledger_items()
        if items is None:
            return "", False
        if not items:
            return "STATE LEDGER: (no tracked constraints or commitments)", False
        rows = sorted(items.values(), key=lambda i: i["updated_turn"])
        hints = self.cond != "lifecycle_nohint"
        txt = self.tc.keep_lines_within(["- " + render_item(i, hints=hints) for i in rows], self.ledger_cap,
                                        header="STATE LEDGER (current status of the user's constraints and commitments):")
        return txt, "older entries dropped" in txt

    def _compose(self, summary: str, blk: str) -> str:
        parts = []
        if self.last_compact >= 0:
            parts.append(f"SUMMARY OF EARLIER CONVERSATION (turns 0-{self.last_compact}):\n{summary}")
        if blk:
            parts.append(blk)
        return "\n\n".join(parts)

    def _fit_summary(self, blk: str) -> str:
        """Under the hard cap, shorten the summary until summary + persistent block fits in B tokens."""
        if not self.hard_cap or self.last_compact < 0:
            return self.summary
        summary, n = self.summary, self.tc.count(self.summary)
        while n > 0 and (over := self.tc.count(self._compose(summary, blk)) - self.B) > 0:
            n = max(0, n - over)
            summary = self.tc.truncate(self.summary, n)
        return summary

    # ------------------------------------------------------------ compaction
    async def compact(self, t: int):
        if self.cond == "full":
            return
        blk, _ = self.block()
        previous = self._fit_summary(blk)  # under the hard cap, compaction only sees memory the agent actually kept
        sum_budget = max(int(0.4 * self.B), self.B - self.tc.count(blk))
        new = "\n".join(fmt_turn(x) for x in self.turns[self.last_compact + 1:t + 1])
        system = SUMMARY_HINT_SYSTEM if self.cond == "summary_hint" else SUMMARY_SYSTEM
        r = await self.llm.chat([
            {"role": "system", "content": system.format(words=int(sum_budget * 0.7))},
            {"role": "user", "content": f"Previous summary:\n{previous or '(none)'}\n\nNew conversation turns:\n{new}"
                                        f"\n\nWrite the updated summary."}], tag="summary", max_tokens=sum_budget)
        self.summary = self.tc.truncate(r["text"].strip(), sum_budget)
        self.last_compact = t

    # ------------------------------------------------------------ context at a decision point
    def context(self, t: int) -> dict:
        if self.cond == "full":
            raw = self.turns[:t + 1]
            return dict(memory="", raw="\n".join(fmt_turn(x) for x in raw), memory_tokens=0, truncated=False,
                        summary_capped=False)
        blk, trunc = self.block()
        summary = self._fit_summary(blk)
        mem = self._compose(summary, blk)
        raw = self.turns[self.last_compact + 1:t + 1]
        return dict(memory=mem, raw="\n".join(fmt_turn(x) for x in raw), memory_tokens=self.tc.count(mem),
                    truncated=trunc, summary_capped=summary != self.summary)

    def ledger_label_for(self, gold_item: dict) -> tuple[str | None, dict | None]:
        """Status label of the ledger item aligned to a gold item (by tool; most recently updated)."""
        items = self.ledger_items()
        if items is None:
            return None, None
        if self.cond == "lifecycle_gold":
            it = items.get(gold_item["id"])
            return status_label(it), it
        cands = [i for i in items.values() if i.get("tool") == gold_item["tool"]]
        typed = [i for i in cands if i["type"] == gold_item["type"]]
        pick = max(typed or cands, key=lambda i: i["updated_turn"]) if (typed or cands) else None
        return status_label(pick), pick
