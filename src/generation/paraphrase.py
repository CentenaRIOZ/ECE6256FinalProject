"""LLM-assisted paraphrase of user event turns, validated against the event specification.

A paraphrase is accepted only if it keeps the entity words, the partial/final distinction, and the
polarity cue of its event type; otherwise the template text is kept.

python -m src.generation.paraphrase --in data/dialogues/dialogues_template.jsonl --out data/dialogues/dialogues.jsonl \
    --model meta-llama/Llama-3.1-8B-Instruct --base-url http://localhost:8001/v1
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re

from src.generation.build import PARAPHRASE_VARIANTS
from src.generation.cues import CUES, NEG_FORBIDDEN
from src.llm.client import LLM

SYSTEM = ("Paraphrase a message that a user sent to their workplace assistant. The speaker is the user ('I'); the "
          "assistant is 'you'. Keep exactly the same meaning: who does what, every condition (and who must approve), "
          "negation, hedge or request to be consulted, named entity, number and document name, and whether a whole "
          "document or only a part of it is meant. Change the wording and sentence structure so it sounds natural. "
          "Output only the paraphrased message.")
JUDGE_SYSTEM = ("You check whether a paraphrase has EXACTLY the same meaning as an original message from a user to their "
                "assistant, for the purpose of deciding what the assistant may do. Check: same action and objects; same "
                "polarity (forbid / allow / request / cancel); same condition, with the USER being the one who approves; "
                "same hedging or request to be consulted first; same scope (final version vs. a part or draft); no added "
                "or dropped instructions. Answer JSON {\"same_meaning\": true|false, \"problem\": \"...\"}.")
JUDGE_SCHEMA = {"type": "object", "properties": {"problem": {"type": "string", "maxLength": 200},
                                                 "same_meaning": {"type": "boolean"}},
                "required": ["problem", "same_meaning"]}


def required_words(turn: dict, item: dict) -> list[str]:
    words = [w for w in re.findall(r"[A-Za-z0-9$#,.-]+", item["vp"]) if w[0].isupper() or any(c.isdigit() for c in w)
             or w.startswith("#")]
    words += [w for w in item["artifact"].split() if len(w) > 3]
    if turn["template"].startswith("approve_partial"):
        partial = next(p for p in item["partials"] if p in turn["text"])
        words += [w for w in partial.split() if len(w) > 3]
    return sorted({w.strip(".,").lower() for w in words if w.strip(".,")})


def valid(text: str, turn: dict, item: dict) -> bool:
    low = text.lower()
    key = turn["template"].split(":")[0]
    if not text or len(text) > 3 * len(turn["text"]) + 40 or "\n\n" in text.strip():
        return False
    if any(w not in low for w in required_words(turn, item)):
        return False
    if key in CUES and not any(c in low for c in CUES[key]):
        return False
    if any(c in low for c in NEG_FORBIDDEN.get(key, [])):
        return False
    return True


async def judge_ok(judge, orig: str, para: str) -> bool:
    parsed, _ = await judge.chat_json([{"role": "system", "content": JUDGE_SYSTEM},
                                       {"role": "user", "content": f"Original: {orig}\nParaphrase: {para}"}],
                                      JUDGE_SCHEMA, tag="judge", max_tokens=150)
    return bool(parsed and parsed.get("same_meaning"))


async def paraphrase_turn(llm, judge, turn: dict, item: dict, tries: int = 4) -> str | None:
    for k in range(tries):
        r = await llm.chat([{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": f"Message (attempt {k + 1}):\n{turn['text']}"}],
                           tag="paraphrase", temperature=0.8, max_tokens=120)
        text = r["text"].strip().strip('"').strip()
        if valid(text, turn, item) and await judge_ok(judge, turn["text"], text):
            return text
    return None


async def main_async(a):
    llm = LLM(a.model, a.base_url, a.cache)
    judge = LLM(a.judge_model, a.judge_url, a.cache.replace(".sqlite", "_judge.sqlite"))
    ds = [json.loads(l) for l in open(a.inp)]
    jobs = []
    for d in ds:
        if d["variant"] in PARAPHRASE_VARIANTS:
            d["paraphrased"] = True
            for t in d["turns"]:
                if t["kind"] == "event":
                    jobs.append((t, d["items"][t["item"]]))
    res = await asyncio.gather(*[paraphrase_turn(llm, judge, t, it) for t, it in jobs])
    ok = 0
    for (t, _), p in zip(jobs, res):
        if p:
            t["template_text"], t["text"] = t["text"], p
            ok += 1
    with open(a.out, "w") as f:
        for d in ds:
            f.write(json.dumps(d) + "\n")
    llm.close()
    judge.close()
    # audit sample for manual inspection
    import random
    acc = [(t, it) for (t, it), p in zip(jobs, res) if p]
    random.Random(0).shuffle(acc)
    with open(a.audit, "w") as f:
        f.write("# Paraphrase audit sample (manual check of label validity)\n\n| # | event | template | paraphrase | ok? |\n|---|---|---|---|---|\n")
        for i, (t, it) in enumerate(acc[:40]):
            f.write(f"| {i} | {t['template'].split(':')[0]} | {t['template_text']} | {t['text']} | |\n")
    print(f"paraphrased {ok}/{len(jobs)} event turns ({ok / max(1, len(jobs)):.0%} accepted) -> {a.out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="data/dialogues/dialogues_template.jsonl")
    ap.add_argument("--out", default="data/dialogues/dialogues.jsonl")
    ap.add_argument("--model", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--base-url", default="http://localhost:8001/v1")
    ap.add_argument("--cache", default="cache/llm_paraphrase.sqlite")
    ap.add_argument("--judge-model", default="Qwen/Qwen2.5-7B-Instruct")
    ap.add_argument("--judge-url", default="http://localhost:8000/v1")
    ap.add_argument("--audit", default="data/paraphrase_audit.md")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
