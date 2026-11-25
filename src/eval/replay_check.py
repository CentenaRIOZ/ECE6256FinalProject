"""Replay finished runs from the LLM cache with the current code and compare them with the stored outputs.

python -m src.eval.replay_check --out results/replay [--only confirm]

Each run is rerun with --cache-only, so no model server is needed. A cache miss means the current code sent a prompt the
original run never sent. A changed decision with zero misses means the code after the LLM calls changed. Smoke runs
are skipped. Run on the machine that holds the caches (PACE-ICE for all PACE runs).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sqlite3
from argparse import Namespace
from pathlib import Path

import pandas as pd

from src.eval.run import main_async

CONFIGS = {"qwen2.5-7b": "configs/qwen7b.yaml", "llama3.1-8b": "configs/llama8b.yaml", "mistral-7b-v0.3": "configs/mistral7b.yaml"}
# Earlier files win when two caches hold the same prompt, so a run's own cache comes before smoke caches.
CACHES = {"qwen2.5-7b": ["llm_qwen7b.sqlite"], "llama3.1-8b": ["llm_llama8b.sqlite"],
          "mistral-7b-v0.3": ["llm_mistral7b.sqlite", "llm_mistral7b_confirm.sqlite", "llm_mistral7b_smoke.sqlite"]}
FIELDS = ["pred_decision", "pred_label", "ledger_label", "memory_tokens", "summary_capped", "ledger_truncated",
          "prompt_tokens"]


def merged_cache(model: str, cache_dir: Path, work: Path) -> Path:
    dst = work / f"replay_{model}.sqlite"
    if dst.exists():
        return dst
    sources = [cache_dir / name for name in CACHES[model] if (cache_dir / name).exists()]
    first = sqlite3.connect(f"file:{sources[0]}?mode=ro", uri=True)
    out = sqlite3.connect(dst)
    first.backup(out)
    first.close()
    for extra in sources[1:]:
        out.execute("ATTACH DATABASE ? AS extra", (f"file:{extra}?mode=ro",))
        out.execute("INSERT OR IGNORE INTO c SELECT k, v FROM extra.c")
        out.commit()
        out.execute("DETACH DATABASE extra")
    out.close()
    return dst


def copied(caches: list[Path], work: Path) -> Path:
    """Merged copy of the given caches, so replaying never touches the originals. Earlier files win on a shared key,
    which only matters for runs made before deterministic serving."""
    dst = work / "replay_given_caches.sqlite"
    if not dst.exists():
        src = sqlite3.connect(f"file:{caches[0]}?mode=ro", uri=True)
        out = sqlite3.connect(dst)
        src.backup(out)
        src.close()
        for extra in caches[1:]:
            out.execute("ATTACH DATABASE ? AS extra", (f"file:{extra}?mode=ro",))
            out.execute("INSERT OR IGNORE INTO c SELECT k, v FROM extra.c")
            out.commit()
            out.execute("DETACH DATABASE extra")
        out.close()
    return dst


def spec(run_dir: Path, budget: int) -> dict:
    name = run_dir.name
    model = next(m for m in CONFIGS if name.startswith(m))
    meta = json.loads((run_dir / f"meta_B{budget}.json").read_text())
    if "confirm" in name:
        data = "data/confirm/dialogues.jsonl"
    elif m := re.search(r"fresh-(early|late)", name):
        data = f"data/fresh/dialogues_{m.group(1)}.jsonl"
    elif "fresh" in name:
        data = "data/fresh/dialogues_spread.jsonl"
    else:
        data = "data/dialogues/dialogues.jsonl"
    data = meta.get("args", {}).get("data", data)
    split = "dev" if "-dev-" in name else None
    return dict(model=model, name=name, budget=budget, data=data, split=split, conditions=meta["conditions"],
                hard_cap=meta.get("hard_cap", False), extract_version=meta.get("extract_version", 1),
                n_dialogues=meta["n_dialogues"])


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f]


def compare(original: Path, replay: Path, budget: int) -> dict:
    key = ["condition", "probe_id"]
    a = pd.DataFrame(read_jsonl(original / f"probes_B{budget}.jsonl")).set_index(key)
    b = pd.DataFrame(read_jsonl(replay / f"probes_B{budget}.jsonl")).set_index(key)
    common = a.index.intersection(b.index)
    a, b = a.loc[common], b.loc[common]
    out = dict(rows=len(a), replay_rows=len(b), matched=len(common))
    for field in FIELDS:
        same = [x == y or (pd.isna(x) and pd.isna(y)) for x, y in zip(a[field].tolist(), b[field].tolist())]
        out[f"diff_{field}"] = len(same) - sum(same)
    out["accuracy_original"] = float((a.pred_decision == a.gold_decision).mean())
    out["accuracy_replay"] = float((b.pred_decision == b.gold_decision).mean())
    if (original / "extractions.jsonl").exists() and (replay / "extractions.jsonl").exists():
        ea = {r["dialogue_id"]: r["events"] for r in read_jsonl(original / "extractions.jsonl")}
        eb = {r["dialogue_id"]: r["events"] for r in read_jsonl(replay / "extractions.jsonl")}
        out["extraction_dialogues_differing"] = sum(ea.get(k) != eb.get(k) for k in set(ea) | set(eb))
    usage = json.loads((replay / f"meta_B{budget}.json").read_text())["usage"]
    out["cache_misses"] = int(sum(v.get("cache_miss", 0) for v in usage.values()))
    out["llm_calls"] = int(sum(v.get("calls", 0) for v in usage.values()))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--cache-dir", default="cache")
    ap.add_argument("--out", default="results/replay")
    ap.add_argument("--only", help="replay only runs whose name contains this text")
    ap.add_argument("--cache-file", action="append",
                    help="replay from these caches instead of the model's default caches; repeat for several files")
    a = ap.parse_args()
    runs, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(os.environ.get("TMPDIR", "/tmp")) / f"replay_{os.getpid()}"
    work.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        for run_dir in sorted(p for p in runs.iterdir() if p.is_dir() and "smoke" not in p.name
                              and any(p.name.startswith(m) and "-pace-" in p.name for m in CONFIGS)):
            if a.only and a.only not in run_dir.name:
                continue
            for probes in sorted(run_dir.glob("probes_B*.jsonl")):
                budget = int(probes.stem.split("_B")[1])
                s = spec(run_dir, budget)
                replay_name = f"{s['name']}"
                target = out / replay_name
                args = Namespace(config=CONFIGS[s["model"]], conditions=",".join(s["conditions"]), split=s["split"],
                                 limit=None, data=s["data"], budget=budget,
                                 run_name=os.path.relpath(target, Path("results/runs")),
                                 cache=str(copied([Path(c) for c in a.cache_file], work) if a.cache_file
                                           else merged_cache(s["model"], Path(a.cache_dir), work)),
                                 hard_cap=s["hard_cap"],
                                 extract_version=s["extract_version"], cache_only=True, max_concurrency=None)
                asyncio.run(main_async(args))
                row = dict(run=s["name"], budget=budget, extract_version=s["extract_version"], **compare(run_dir, target, budget))
                rows.append(row)
                print(json.dumps(row), flush=True)
                pd.DataFrame(rows).to_csv(out / "replay_summary.csv", index=False)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    table = pd.DataFrame(rows)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
