import json
import random

from src.extraction.extractor import Registry
from src.generation.build import FAMILIES, Renderer, make_timeline
from src.ledger.reducer import Reducer, ReducerConfig, gold_decision, label_history, status_label


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
