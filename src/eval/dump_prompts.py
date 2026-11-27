"""Write every prompt the project sends to a model, verbatim, to docs/prompts.md.

python -m src.eval.dump_prompts --out docs/prompts.md

System prompts are printed exactly as sent. User messages are recorded from the real code paths, run on the first Confirm
dialogue (and one Test event turn for the paraphraser) with a stand-in model that returns fixed placeholder answers and a
whitespace token counter, so their content is an example while their wording and layout are exactly the code's.
tests/test_core.py checks that the file matches this script's output.
"""
from __future__ import annotations

import argparse
import ast
import asyncio
import json
from pathlib import Path

from src.extraction.extractor import EXTRACT_PROMPTS, extract_dialogue
from src.extraction.noise import noisy_gold_events
from src.generation.content import TOOLS
from src.memory.managers import (ACTION_GUIDANCE, PIN_HINT_SYSTEM, PIN_SYSTEM, SUMMARY_HINT_SYSTEM, SUMMARY_SYSTEM,
                                 TRANSITION_SYSTEM, Memory)
from src.policy.policy import POLICY_SYSTEM, STATE_SYSTEM, decide, state_query

ROOT = Path(__file__).resolve().parents[2]
REPLIES = {"extract": '{"events": []}', "transition": '{"items": []}', "summary": "(summary written by the model)",
           "pin": "(pinned rules written by the model)", "state_query": '{"status": "unknown"}',
           "policy": '{"user_instructions": "none", "current_status": "none", "decision": "act"}'}


class Recorder:
    """Stands in for src.llm.client.LLM and keeps the first request of each kind."""

    def __init__(self):
        self.calls: dict[str, dict] = {}

    async def chat(self, messages, *, tag="", max_tokens=512, temperature=0.0, json_schema=None):
        self.calls.setdefault(tag, dict(messages=messages, max_tokens=max_tokens, temperature=temperature,
                                        json_schema=json_schema))
        return dict(text=REPLIES.get(tag, ""), prompt_tokens=0, completion_tokens=0, latency=0.0, cached=False)

    async def chat_json(self, messages, schema, **kw):
        r = await self.chat(messages, json_schema=schema, **kw)
        return json.loads(r["text"]), r


class Words:
    def count(self, text):
        return len(text.split()) if text else 0

    def truncate(self, text, n):
        return " ".join(text.split()[:n]) if n > 0 else ""

    def keep_lines_within(self, lines, n, header=""):
        kept, total = [], self.count(header)
        for ln in reversed(lines):
            if total + self.count(ln) + 1 > n:
                break
            kept.append(ln)
            total += self.count(ln) + 1
        body = "\n".join(reversed(kept))
        if len(kept) < len(lines):
            body = f"(... {len(lines) - len(kept)} older entries dropped for budget ...)\n" + body
        return (header + "\n" + body) if header else body


def paraphrase_constants() -> dict[str, str]:
    """SYSTEM and JUDGE_SYSTEM from src/generation/paraphrase.py, read without importing the model client."""
    tree = ast.parse((ROOT / "src/generation/paraphrase.py").read_text())
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ("SYSTEM", "JUDGE_SYSTEM"):
            out[node.targets[0].id] = ast.literal_eval(node.value)
    return out


async def record(cond: str, dlg: dict, events) -> Recorder:
    rec = Recorder()
    mem = Memory(cond, dlg, rec, Words(), 384, events, hard_cap=True)
    probe = dlg["probes"][-1]
    for t in range(probe["after_turn"] + 1):
        await mem.observe(t)
        if t in dlg["compaction_after"]:
            await mem.compact(t)
    ctx = mem.context(probe["after_turn"], query=probe["text"])
    await decide(rec, ctx, probe)
    await state_query(rec, ctx, dlg["items"][probe["item"]]["vp"])
    return rec


def block(title: str, text: str) -> list[str]:
    return [f"### {title}", "", "```text", text, "```", ""]


def messages_block(title: str, call: dict) -> list[str]:
    out = [f"### {title}", "", f"max_tokens={call['max_tokens']}, temperature={call['temperature']}, "
           f"JSON schema: {'yes' if call['json_schema'] else 'no'}", ""]
    for m in call["messages"]:
        if m["role"] == "user":
            out += [f"**{m['role']}**", "", "```text", m["content"], "```", ""]
    return out


def build() -> str:
    tools = "\n".join(f"- {v}" for v in TOOLS.values())
    confirm = json.loads((ROOT / "data/confirm/dialogues.jsonl").read_text().splitlines()[0])
    test = [json.loads(line) for line in (ROOT / "data/dialogues/dialogues.jsonl").read_text().splitlines()]
    perfect, _ = noisy_gold_events(confirm)
    recs = {}
    for cond in ("summary", "summary_hint", "pinning", "pinning_hint", "chrono", "chrono_hint", "typed_llm", "lifecycle",
                 "lifecycle_nohint", "recent", "retrieval", "summary_retrieval", "full"):
        recs[cond] = asyncio.run(record(cond, confirm, perfect))
    extraction = {}
    for v in (1, 2):
        rec = Recorder()
        asyncio.run(extract_dialogue(rec, confirm, version=v))
        extraction[v] = rec.calls["extract"]
    para = paraphrase_constants()
    turn = next(t for d in test for t in d["turns"] if t["kind"] == "event" and t.get("template_text"))

    lines = ["# Prompts", "",
             "Every prompt the project sends to a model, written by `python -m src.eval.dump_prompts --out docs/prompts.md`. "
             "Do not edit by hand; `tests/test_core.py` checks that this file matches the code.", "",
             "System prompts are exactly as sent. Each user message is recorded from the code on the first Confirm "
             "dialogue (`C00_v0`, last decision point) with a stand-in model that returns placeholder answers, gold "
             "events, and a whitespace token counter. The wording and layout are the code's; the memory contents are an "
             "example. The two paraphrase user messages are built here with the same f-strings as `src/generation/paraphrase.py`, "
             "because that module needs a model server to import. All model calls use temperature 0 and seed 0, except "
             "paraphrasing (temperature 0.8, seed 0).", "",
             "## Decision policy and state question", ""]
    lines += block("Policy system prompt", POLICY_SYSTEM.format(tools=tools))
    lines += messages_block("Policy user message (example: LADL with gold events)", recs["lifecycle"].calls["policy"])
    lines += block("State question system prompt", STATE_SYSTEM)
    lines += messages_block("State question user message", recs["lifecycle"].calls["state_query"])
    lines += ["## Memory upkeep", ""]
    lines += block("Summary system prompt (`summary` and all conditions with a summary; {words} is filled per call)",
                   SUMMARY_SYSTEM)
    lines += block("Summary system prompt with action guidance (`summary_hint`)", SUMMARY_HINT_SYSTEM)
    lines += block("Action guidance text inserted in the hint prompts", ACTION_GUIDANCE)
    lines += messages_block("Summary user message", recs["summary"].calls["summary"])
    lines += block("Pinning system prompt (`pinning`)", PIN_SYSTEM)
    lines += block("Pinning system prompt with action guidance (`pinning_hint`)", PIN_HINT_SYSTEM)
    lines += messages_block("Pinning user message", recs["pinning"].calls["pin"])
    lines += block("LLM-written transitions system prompt (`typed_llm`)", TRANSITION_SYSTEM)
    lines += messages_block("LLM-written transitions user message", recs["typed_llm"].calls["transition"])
    lines += ["## Event extraction", ""]
    for v in (1, 2):
        lines += block(f"Extraction system prompt v{v}", EXTRACT_PROMPTS[v].format(tools=tools))
    lines += messages_block("Extraction user message (same for v1 and v2)", extraction[1])
    lines += ["## Memory text shown to the policy", "",
              "The policy sees memory inside the user message above. One example per condition family:", ""]
    for cond in ("chrono", "chrono_hint", "lifecycle", "lifecycle_nohint", "recent", "retrieval", "summary_retrieval"):
        user = recs[cond].calls["policy"]["messages"][1]["content"]
        memory = user.split("=== MEMORY ===\n", 1)[1].split("\n\n=== RECENT CONVERSATION ===", 1)[0]
        lines += block(f"`{cond}`", memory)
    lines += ["## Data generation (Test and dev dialogues)", ""]
    lines += block("Paraphrase system prompt (Llama-3.1-8B-Instruct, temperature 0.8)", para["SYSTEM"])
    lines += block("Paraphrase user message", f"Message (attempt 1):\n{turn['template_text']}")
    lines += block("Paraphrase judge system prompt (Qwen2.5-7B-Instruct)", para["JUDGE_SYSTEM"])
    lines += block("Paraphrase judge user message", f"Original: {turn['template_text']}\nParaphrase: {turn['text']}")
    lines += ["The Fresh, Confirm, and forged-update sets use no model: their text comes from templates in "
              "`src/generation/`.", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/prompts.md")
    a = ap.parse_args()
    Path(a.out).write_text(build())
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
