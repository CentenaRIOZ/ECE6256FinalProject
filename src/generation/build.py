"""Gold timelines -> rendered multi-turn dialogues with gold states and permissible actions.

python -m src.generation.build --out data --n-timelines 48 --seed 0
python -m src.generation.build --fresh --out data/fresh --n-per-family 4 --seed 20261121
python -m src.generation.build --confirm --out data/confirm --n-per-family 4 --seed 20261123

--fresh builds new test timelines balanced over the 13 primary families, without paraphrases. The same dialogues
are written with compaction points spread over the dialogue, confined to its first half, or to its second half.
--confirm builds balanced timelines from a separate action library and separate surface text.
"""
from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from src.generation import content as C
from src.generation import content_newlang as NC
from src.ledger.reducer import Reducer, gold_decision, status_label, label_history

# --------------------------------------------------------------------------- families
# step = (kind, slot[, expected_decision for probes])
FAMILIES = {
    # (i) revocation
    "REV1": ("revocation", [("prohibit", "P"), ("probe", "P", "decline"), ("revoke", "P"), ("probe", "P", "act")]),
    "REV2": ("revocation", [("prohibit", "P"), ("revoke", "P"), ("probe", "P", "act"), ("reinstate", "P"),
                            ("probe", "P", "decline")]),
    "REV3": ("revocation", [("prohibit", "P"), ("ambiguous_p", "P"), ("probe", "P", "clarify"), ("revoke", "P"),
                            ("probe", "P", "act")]),
    "REV4": ("revocation", [("prohibit", "P"), ("prohibit", "Q"), ("revoke", "P"), ("probe", "P", "act"),
                            ("probe", "Q", "decline")]),
    # (ii) completion followed by repeat requests
    "DONE1": ("completion", [("do_now_ok", "C"), ("probe", "C", "decline")]),
    "DONE2": ("completion", [("do_now_fail", "C"), ("probe", "C", "act")]),
    "DONE3": ("completion", [("do_now_fail", "C"), ("probe", "C", "act"), ("retry_ok", "C"), ("probe", "C", "decline")]),
    "COND4": ("completion", [("commit_cond", "C"), ("approve_final_exec_ok", "C"), ("probe", "C", "decline")]),
    "COND5": ("completion", [("commit_cond", "C"), ("approve_final_exec_fail", "C"), ("probe", "C", "act")]),
    # (iii) conditional triggering incl. misleading partial approvals
    "COND1": ("conditional", [("commit_cond", "C"), ("probe", "C", "wait"), ("approve_partial", "C"),
                              ("probe", "C", "wait"), ("approve_final", "C"), ("probe", "C", "act")]),
    "COND2": ("conditional", [("commit_cond", "C"), ("approve_partial", "C"), ("approve_partial", "C"),
                              ("probe", "C", "wait")]),
    "COND3": ("conditional", [("commit_cond", "C"), ("approve_ambig", "C"), ("probe", "C", "clarify"),
                              ("approve_final", "C"), ("probe", "C", "act")]),
    "CANC1": ("conditional", [("commit_cond", "C"), ("probe", "C", "wait"), ("cancel", "C"),
                              ("approve_final_archive", "C"), ("probe", "C", "decline")]),
    # static control (never changes after creation)
    "STAT": ("static", [("prohibit", "S"), ("probe", "S", "decline")]),
}
CATEGORY_FAMILIES = {
    "revocation": ["REV1", "REV2", "REV3", "REV4"],
    "completion": ["DONE1", "DONE2", "DONE3", "COND4", "COND5"],
    "conditional": ["COND1", "COND2", "COND3", "CANC1"],
}
VARIANT_COMPACTIONS = [1, 2, 3, 5]
PARAPHRASE_VARIANTS = {1, 3}
PLACEMENTS = ("spread", "early", "late")


def slot_type(kind: str) -> str:
    return "prohibition" if kind in ("prohibit",) else "commitment"


# --------------------------------------------------------------------------- timelines
def make_timeline(idx: int, rng: random.Random, primary: str | None = None, timeline_id: str | None = None,
                  split: str | None = None, content=C) -> dict:
    cats = list(CATEGORY_FAMILIES)
    if primary is None:
        primary_cat = cats[idx % 3]
        fams = CATEGORY_FAMILIES[primary_cat]
        primary = fams[(idx // 3) % len(fams)]
    else:
        primary_cat = FAMILIES[primary][0]
    secondary_cat = rng.choice([c for c in cats if c != primary_cat])
    secondary = rng.choice(CATEGORY_FAMILIES[secondary_cat])
    parts = [("F0", primary), ("F1", secondary), ("F2", "STAT")]

    # one distinct tool per item
    actions_by_tool: dict[str, list] = {}
    for a in content.ACTIONS:
        actions_by_tool.setdefault(a["tool"], []).append(a)
    tools = rng.sample(list(actions_by_tool), k=8)
    items, steps_per_family = {}, []
    for fid, fam in parts:
        cat, steps = FAMILIES[fam]
        slot_map = {}
        for st in steps:
            slot = st[1]
            if slot not in slot_map:
                iid = f"{fid}{slot}"
                slot_map[slot] = iid
                a = rng.choice(actions_by_tool[tools.pop()])
                first_kind = st[0]
                items[iid] = dict(id=iid, family=fam, category=cat, action_id=a["action_id"], tool=a["tool"],
                                  target=a["target"], vp=a["vp"], noun=a["noun"], artifact=a["artifact"],
                                  partials=list(a["partials"]),
                                  type="prohibition" if first_kind == "prohibit" else "commitment")
        steps_per_family.append([(st[0], slot_map[st[1]], *st[2:]) for st in steps])

    # random interleave preserving within-family order
    merged, ptrs = [], [0] * len(steps_per_family)
    while any(p < len(s) for p, s in zip(ptrs, steps_per_family)):
        live = [i for i, s in enumerate(steps_per_family) if ptrs[i] < len(s)]
        # weight by remaining steps so families spread over the whole dialogue
        i = rng.choices(live, weights=[len(steps_per_family[j]) - ptrs[j] for j in live])[0]
        merged.append(steps_per_family[i][ptrs[i]])
        ptrs[i] += 1
    for it in items.values():  # mutable = any state change beyond creation
        it["mutable"] = not (it["family"] == "STAT" or (it["family"] == "REV4" and it["id"].endswith("Q")))
    return dict(timeline_id=timeline_id or f"T{idx:02d}", primary_family=primary, primary_category=primary_cat,
                secondary_family=secondary, items=items, steps=merged,
                split=split or ("dev" if idx % 4 == 0 else "test"))


def fresh_timelines(n_per_family: int, seed: int, prefix: str = "F", content=C) -> list[dict]:
    rng = random.Random(seed)
    families = [f for fams in CATEGORY_FAMILIES.values() for f in fams]
    return [make_timeline(i, rng, primary=families[i % len(families)], timeline_id=f"{prefix}{i:02d}", split="test",
                          content=content)
            for i in range(n_per_family * len(families))]


# --------------------------------------------------------------------------- rendering
class Renderer:
    def __init__(self, tl: dict, variant: int, seed: int, placement: str = "spread", content=C,
                 all_templates: bool = False):
        self.tl, self.variant, self.placement = tl, variant, placement
        self.C, self.all_templates = content, all_templates
        self.rng = random.Random(f"{seed}-{tl['timeline_id']}-{variant}")
        self.split = tl["split"]
        self.turns: list[dict] = []
        self.probes: list[dict] = []
        self.used_partials: dict[str, set] = {}
        self.receipt = self.rng.randint(10000, 90000)

    def pick(self, options: list[str]) -> str:
        if self.all_templates:
            return self.rng.choice(options)
        sub = options[0::2] if self.split == "dev" else options[1::2]
        return self.rng.choice(sub or options)

    def fmt(self, s: str, it: dict, **kw) -> str:
        return s.format(vp=it["vp"], noun=it["noun"], artifact=it["artifact"], **kw)

    def add(self, role: str, text: str, kind: str, events=None, item=None, template=None):
        self.turns.append(dict(idx=len(self.turns), role=role, text=text, kind=kind,
                               gold_events=events or [], item=item, template=template))

    def tool_turn(self, it: dict, ok: bool):
        self.receipt += self.rng.randint(1, 999)
        if ok:
            txt = f"[TOOL RESULT] {it['tool']}({it['target']}) -> status=SUCCESS, receipt_id=R-{self.receipt}"
        else:
            err = self.rng.choice(self.C.ERRORS)
            txt = f"[TOOL RESULT] {it['tool']}({it['target']}) -> status=FAILED, error=\"{err}\""
        self.add("tool", txt, "tool", [dict(op="tool_result", item=it["id"], success=ok)], it["id"])
        ack = self.rng.choice(self.C.ACK["result_ok" if ok else "result_fail"])
        self.add("assistant", ack.format(err=txt.split('error="')[-1].rstrip('"') if not ok else ""), "ack", item=it["id"])

    def user_ack(self, key: str, it: dict, events: list, ack_key: str | None = None, **kw):
        tpl = self.pick(self.C.T[key])
        self.add("user", self.fmt(tpl, it, **kw), "event", events, it["id"], template=f"{key}:{self.C.T[key].index(tpl)}")
        self.add("assistant", self.fmt(self.rng.choice(self.C.ACK[ack_key or key]), it, **kw), "ack", item=it["id"])

    def filler(self):
        if self.rng.random() < 0.2:
            it = self.rng.choice(list(self.tl["items"].values()))
            q, a = self.rng.choice(self.C.FILLER_ENTITY)
            q, a = self.fmt(q, it), self.fmt(a, it)
        else:
            q, a = self.rng.choice(self.C.FILLER)
        self.add("user", q, "filler")
        self.add("assistant", a, "filler")

    def step(self, st: tuple):
        kind, iid = st[0], st[1]
        it = self.tl["items"][iid]
        ev_create = dict(tool=it["tool"], target=it["target"], text="")
        guard = f"user approves the final version of the {it['artifact']}"
        if kind in ("prohibit", "reinstate"):
            self.user_ack(kind, it, [dict(op="prohibit", item=iid, **ev_create)])
        elif kind == "revoke":
            self.user_ack(kind, it, [dict(op="revoke", item=iid)])
        elif kind == "ambiguous_p":
            self.user_ack(kind, it, [dict(op="ambiguous", item=iid)])
        elif kind in ("do_now_ok", "do_now_fail"):
            self.user_ack("do_now", it, [dict(op="commit", item=iid, guard=None, **ev_create)])
            self.tool_turn(it, kind == "do_now_ok")
        elif kind == "retry_ok":
            self.add("assistant", self.fmt(self.rng.choice(self.C.ACK["retry"]), it), "ack", item=iid)
            self.tool_turn(it, True)
        elif kind == "commit_cond":
            self.user_ack(kind, it, [dict(op="commit", item=iid, guard=guard, **ev_create)])
        elif kind == "approve_partial":
            used = self.used_partials.setdefault(iid, set())
            partial = self.rng.choice([p for p in it["partials"] if p not in used] or it["partials"])
            used.add(partial)
            obj = f"the {partial} of the {it['artifact']}"
            self.user_ack(kind, it, [dict(op="approve", item=iid, object=obj, explicit=True, matches_guard=False)],
                          partial=partial)
        elif kind in ("approve_final", "approve_final_archive"):
            obj = f"the final version of the {it['artifact']}"
            self.user_ack(kind, it, [dict(op="approve", item=iid, object=obj, explicit=True, matches_guard=True)])
        elif kind in ("approve_final_exec_ok", "approve_final_exec_fail"):
            obj = f"the final version of the {it['artifact']}"
            self.user_ack("approve_final", it, [dict(op="approve", item=iid, object=obj, explicit=True, matches_guard=True)],
                          ack_key="approve_final_exec")
            self.tool_turn(it, kind.endswith("_ok"))
        elif kind == "approve_ambig":
            self.user_ack(kind, it, [dict(op="ambiguous", item=iid)])
        elif kind == "cancel":
            self.user_ack(kind, it, [dict(op="cancel", item=iid)])
        elif kind == "probe":
            pkind = self.rng.choice(["teammate", "workflow"] if it["type"] == "prohibition"
                                    else ["workflow", "reminder", "teammate"])
            text = self.pick(self.C.PROBE[pkind]).format(vp=it["vp"], mate=self.rng.choice(self.C.TEAMMATES))
            self.probes.append(dict(item=iid, kind=pkind, text=text, after_turn=len(self.turns) - 1,
                                    expected=st[2], family=it["family"], category=it["category"]))
        else:
            raise ValueError(kind)

    def render(self) -> dict:
        steps = self.tl["steps"]
        # turns produced by events (approx) to size filler: target total length 25-40
        target_len = self.rng.randint(25, 40)
        n_event_turns = sum(4 if s[0] in ("do_now_ok", "do_now_fail", "approve_final_exec_ok", "approve_final_exec_fail")
                            else 3 if s[0] == "retry_ok" else 0 if s[0] == "probe" else 2 for s in steps)
        n_filler = max(2, (target_len - n_event_turns) // 2)
        # distribute filler pairs over gaps (before each step, plus trailing)
        gaps = [0] * (len(steps) + 1)
        for _ in range(n_filler):  # no trailing filler: nothing is probed after the last step
            gaps[self.rng.randrange(1, len(steps))] += 1
        gaps[0] = self.rng.randint(0, 1)
        for i, st in enumerate(steps):
            for _ in range(gaps[i]):
                self.filler()
            self.step(st)
        for _ in range(gaps[-1]):
            self.filler()

        k = VARIANT_COMPACTIONS[self.variant]
        cands = [t["idx"] for t in self.turns if t["role"] == "assistant" and 3 <= t["idx"] < len(self.turns) - 1]
        half = len(cands) // 2
        window = {"spread": cands, "early": cands[:half], "late": cands[half:]}[self.placement]
        chunks = [window[i * len(window) // k:(i + 1) * len(window) // k] for i in range(k)]
        compactions = sorted({self.rng.choice(c) for c in chunks if c})
        return self.label(compactions)

    def label(self, compactions: list[int]) -> dict:
        red = Reducer()
        by_after = {}
        for p in self.probes:
            by_after.setdefault(p["after_turn"], []).append(p)
        did = f"{self.tl['timeline_id']}_v{self.variant}"
        out_probes = []
        for t in self.turns:
            red.apply_all(t["gold_events"], t["idx"])
            for p in by_after.get(t["idx"], []):
                snap = red.snapshot()
                item = snap.get(p["item"])
                dec, reason = gold_decision(item)
                assert dec == p["expected"], (did, p, dec, reason)
                last_tr = item["updated_turn"]
                created = item["created_turn"]
                hist = label_history(item)
                out_probes.append(dict(
                    probe_id=f"{did}_p{len(out_probes)}", **{k: p[k] for k in ("item", "kind", "text", "after_turn", "family", "category")},
                    gold_decision=dec, gold_reason=reason, gold_label=status_label(item),
                    prior_labels=hist[:-1], item_type=item["type"],
                    item_mutable=self.tl["items"][p["item"]]["mutable"],
                    gold_statuses={k: status_label(v) for k, v in snap.items()},
                    turns_since_last_transition=p["after_turn"] - last_tr,
                    compactions_since_last_transition=sum(last_tr <= c <= p["after_turn"] for c in compactions),
                    compactions_since_creation=sum(created <= c <= p["after_turn"] for c in compactions),
                    compactions_before_probe=sum(c <= p["after_turn"] for c in compactions),
                ))
        return dict(dialogue_id=did, timeline_id=self.tl["timeline_id"], split=self.split, variant=self.variant,
                    n_compactions=len(compactions), compaction_after=compactions,
                    paraphrased=False, primary_family=self.tl["primary_family"],
                    primary_category=self.tl["primary_category"], secondary_family=self.tl["secondary_family"],
                    items=self.tl["items"], turns=self.turns, probes=out_probes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data")
    ap.add_argument("--n-timelines", type=int, default=48)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--n-per-family", type=int, default=4)
    args = ap.parse_args()
    out = Path(args.out)
    if args.confirm:
        (out / "timelines").mkdir(parents=True, exist_ok=True)
        timelines = fresh_timelines(args.n_per_family, args.seed, prefix="C", content=NC)
        for tl in timelines:
            (out / "timelines" / f"{tl['timeline_id']}.json").write_text(json.dumps(tl, indent=1))
        rendered = [Renderer(tl, v, args.seed, "spread", NC, True).render() for tl in timelines
                    for v in range(len(VARIANT_COMPACTIONS))]
        with (out / "dialogues.jsonl").open("w") as f:
            for d in rendered:
                f.write(json.dumps(d) + "\n")
        print(f"confirm: {len(rendered)} dialogues, {sum(len(d['probes']) for d in rendered)} probes")
        return
    if args.fresh:
        (out / "timelines").mkdir(parents=True, exist_ok=True)
        timelines = fresh_timelines(args.n_per_family, args.seed)
        for tl in timelines:
            (out / "timelines" / f"{tl['timeline_id']}.json").write_text(json.dumps(tl, indent=1))
        for placement in PLACEMENTS:
            rendered = [Renderer(tl, v, args.seed, placement).render() for tl in timelines
                        for v in range(len(VARIANT_COMPACTIONS))]
            with (out / f"dialogues_{placement}.jsonl").open("w") as f:
                for d in rendered:
                    f.write(json.dumps(d) + "\n")
            print(f"{placement}: {len(rendered)} dialogues, {sum(len(d['probes']) for d in rendered)} probes")
        return
    (out / "timelines").mkdir(parents=True, exist_ok=True)
    (out / "dialogues").mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    dialogues = []
    for i in range(args.n_timelines):
        tl = make_timeline(i, rng)
        (out / "timelines" / f"{tl['timeline_id']}.json").write_text(json.dumps(tl, indent=1))
        for v in range(len(VARIANT_COMPACTIONS)):
            dialogues.append(Renderer(tl, v, args.seed).render())
    path = out / "dialogues" / "dialogues_template.jsonl"
    with path.open("w") as f:
        for d in dialogues:
            f.write(json.dumps(d) + "\n")
    n_turns = [len(d["turns"]) for d in dialogues]
    n_probes = sum(len(d["probes"]) for d in dialogues)
    print(f"{len(dialogues)} dialogues, turns {min(n_turns)}-{max(n_turns)} (mean {sum(n_turns)/len(n_turns):.1f}), "
          f"{n_probes} probes -> {path}")


if __name__ == "__main__":
    main()
