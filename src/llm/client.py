"""Async client for any OpenAI-compatible server (vLLM locally or on PACE-ICE), with an on-disk
response cache (reproducibility + cheap reruns), JSON-schema constrained decoding, and usage stats."""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from openai import AsyncOpenAI


class Cache:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), timeout=300)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS c (k TEXT PRIMARY KEY, v TEXT)")
        self._pending = 0

    def get(self, k: str):
        r = self.db.execute("SELECT v FROM c WHERE k=?", (k,)).fetchone()
        return json.loads(r[0]) if r else None

    def put(self, k: str, v: dict):
        self.db.execute("INSERT OR REPLACE INTO c VALUES (?,?)", (k, json.dumps(v)))
        self._pending += 1
        if self._pending >= 200:
            self.db.commit()
            self._pending = 0

    def close(self):
        self.db.commit()
        self.db.close()


class LLM:
    def __init__(self, model: str, base_url: str = "http://localhost:8000/v1", cache_path: str = "cache/llm.sqlite",
                 max_concurrency: int = 128, api_key: str | None = None, timeout: float = 300):
        self.model = model
        self.client = AsyncOpenAI(base_url=base_url, api_key=api_key or os.environ.get("OPENAI_API_KEY", "EMPTY"),
                                  timeout=timeout, max_retries=3)
        self.cache = Cache(cache_path)
        self.sem = asyncio.Semaphore(max_concurrency)
        self.stats = defaultdict(lambda: defaultdict(float))  # tag -> counters

    async def chat(self, messages: list[dict], *, tag: str = "", max_tokens: int = 512, temperature: float = 0.0,
                   json_schema: dict | None = None) -> dict:
        payload = dict(model=self.model, messages=messages, max_tokens=max_tokens, temperature=temperature,
                       schema=json_schema)
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        hit = self.cache.get(key)
        if hit is None:
            kw = {}
            if json_schema is not None:
                kw["response_format"] = {"type": "json_schema",
                                         "json_schema": {"name": "out", "schema": json_schema, "strict": True}}
            async with self.sem:
                t0 = time.perf_counter()
                r = await self.client.chat.completions.create(model=self.model, messages=messages, max_tokens=max_tokens,
                                                              temperature=temperature, seed=0, **kw)
                lat = time.perf_counter() - t0
            hit = dict(text=r.choices[0].message.content or "", prompt_tokens=r.usage.prompt_tokens,
                       completion_tokens=r.usage.completion_tokens, latency=lat)
            self.cache.put(key, hit)
            cached = False
        else:
            cached = True
        s = self.stats[tag]
        s["calls"] += 1
        s["cached"] += cached
        s["prompt_tokens"] += hit["prompt_tokens"]
        s["completion_tokens"] += hit["completion_tokens"]
        s["latency"] += hit["latency"]
        return dict(hit, cached=cached)

    async def chat_json(self, messages: list[dict], schema: dict, **kw) -> tuple[dict | None, dict]:
        r = await self.chat(messages, json_schema=schema, **kw)
        return parse_json(r["text"]), r

    def close(self):
        self.cache.close()


def parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
    return None


class TokenCounter:
    """Counts/truncates with the action model's own tokenizer (falls back to whitespace)."""

    def __init__(self, model: str):
        try:
            from transformers import AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(model)
        except Exception:
            self.tok = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        return len(self.tok.encode(text, add_special_tokens=False)) if self.tok else len(text.split())

    def truncate(self, text: str, n: int) -> str:
        if n <= 0:
            return ""
        if self.tok is None:
            return " ".join(text.split()[:n])
        ids = self.tok.encode(text, add_special_tokens=False)
        return text if len(ids) <= n else self.tok.decode(ids[:n])

    def keep_lines_within(self, lines: list[str], n: int, header: str = "") -> str:
        """Keep the newest lines whose total fits in n tokens (drops oldest first)."""
        kept, total = [], self.count(header)
        for ln in reversed(lines):
            c = self.count(ln) + 1
            if total + c > n:
                break
            kept.append(ln)
            total += c
        dropped = len(lines) - len(kept)
        body = "\n".join(reversed(kept))
        if dropped:
            body = f"(... {dropped} older entries dropped for budget ...)\n" + body
        return (header + "\n" + body) if header else body
