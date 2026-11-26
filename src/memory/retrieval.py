"""BM25 over earlier turns and token-exact packing, for the retrieval baselines (docs/scale_retrieval_forgery_plan.md)."""
from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "can", "could", "do", "for", "from", "has", "have",
             "i", "if", "in", "is", "it", "its", "me", "my", "now", "of", "on", "or", "our", "please", "so", "that", "the",
             "their", "them", "then", "this", "to", "up", "us", "was", "we", "will", "with", "you", "your"}
K1, B = 1.5, 0.75


def terms(text: str) -> list[str]:
    """Lower-cased words and numbers (such as $3,750 or 2021), without stopwords or possessive 's."""
    words = (w.strip(".,'") for w in re.findall(r"[a-z0-9$][a-z0-9$,.']*", text.lower().replace("'s ", " ")))
    return [w for w in words if w and w not in STOPWORDS]


def bm25(query: str, docs: list[str]) -> list[float]:
    """Okapi BM25 score of each document for the query (k1 = 1.5, b = 0.75)."""
    toks = [terms(d) for d in docs]
    if not toks:
        return []
    avg = sum(map(len, toks)) / len(toks) or 1.0
    df = Counter(w for t in toks for w in set(t))
    n = len(toks)
    scores = []
    for t in toks:
        tf = Counter(t)
        s = 0.0
        for w in set(terms(query)):
            if w in tf:
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * tf[w] * (K1 + 1) / (tf[w] + K1 * (1 - B + B * len(t) / avg))
        scores.append(s)
    return scores


def pack(lines: list[tuple[int, str]], order: list[int], budget: int, header: str, count) -> str:
    """Add lines in the given priority order while the whole block stays within budget tokens; show them by turn."""
    chosen: list[tuple[int, str]] = []
    for i in order:
        trial = sorted(chosen + [lines[i]])
        if count(header + "\n" + "\n".join(text for _, text in trial)) <= budget:
            chosen = trial
    return header + "\n" + "\n".join(text for _, text in chosen) if chosen else ""


def retrieve(query: str, turns: list[dict], fmt, budget: int, header: str, count) -> str:
    """Earlier turns that share a term with the query, best first and later turns first on ties, packed to budget."""
    scores = bm25(query, [t["text"] for t in turns])
    lines = [(t["idx"], fmt(t)) for t in turns]
    order = [i for i in sorted(range(len(turns)), key=lambda i: (-scores[i], -turns[i]["idx"])) if scores[i] > 0]
    return pack(lines, order, budget, header, count)


def most_recent(turns: list[dict], fmt, budget: int, header: str, count) -> str:
    """The latest earlier turns, verbatim, as many as fit in budget."""
    lines = [(t["idx"], fmt(t)) for t in turns]
    order = list(range(len(turns) - 1, -1, -1))
    out, chosen = "", []
    for i in order:  # contiguous: stop at the first turn that does not fit
        trial = sorted(chosen + [lines[i]])
        text = header + "\n" + "\n".join(x for _, x in trial)
        if count(text) > budget:
            break
        chosen, out = trial, text
    return out
