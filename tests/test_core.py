import json
import random

from src.extraction.extractor import Registry
from src.generation.build import CATEGORY_FAMILIES, FAMILIES, Renderer, fresh_timelines, make_timeline
from src.ledger.reducer import Reducer, ReducerConfig, gold_decision, label_history, render_item, status_label
from src.memory.managers import Memory


def item(r, iid):
    return r.snapshot()[iid]


def test_prohibition_lifecycle():
    r = Reducer()
    r.apply(dict(op="prohibit", item="P", tool="send_email", target="x"), 1)
    assert gold_decision(item(r, "P")) == ("decline", "prohibited_active")
    r.apply(dict(op="ambiguous", item="P"), 2)
    assert gold_decision(item(r, "P"))[0] == "clarify"
    r.apply(dict(op="revoke", item="P"), 3)
    assert gold_decision(item(r, "P")) == ("act", "revoked")
    r.apply(dict(op="prohibit", item="P"), 4)
    assert gold_decision(item(r, "P")) == ("decline", "prohibited_active")
    assert label_history(item(r, "P")) == ["in_force", "needs_confirmation", "lifted", "in_force"]


def test_guard_and_receipts():
    r = Reducer()
    r.apply(dict(op="commit", item="C", tool="send_email", target="x", guard="final approved"), 1)
    assert gold_decision(item(r, "C")) == ("wait", "guard_unmet")
    r.apply(dict(op="approve", item="C", object="outline", explicit=True, matches_guard=False), 2)
    assert item(r, "C")["status"] == "waiting"
    r.apply(dict(op="approve", item="C", object="final", explicit=True, matches_guard=True), 3)
    assert gold_decision(item(r, "C")) == ("act", "ready")
    r.apply(dict(op="tool_result", item="C", success=False), 4)
    assert gold_decision(item(r, "C")) == ("act", "retry_after_failure")
    r.apply(dict(op="tool_result", item="C", success=True), 5)
    assert gold_decision(item(r, "C")) == ("decline", "completed")


def test_ablations():
    r = Reducer(ReducerConfig(guard_logic=False))
    r.apply(dict(op="commit", item="C", tool="t", guard="g"), 1)
    r.apply(dict(op="approve", item="C", explicit=True, matches_guard=False), 2)
    assert item(r, "C")["status"] == "ready"
    r = Reducer(ReducerConfig(receipt_logic=False))
    r.apply(dict(op="commit", item="C", tool="t", guard=None), 1)
    r.apply(dict(op="tool_result", item="C", success=False), 2)
    assert item(r, "C")["status"] == "completed"


def test_cancel_then_approve_stays_cancelled():
    r = Reducer()
    r.apply(dict(op="commit", item="C", tool="t", guard="g"), 1)
    r.apply(dict(op="cancel", item="C"), 2)
    r.apply(dict(op="approve", item="C", explicit=True, matches_guard=True), 3)
    assert gold_decision(item(r, "C")) == ("decline", "cancelled")


def test_all_families_render_with_expected_gold():
    rng = random.Random(1)
    for i in range(24):
        tl = make_timeline(i, rng)
        for v in range(4):
            d = Renderer(tl, v, 1).render()  # asserts expected decisions internally
            assert 20 <= len(d["turns"]) <= 45
            tools = [it["tool"] for it in d["items"].values()]
            assert len(tools) == len(set(tools))
            json.dumps(d)
    assert set(FAMILIES) >= {"REV1", "COND1", "DONE1", "STAT"}


def test_registry_resolution():
    reg = Registry()
    evs = reg.resolve([dict(op="prohibit", item="new", tool="share_file", target="pitch deck; Acme")])
    assert evs[0]["item"] == "I1"
    # a second prohibit on the same action reuses the item (reinstatement)
    evs = reg.resolve([dict(op="prohibit", item="new", tool="share_file", target="Acme pitch deck")])
    assert evs[0]["item"] == "I1"
    # dangling id resolved by tool
    evs = reg.resolve([dict(op="revoke", item="I9", tool="share_file", target="")])
    assert evs[0]["item"] == "I1"
    evs = reg.resolve([dict(op="tool_result", item="new", tool="send_email", target="Dana", success=True)])
    assert evs[0]["item"] == "I2"


def test_status_label():
    assert status_label(None) == "unknown"
    assert status_label(dict(status="ready", unclear=True)) == "needs_confirmation"


def test_no_hint_render_keeps_state_without_directives():
    r = Reducer()
    r.apply(dict(op="prohibit", item="P", tool="send_email", target="report"), 1)
    r.apply(dict(op="ambiguous", item="P"), 2)
    r.apply(dict(op="commit", item="C", tool="share_file", target="deck"), 3)
    r.apply(dict(op="tool_result", item="C", success=False), 4)
    plain = render_item(item(r, "P"), hints=False) + render_item(item(r, "C"), hints=False)
    assert "ACTIVE" in plain and "UNCLEAR" in plain and "READY" in plain and "1 failed attempt(s)" in plain
    for directive in ("do NOT", "allowed", "perform", "ask the user", "still pending"):
        assert directive not in plain
    assert "do NOT perform" in render_item(item(r, "P"))


class WordCounter:
    def count(self, text):
        return len(text.split())

    def truncate(self, text, n):
        return " ".join(text.split()[:n])

    def keep_lines_within(self, lines, n, header=""):
        return "\n".join([header, *lines])


def _capped_memory(hard_cap):
    tc = WordCounter()
    dlg = {"turns": [{"idx": 0, "role": "user", "text": "x"}]}
    mem = Memory("lifecycle", dlg, None, tc, 40, [[]], hard_cap=hard_cap)
    mem.reducer.apply(dict(op="prohibit", item="P", tool="send_email", target="report"), 0)
    mem.summary = " ".join(f"w{i}" for i in range(100))
    mem.last_compact = 0
    return mem, tc


def test_hard_cap_limits_memory_and_keeps_ledger():
    mem, tc = _capped_memory(hard_cap=True)
    ctx = mem.context(0)
    assert tc.count(ctx["memory"]) <= 40
    assert ctx["summary_capped"] and "PROHIBITION" in ctx["memory"]


def test_fresh_timelines_are_balanced_and_placement_only_moves_compactions():
    timelines = fresh_timelines(2, 7)
    families = [f for fams in CATEGORY_FAMILIES.values() for f in fams]
    assert sorted(t["primary_family"] for t in timelines) == sorted(families * 2)
    assert all(t["split"] == "test" and t["timeline_id"].startswith("F") for t in timelines)
    for tl in timelines:
        spread, early, late = (Renderer(tl, 3, 7, p).render() for p in ("spread", "early", "late"))
        assert [t["text"] for t in spread["turns"]] == [t["text"] for t in early["turns"]] == [t["text"] for t in late["turns"]]
        assert [p["gold_decision"] for p in spread["probes"]] == [p["gold_decision"] for p in late["probes"]]
        assert max(early["compaction_after"]) < min(late["compaction_after"])


def test_default_memory_is_unchanged_without_hard_cap():
    mem, tc = _capped_memory(hard_cap=False)
    ctx = mem.context(0)
    assert mem.summary in ctx["memory"] and tc.count(ctx["memory"]) > 40
    assert not ctx["summary_capped"]
