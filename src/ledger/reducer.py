"""Lifecycle-Aware Dialogue Ledger: record schema + deterministic reducer.

Events (shared by gold timelines and LLM extraction):
  prohibit    {item, tool, target, text}            create / reinstate a prohibition -> active
  revoke      {item}                                prohibition active -> revoked
  ambiguous   {item}                                flag item as unclear (needs clarification)
  commit      {item, tool, target, guard|None}      create commitment -> waiting (guard) / ready (no guard)
  approve     {item, object, explicit, matches_guard}
                                                    waiting -> ready only if explicit AND matches_guard
  cancel      {item}                                waiting/ready -> cancelled
  tool_result {item, success}                       ready -> completed only on verified success;
                                                    failure keeps it pending (ready, failed_attempts+1)

Every transition (and every rejected transition) is logged with its evidence turn.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field, asdict
from typing import Optional

PROHIBITION = "prohibition"
COMMITMENT = "commitment"

PROHIBITION_STATUSES = ("active", "revoked")
COMMITMENT_STATUSES = ("waiting", "ready", "completed", "cancelled")

OPS = ("prohibit", "revoke", "ambiguous", "commit", "approve", "cancel", "tool_result")
CREATING_OPS = ("prohibit", "commit")


@dataclass
class ItemState:
    id: str
    type: str
    tool: Optional[str] = None
    target: str = ""
    text: str = ""
    guard: Optional[str] = None
    status: str = ""
    unclear: bool = False
    failed_attempts: int = 0
    created_turn: int = -1
    updated_turn: int = -1
    history: list = field(default_factory=list)  # [turn, op, from_status, to_status, note]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReducerConfig:
    guard_logic: bool = True     # ablation: False -> any approval triggers a waiting commitment
    receipt_logic: bool = True   # ablation: False -> any tool result (even failure) completes it


class Reducer:
    def __init__(self, config: ReducerConfig | None = None):
        self.cfg = config or ReducerConfig()
        self.items: dict[str, ItemState] = {}

    # ------------------------------------------------------------------ helpers
    def _log(self, it: ItemState, turn: int, op: str, before: str, note: str = ""):
        it.history.append([turn, op, before, it.status, note])
        it.updated_turn = turn

    def find_by_tool(self, tool: Optional[str], type_: Optional[str] = None) -> Optional[ItemState]:
        cands = [i for i in self.items.values() if i.tool == tool and (type_ is None or i.type == type_)]
        return max(cands, key=lambda i: i.updated_turn) if cands else None

    # ------------------------------------------------------------------ apply
    def apply(self, ev: dict, turn: int) -> None:
        op = ev.get("op")
        iid = ev.get("item")
        it = self.items.get(iid) if iid else None

        if op == "prohibit":
            if it is None:
                it = ItemState(id=iid, type=PROHIBITION, tool=ev.get("tool"), target=ev.get("target", ""),
                               text=ev.get("text", ""), status="active", created_turn=turn)
                self.items[iid] = it
                self._log(it, turn, op, "", "created")
            elif it.type == PROHIBITION:
                before = it.status
                it.status, it.unclear = "active", False
                self._log(it, turn, op, before, "reinstated" if before == "revoked" else "restated")
            return

        if op == "commit":
            if it is None:
                guard = ev.get("guard") or None
                it = ItemState(id=iid, type=COMMITMENT, tool=ev.get("tool"), target=ev.get("target", ""),
                               text=ev.get("text", ""), guard=guard,
                               status="waiting" if guard else "ready", created_turn=turn)
                self.items[iid] = it
                self._log(it, turn, op, "", "created")
            return  # re-commit of an existing item: no state change

        if op == "tool_result" and it is None:
            # action outcome without a known commitment: record it as an action-outcome item
            if not iid:
                return
            ok = bool(ev.get("success"))
            it = ItemState(id=iid, type=COMMITMENT, tool=ev.get("tool"), target=ev.get("target", ""),
                           status="completed" if (ok or not self.cfg.receipt_logic) else "ready",
                           failed_attempts=0 if ok else 1, created_turn=turn)
            self.items[iid] = it
            self._log(it, turn, op, "", "outcome-only record")
            return

        if it is None:
            return  # update for an unknown item: ignored (logged by caller if needed)

        before = it.status
        if op == "revoke":
            if it.type == PROHIBITION:
                it.status, it.unclear = "revoked", False
                self._log(it, turn, op, before)
            elif it.status in ("waiting", "ready"):
                it.status, it.unclear = "cancelled", False
                self._log(it, turn, op, before, "revoke on commitment treated as cancel")
        elif op == "ambiguous":
            if it.status in ("active", "waiting", "ready"):
                it.unclear = True
                self._log(it, turn, op, before, "flagged for clarification")
        elif op == "approve":
            if it.type != COMMITMENT:
                return
            if it.status != "waiting":
                self._log(it, turn, op, before, f"approval ignored (status {it.status})")
                return
            explicit = bool(ev.get("explicit", True))
            matches = bool(ev.get("matches_guard", True))
            if not self.cfg.guard_logic or (explicit and matches):
                it.status, it.unclear = "ready", False
                self._log(it, turn, op, before, f"guard satisfied by: {ev.get('object', '')}")
            elif not explicit:
                it.unclear = True
                self._log(it, turn, op, before, f"non-explicit approval of {ev.get('object', '')}: needs clarification")
            else:
                self._log(it, turn, op, before, f"approval of {ev.get('object', '')} does NOT satisfy guard")
        elif op == "cancel":
            if it.type == COMMITMENT and it.status in ("waiting", "ready"):
                it.status, it.unclear = "cancelled", False
                self._log(it, turn, op, before)
            elif it.type == PROHIBITION and it.status == "active":
                it.status, it.unclear = "revoked", False
                self._log(it, turn, op, before, "cancel on prohibition treated as revoke")
        elif op == "tool_result":
            if it.type != COMMITMENT or it.status in ("completed", "cancelled"):
                self._log(it, turn, op, before, "tool result on inactive item")
                return
            ok = bool(ev.get("success"))
            if ok or not self.cfg.receipt_logic:
                it.status, it.unclear = "completed", False
                self._log(it, turn, op, before, "verified success" if ok else "attempt (no receipt check)")
            else:
                it.status = "ready"
                it.failed_attempts += 1
                self._log(it, turn, op, before, "attempt FAILED; still pending")

    def apply_all(self, events: list[dict], turn: int) -> None:
        for ev in events:
            self.apply(ev, turn)

    def snapshot(self) -> dict[str, dict]:
        return {k: v.to_dict() for k, v in copy.deepcopy(self.items).items()}


# ---------------------------------------------------------------------- decisions
DECISIONS = ("act", "wait", "clarify", "decline")


def gold_decision(item: Optional[dict]) -> tuple[str, str]:
    """Rule mapping an item's lifecycle state to the permissible decision (+ reason code)."""
    if item is None:
        return "act", "unrestricted"
    if item["type"] == PROHIBITION:
        if item["status"] == "active":
            return ("clarify", "ambiguous") if item["unclear"] else ("decline", "prohibited_active")
        return "act", "revoked"
    st = item["status"]
    if st == "cancelled":
        return "decline", "cancelled"
    if st == "completed":
        return "decline", "completed"
    if item["unclear"]:
        return "clarify", "ambiguous"
    if st == "waiting":
        return "wait", "guard_unmet"
    return ("act", "retry_after_failure") if item["failed_attempts"] > 0 else ("act", "ready")


def status_label(item: Optional[dict]) -> str:
    """Coarse user-facing status label (used by state queries / state accuracy)."""
    if item is None:
        return "unknown"
    if item.get("unclear") and item["status"] in ("active", "waiting", "ready"):
        return "needs_confirmation"
    return {
        "active": "in_force", "revoked": "lifted",
        "waiting": "waiting_for_condition", "ready": "ready_to_do",
        "completed": "done", "cancelled": "cancelled",
    }.get(item["status"], "unknown")


def label_history(item: dict) -> list[str]:
    """Sequence of labels an item has had (for stale-vs-missing analysis)."""
    labels, unclear = [], False
    for turn, op, before, after, note in item["history"]:
        if op == "ambiguous" or "needs clarification" in note:
            unclear = True
        elif before != after or op in CREATING_OPS:
            unclear = False
        lab = status_label({"status": after, "unclear": unclear})
        if not labels or labels[-1] != lab:
            labels.append(lab)
    return labels


STATUS_HINT = {
    ("prohibition", "active"): "ACTIVE - do NOT perform",
    ("prohibition", "revoked"): "REVOKED - restriction lifted, action allowed",
    ("commitment", "waiting"): "WAITING - condition not yet met",
    ("commitment", "ready"): "READY - condition met / requested, not yet done: perform when asked",
    ("commitment", "completed"): "COMPLETED - verified success, do NOT repeat",
    ("commitment", "cancelled"): "CANCELLED - do NOT perform",
}


def render_item(it: dict) -> str:
    action = f"{it.get('tool') or '?'}({it.get('target', '')})"
    status = STATUS_HINT.get((it["type"], it["status"]), it["status"].upper())
    parts = [f"[{it['id']}] {it['type'].upper()} {action}: {status} (since turn {it['updated_turn']})"]
    if it.get("guard"):
        parts.append(f"condition: {it['guard']}")
    if it.get("unclear"):
        parts.append("UNCLEAR - latest user update was ambiguous; ask the user before acting")
    if it.get("failed_attempts") and it["status"] == "ready":
        parts.append(f"{it['failed_attempts']} failed attempt(s) - still pending")
    last_note = it["history"][-1][4] if it.get("history") else ""
    if last_note and ("NOT satisfy" in last_note or "ignored" in last_note):
        parts.append(f"note: {last_note}")
    return "; ".join(parts)


def render_ledger(items: dict[str, dict]) -> str:
    if not items:
        return "STATE LEDGER: (no tracked constraints or commitments)"
    rows = sorted(items.values(), key=lambda i: i["created_turn"])
    return "STATE LEDGER (current status of the user's constraints and commitments):\n" + \
        "\n".join("- " + render_item(i) for i in rows)
