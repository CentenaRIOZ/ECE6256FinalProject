"""Experiment A of docs/followup_experiments_plan.md: dialogue-level metrics and cost.

python -m src.eval.dialogue_report --runs results/runs_det --replays results/replay_followup/det_confirm \
    --out results/followup/dialogue

Dialogue metrics come from the deterministic runs. Tokens and calls per condition come from the cache-only replays of
the deterministic Confirm runs, which count usage per condition. Latency comes from the one-request-at-a-time runs
<model>-pace-latency-<condition>, which are skipped when missing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.confirm_report import PRIMARY
from src.eval.followup_settings import LATENCY_CONDITIONS
from src.eval.models import MODELS, available
from src.eval.replication_report import SOURCES, read_dataset
from src.eval.robustness import REPS, holm, load
from src.memory.managers import NEEDS_EXTRACTION

FLOOR = 2 / (REPS + 1)
FAMILIES = [("A1", "success", ["Qwen", "Llama"], True), ("A2", "success", ["Mistral"], False),
            ("A3", "safe", ["Qwen", "Llama"], True), ("A4", "safe", ["Mistral"], False)]
UPKEEP = ["extract", "pin", "summary", "transition"]  # memory upkeep calls; policy is the decision call


def dialogues(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (condition, dialogue): success, safe, and the 1-based position of the first wrong probe."""
    d = df.sort_values(["condition", "dialogue_id", "after_turn", "probe_id"]).copy()
    d["correct"] = d.pred_decision == d.gold_decision
    d["unsafe"] = (d.pred_decision == "act") & (d.gold_decision != "act")
    d["position"] = d.groupby(["condition", "dialogue_id"]).cumcount() + 1
    first = d[~d.correct].groupby(["condition", "dialogue_id"]).position.min().rename("first_error")
    out = d.groupby(["condition", "dialogue_id"]).agg(timeline_id=("timeline_id", "first"), n_probes=("probe_id", "size"),
                                                      success=("correct", "all"), unsafe=("unsafe", "any"))
    out = out.join(first)
    out["safe"] = ~out.unsafe
    return out.reset_index()


def rate_ci(frame: pd.DataFrame, col: str, seed: int = 0) -> tuple[float, float, float]:
    agg = frame.groupby("timeline_id")[col].agg(["sum", "size"])
    n, m = agg["sum"].to_numpy(float), agg["size"].to_numpy(float)
    idx = np.random.default_rng(seed).integers(0, len(n), size=(REPS, len(n)))
    boot = n[idx].sum(1) / m[idx].sum(1)
    return n.sum() / m.sum(), *np.percentile(boot, [2.5, 97.5])


def paired_rate_diff(frame: pd.DataFrame, a: str, b: str, col: str, seed: int = 0):
    """Rate(a) - rate(b) over the same dialogues, resampling timelines; same procedure as analyze.paired_diff."""
    parts = [frame[frame.condition == c].groupby("timeline_id")[col].agg(["sum", "size"]) for c in (a, b)]
    j = parts[0].join(parts[1], lsuffix="_a", rsuffix="_b", how="inner")
    idx = np.random.default_rng(seed).integers(0, len(j), size=(REPS, len(j)))
    A = j.sum_a.to_numpy(float)[idx].sum(1) / j.size_a.to_numpy(float)[idx].sum(1)
    B = j.sum_b.to_numpy(float)[idx].sum(1) / j.size_b.to_numpy(float)[idx].sum(1)
    diff = A - B
    point = j.sum_a.sum() / j.size_a.sum() - j.sum_b.sum() / j.size_b.sum()
    p = 2 * min((diff <= 0).mean(), (diff >= 0).mean())
    return point, *np.percentile(diff, [2.5, 97.5]), max(min(1.0, p), FLOOR)


def metrics_table(frames: dict[tuple[str, str], pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for (dataset, model), dlg in frames.items():
        for cond, x in dlg.groupby("condition"):
            s, s_lo, s_hi = rate_ci(x, "success")
            f, f_lo, f_hi = rate_ci(x, "safe")
            row = dict(dataset=dataset, model=model, condition=cond, dialogues=len(x), success=s, success_lo=s_lo,
                       success_hi=s_hi, safe=f, safe_lo=f_lo, safe_hi=f_hi,
                       mean_first_error=x.first_error.mean())
            for k in range(1, 5):
                has = x[x.n_probes >= k]
                row[f"clean_after_{k}"] = ((has.first_error.isna()) | (has.first_error > k)).mean()
            rows.append(row)
    return pd.DataFrame(rows)


def planned_tests(confirm: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for name, col, models, directional in FAMILIES:
        family = []
        for model in models:
            if model not in confirm:
                continue
            for a, b in PRIMARY:
                diff, lo, hi, p = paired_rate_diff(confirm[model], a, b, col)
                family.append(dict(family=name, metric=col, model=model, a=a, b=b, diff=diff, lo=lo, hi=hi, p=p,
                                   prediction="positive" if directional else "two-sided"))
        for row, adjusted in zip(family, holm(np.array([r["p"] for r in family]))):
            row["p_holm"] = adjusted
            row["result"] = bool(adjusted < 0.05 and (row["diff"] > 0 or not directional))
        rows += family
    return pd.DataFrame(rows)


def cost_table(root: Path, replays: Path) -> pd.DataFrame:
    rows = []
    for model, run in MODELS.items():
        for version in ("v1", "v2"):
            replay = replays / run / f"{run}-det1-pace-confirm-{version}"
            meta_path = replay / "meta_B384.json"
            if not meta_path.exists():
                continue
            meta = json.loads(meta_path.read_text())
            by_cond = meta["usage_by_condition"]
            probes = load(str(root / f"{run}-pace-confirm-{version}"), 384)
            n = meta["n_dialogues"]
            for cond in meta["conditions"]:
                usage = {tag: dict(v) for tag, v in by_cond.get(cond, {}).items()}
                if cond in NEEDS_EXTRACTION:
                    usage["extract"] = by_cond["_extraction"]["extract"]
                agent = {tag: v for tag, v in usage.items() if tag != "state_query"}
                p = probes[probes.condition == cond]
                compacted = p[p.compactions_before_probe > 0]
                row = dict(model=model, extraction=version, condition=cond,
                           calls=sum(v["calls"] for v in agent.values()) / n,
                           prompt_tokens=sum(v["prompt_tokens"] for v in agent.values()) / n,
                           completion_tokens=sum(v["completion_tokens"] for v in agent.values()) / n,
                           upkeep_calls=sum(agent.get(t, {}).get("calls", 0) for t in UPKEEP) / n,
                           upkeep_tokens=sum(agent.get(t, {}).get("prompt_tokens", 0)
                                             + agent.get(t, {}).get("completion_tokens", 0) for t in UPKEEP) / n,
                           decision_prompt_tokens=p.prompt_tokens.mean(), memory_tokens=compacted.memory_tokens.mean(),
                           state_query_tokens=sum(usage.get("state_query", {}).get(k, 0)
                                                  for k in ("prompt_tokens", "completion_tokens")) / n,
                           cache_misses=sum(v.get("cache_miss", 0) for v in usage.values()))
                for tag in UPKEEP + ["policy"]:
                    row[f"calls_{tag}"] = agent.get(tag, {}).get("calls", 0) / n
                rows.append(row)
    return pd.DataFrame(rows)


def latency_table(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Seconds per dialogue, decision, and user turn; and whether decisions match the deterministic Confirm run."""
    rows, checks = [], []
    data = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open("data/confirm/dialogues.jsonl")}
    for model, run in MODELS.items():
        for cond in LATENCY_CONDITIONS:
            path = root / f"{run}-pace-latency-{cond}"
            if not (path / "meta_B384.json").exists():
                continue
            meta = json.loads((path / "meta_B384.json").read_text())
            usage = {tag: dict(v) for tag, v in meta["usage"].items()}
            probes = load(str(path), 384)
            ids = probes.dialogue_id.unique()
            turns = sum(t["role"] in ("user", "tool") for i in ids for t in data[i]["turns"])
            agent = sum(v["latency"] for tag, v in usage.items() if tag != "state_query")
            policy = usage.get("policy", {})
            rows.append(dict(model=model, condition=cond, dialogues=len(ids), decisions=len(probes),
                             seconds_per_dialogue=agent / len(ids),
                             seconds_per_decision=policy.get("latency", 0) / max(1, policy.get("calls", 0)),
                             upkeep_seconds_per_turn=sum(usage.get(t, {}).get("latency", 0) for t in UPKEEP) / turns,
                             state_query_seconds_per_dialogue=usage.get("state_query", {}).get("latency", 0) / len(ids),
                             cached_calls=sum(v.get("cached", 0) for v in usage.values()),
                             max_concurrency=meta["args"]["max_concurrency"], gpu=meta.get("gpu")))
            ref = load(str(root / f"{run}-pace-confirm-v1"), 384)
            ref = ref[(ref.condition == cond) & ref.dialogue_id.isin(ids)].set_index("probe_id")
            mine = probes.set_index("probe_id")
            same = (mine.pred_decision == ref.pred_decision.reindex(mine.index)).sum()
            checks.append(dict(model=model, condition=cond, probes=len(mine), same_decision_as_det_run=int(same)))
    return pd.DataFrame(rows), pd.DataFrame(checks)


def pct(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    out[cols] = (out[cols].astype(float) * 100).round(1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_det")
    ap.add_argument("--replays", default="results/replay_followup/det_confirm")
    ap.add_argument("--out", default="results/followup/dialogue")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = {}
    for dataset, (base, hints, v2) in SOURCES.items():
        for model, run in available(root, [s for s in (base, hints, v2) if s]).items():
            frames[(dataset, model)] = dialogues(read_dataset(root, run, base, hints, v2))
    metrics = metrics_table(frames)
    tests = planned_tests({m: f for (d, m), f in frames.items() if d == "Confirm"})
    cost = cost_table(root, Path(a.replays))
    latency, latency_check = latency_table(root)
    metrics.to_csv(out / "dialogue_metrics.csv", index=False)
    tests.to_csv(out / "dialogue_tests.csv", index=False)
    cost.to_csv(out / "cost.csv", index=False)
    latency.to_csv(out / "latency.csv", index=False)
    latency_check.to_csv(out / "latency_decision_check.csv", index=False)
    rate_cols = [c for c in metrics.columns if c.startswith(("success", "safe", "clean_after"))]
    show_tests = pct(tests, ["diff", "lo", "hi"])
    show_tests[["p", "p_holm"]] = show_tests[["p", "p_holm"]].round(4)
    text = ["# Dialogue-level metrics and cost", "", "Planned tests follow docs/followup_experiments_plan.md.", "",
            "## Planned tests on Confirm", "", show_tests.to_markdown(index=False), "",
            "## Dialogue metrics", "", pct(metrics, rate_cols).round(2).to_markdown(index=False), "",
            "## Tokens and calls per dialogue (state queries excluded)", "", cost.round(1).to_markdown(index=False), ""]
    if len(latency):
        text += ["## Latency, one request at a time", "", latency.round(3).to_markdown(index=False), "",
                 "## Latency runs against the deterministic Confirm run", "", latency_check.to_markdown(index=False), ""]
    (out / "report.md").write_text("\n".join(text))
    print(show_tests.to_string(index=False))


if __name__ == "__main__":
    main()
