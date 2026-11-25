"""Run memory conditions over dialogues and score decisions at probe checkpoints.

python -m src.eval.run --config configs/qwen7b.yaml [--conditions summary,lifecycle] [--split test] [--limit 10]
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import yaml

from src.extraction.extractor import extract_dialogue, gold_events
from src.llm.client import LLM, TokenCounter, model_revision
from src.memory.managers import CONDITIONS, LEDGER_CONDS, Memory
from src.policy.policy import decide, state_query

NEEDS_EXTRACTION = {"chrono", "typed_llm", "lifecycle", "abl_noguard", "abl_noreceipt", "lifecycle_strict",
                    "lifecycle_nohint", "chrono_hint"}


def load_dialogues(path: str, split: str | None, limit: int | None) -> list[dict]:
    ds = [json.loads(l) for l in open(path)]
    if split and split != "all":
        ds = [d for d in ds if d["split"] == split]
    return ds[:limit] if limit else ds


async def run_one(cond: str, dlg: dict, llm, tc, budget: int, events, hard_cap: bool = False) -> list[dict]:
    mem = Memory(cond, dlg, llm, tc, budget, events, hard_cap=hard_cap)
    comp = set(dlg["compaction_after"])
    by_t: dict[int, list] = {}
    for p in dlg["probes"]:
        by_t.setdefault(p["after_turn"], []).append(p)
    rows = []
    for t in range(len(dlg["turns"])):
        await mem.observe(t)
        if t in comp:
            await mem.compact(t)
        for p in by_t.get(t, []):
            ctx = mem.context(t)
            item = dlg["items"][p["item"]]
            d, s = await asyncio.gather(decide(llm, ctx, p), state_query(llm, ctx, item["vp"]))
            led_label, led_item = mem.ledger_label_for(item)
            rows.append(dict(
                condition=cond, dialogue_id=dlg["dialogue_id"], timeline_id=dlg["timeline_id"], split=dlg["split"],
                variant=dlg["variant"], n_compactions=dlg["n_compactions"], paraphrased=dlg.get("paraphrased", False),
                **{k: v for k, v in p.items() if k not in ("gold_statuses",)},
                tool=item["tool"], pred_decision=d["decision"], pred_reason=d["reason"], pred_label=s,
                ledger_label=led_label, ledger_item=led_item, ledger_truncated=ctx["truncated"],
                memory_tokens=ctx["memory_tokens"], summary_capped=ctx["summary_capped"],
                prompt_tokens=d["prompt_tokens"], latency=d["latency"],
                summary=mem.summary if p is dlg["probes"][-1] else None,
            ))
    return rows


def code_fingerprint() -> dict:
    """Identifies the code that produced a run, also on machines where the project is not a git checkout."""
    root = Path(__file__).resolve().parents[2]
    files = sorted(p for p in (root / "src").rglob("*.py"))
    digest = hashlib.sha256()
    for p in files:
        digest.update(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() + b"\0")
    try:
        commit = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", "src"],
                                    capture_output=True, text=True).stdout.strip())
    except Exception:
        commit, dirty = "", None
    # Only the project modules this run imported; tools and reports elsewhere in src/ do not change it.
    loaded = sorted(Path(m.__file__).resolve() for name, m in list(sys.modules.items())
                    if name.startswith("src.") and getattr(m, "__file__", None))
    run_digest = hashlib.sha256()
    for p in loaded:
        run_digest.update(str(p.relative_to(root)).encode() + b"\0" + p.read_bytes() + b"\0")
    return dict(src_sha256=digest.hexdigest(), n_files=len(files), git_commit=commit or None, src_dirty=dirty,
                run_sha256=run_digest.hexdigest(), run_files=[str(p.relative_to(root)) for p in loaded])


def server_version(base_url: str) -> str | None:
    import urllib.request
    try:
        with urllib.request.urlopen(base_url.rsplit("/v1", 1)[0] + "/version", timeout=5) as r:
            return json.loads(r.read()).get("version")
    except Exception:
        return None


def gpu_info() -> str:
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                              capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


async def main_async(args):
    cfg = yaml.safe_load(open(args.config))
    conds = args.conditions.split(",") if args.conditions else cfg.get("conditions", CONDITIONS)
    unknown = set(conds) - set(CONDITIONS)
    assert not unknown, f"unknown conditions {unknown}"
    out = Path(cfg["out_dir"]) / (args.run_name or cfg["run_name"])
    out.mkdir(parents=True, exist_ok=True)
    dlgs = load_dialogues(args.data or cfg["data"], args.split or cfg.get("split"), args.limit)
    llm = LLM(cfg["model"], cfg["base_url"], args.cache or cfg.get("cache", "cache/llm.sqlite"),
              args.max_concurrency or cfg.get("max_concurrency", 128), cache_only=args.cache_only)
    tc = TokenCounter(cfg.get("tokenizer", cfg["model"]))
    budget = int(args.budget or cfg["budget"])
    t0 = time.time()

    # ---- stage 1: per-turn extraction (shared by all extraction-based conditions)
    extractions = {}
    if NEEDS_EXTRACTION & set(conds):
        ex_path = out / "extractions.jsonl"
        res = await asyncio.gather(*[extract_dialogue(llm, d, version=args.extract_version) for d in dlgs])
        with ex_path.open("w") as f:
            for d, ev in zip(dlgs, res):
                extractions[d["dialogue_id"]] = ev
                f.write(json.dumps(dict(dialogue_id=d["dialogue_id"], events=ev)) + "\n")
        print(f"[extract] {len(dlgs)} dialogues in {time.time() - t0:.0f}s", flush=True)

    # ---- stage 2: conditions
    done = 0
    total = len(conds) * len(dlgs)
    probes_path = out / f"probes_B{budget}.jsonl"

    async def task(cond, d):
        nonlocal done
        if cond in NEEDS_EXTRACTION:
            ev = extractions[d["dialogue_id"]]
        elif cond == "lifecycle_gold":
            ev = gold_events(d)
        else:
            ev = None
        rows = await run_one(cond, d, llm, tc, budget, ev, hard_cap=args.hard_cap)
        done += 1
        if done % 50 == 0 or done == total:
            print(f"[run] {done}/{total} dialogue-conditions ({time.time() - t0:.0f}s)", flush=True)
        return rows

    results = await asyncio.gather(*[task(c, d) for c in conds for d in dlgs])
    with probes_path.open("w") as f:
        for rows in results:
            for r in rows:
                f.write(json.dumps(r) + "\n")
    llm.close()
    meta = dict(config=cfg, conditions=conds, budget=budget, hard_cap=args.hard_cap, extract_version=args.extract_version,
                n_dialogues=len(dlgs),
                args=dict(data=args.data or cfg["data"], split=args.split or cfg.get("split"), limit=args.limit,
                          cache=args.cache or cfg.get("cache"), cache_only=args.cache_only,
                          max_concurrency=args.max_concurrency or cfg.get("max_concurrency", 128)),
                code=code_fingerprint(), model_revision=model_revision(cfg["model"]),
                server_version=None if args.cache_only else server_version(cfg["base_url"]),
                wall_seconds=time.time() - t0,
                gpu=gpu_info(), usage={k: dict(v) for k, v in llm.stats.items()})
    (out / f"meta_B{budget}.json").write_text(json.dumps(meta, indent=1))
    print(f"wrote {probes_path} ({sum(map(len, results))} rows) in {time.time() - t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--conditions")
    ap.add_argument("--split")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--data")
    ap.add_argument("--budget", type=int)
    ap.add_argument("--run-name")
    ap.add_argument("--cache", help="override the config's LLM cache path")
    ap.add_argument("--hard-cap", action="store_true", help="enforce summary + persistent block <= budget at every probe")
    ap.add_argument("--extract-version", type=int, choices=[1, 2], default=1)
    ap.add_argument("--max-concurrency", type=int, help="override the config's number of concurrent requests")
    ap.add_argument("--cache-only", action="store_true",
                    help="replay from the cache without calling the server; misses are counted in meta usage")
    asyncio.run(main_async(ap.parse_args()))


if __name__ == "__main__":
    main()
