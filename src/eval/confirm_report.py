"""Confirmation analysis for the post-milestone new-language set.

python -m src.eval.confirm_report --out results/confirm

The two-model tests follow docs/post_milestone_confirmation_plan.md. Mistral tests follow docs/third_model_plan.md and
are corrected in their own families, so adding Mistral does not change the two-model results. Mistral is skipped when its
runs are missing.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import cluster_boot, paired_diff
from src.eval.error_analysis import attribution_shares, gold_error_counts, guard_counts, read_jsonl
from src.eval.extraction_eval import evaluate
from src.eval.robustness import REPS, binary, holm, load

TWO_MODELS = {"Qwen2.5-7B-Instruct": ("Qwen", "qwen2.5-7b"), "Llama-3.1-8B-Instruct": ("Llama", "llama3.1-8b")}
THIRD_MODEL = {"Mistral-7B-Instruct-v0.3": ("Mistral", "mistral-7b-v0.3")}
MODELS = dict(TWO_MODELS)
DATA = "data/confirm/dialogues.jsonl"
PRIMARY = [("lifecycle", "summary_hint"), ("lifecycle", "pinning_hint"), ("lifecycle", "chrono_hint"),
           ("lifecycle", "typed_llm")]
SECONDARY = [("lifecycle", "summary"), ("lifecycle", "pinning"), ("lifecycle", "chrono"), ("lifecycle", "lifecycle_nohint"),
             ("lifecycle_v2", "lifecycle"), ("lifecycle_strict", "lifecycle")]
# Planned for Mistral only. For Qwen and Llama the same tests are reported as exploratory.
V2_FAMILY = [("lifecycle_v2", b) for b in
             ("summary", "summary_hint", "pinning", "pinning_hint", "chrono_v2", "chrono_hint_v2", "typed_llm_v2")]
ORDER = ["full", "summary", "summary_hint", "pinning", "pinning_hint", "chrono", "chrono_hint", "typed_llm", "lifecycle",
         "lifecycle_nohint", "lifecycle_strict", "lifecycle_gold", "abl_noguard", "abl_noreceipt"]
FLOOR = 2 / (REPS + 1)


def read_runs(root: Path) -> pd.DataFrame:
    frames = []
    for _, run in MODELS.values():
        v1 = load(str(root / f"{run}-pace-confirm-v1"), 384)
        v2 = load(str(root / f"{run}-pace-confirm-v2"), 384)
        v2["condition"] = v2.condition + "_v2"
        frames += [v1, v2]
    return pd.concat(frames, ignore_index=True)


def family(df: pd.DataFrame, tests: list[tuple[str, str]], name: str, metric: str, models: dict | None = None,
           planned: bool = True) -> list[dict]:
    """Holm correction runs over every test in one call, across the given models."""
    frame = binary(df) if metric == "execute" else df
    rows = []
    for model, (label, _) in (models or TWO_MODELS).items():
        sub = frame[frame.model == model]
        for a, b in tests:
            diff, lo, hi, p = paired_diff(sub, a, b, "accuracy", reps=REPS)
            rows.append(dict(family=name, planned=planned, metric=metric, model=label, a=a, b=b, diff=diff, lo=lo, hi=hi,
                             p=max(p, FLOOR)))
    for row, adjusted in zip(rows, holm(np.array([r["p"] for r in rows]))):
        row["p_holm"] = adjusted
        row["confirmed"] = bool(row["diff"] > 0 and adjusted < 0.05)
    return rows


def accuracy_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model, (label, _) in MODELS.items():
        sub = df[df.model == model]
        for condition in sorted(sub.condition.unique()):
            d = sub[sub.condition == condition]
            acc, lo, hi = cluster_boot(d, "accuracy")
            execute, ex_lo, ex_hi = cluster_boot(binary(d), "accuracy")
            compacted = d[d.compactions_before_probe > 0]
            rows.append(dict(model=label, condition=condition, n=len(d), accuracy=acc, lo=lo, hi=hi, execute=execute,
                             execute_lo=ex_lo, execute_hi=ex_hi, memory_tokens=compacted.memory_tokens.mean(),
                             max_tokens=compacted.memory_tokens.max(), invalid=(d.pred_decision == "invalid").mean()))
    return pd.DataFrame(rows)


def extraction_table(root: Path, dialogues: dict) -> pd.DataFrame:
    rows = []
    for _, (label, run) in MODELS.items():
        for version in ("v1", "v2"):
            path = root / f"{run}-pace-confirm-{version}"
            extracted = {r["dialogue_id"]: r["events"] for r in read_jsonl(path / "extractions.jsonl")}
            quality = evaluate({k: dialogues[k] for k in extracted},
                               [dict(dialogue_id=k, events=v) for k, v in extracted.items()])
            probes = pd.DataFrame(read_jsonl(path / "probes_B384.jsonl"))
            shares = attribution_shares(probes, "lifecycle", dialogues, extracted)
            rows.append(dict(model=label, extraction=version, f1=quality["f1"], approve_f1=quality["per_op"]["approve"]["f1"],
                             ladl_bad_extraction=shares.get("bad extraction", 0.0),
                             ladl_wrong_action=shares.get("wrong action | correct state", 0.0),
                             **guard_counts(probes[probes.condition == "lifecycle"])))
    return pd.DataFrame(rows)


def gold_table(root: Path) -> pd.DataFrame:
    rows = []
    for _, (label, run) in MODELS.items():
        probes = pd.DataFrame(read_jsonl(root / f"{run}-pace-confirm-v1" / "probes_B384.jsonl"))
        rows.append(dict(model=label, **gold_error_counts(probes)))
    return pd.DataFrame(rows)


def pct(table: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = table.copy()
    out[columns] = (out[columns].astype(float) * 100).round(1)
    return out


def planned_tests(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All test families for the runs under root, and the probe table they were computed from."""
    MODELS.clear()
    MODELS.update(TWO_MODELS)
    third = all((root / f"{run}-pace-confirm-{v}" / "probes_B384.jsonl").exists() for _, run in THIRD_MODEL.values()
                for v in ("v1", "v2"))
    if third:
        MODELS.update(THIRD_MODEL)
    df = read_runs(root)
    rows = []
    for metric in ("four_way", "execute"):
        rows += family(df, PRIMARY, "primary", metric) + family(df, SECONDARY, "secondary", metric)
        if third:
            rows += (family(df, PRIMARY, "third primary", metric, THIRD_MODEL)
                     + family(df, V2_FAMILY, "third v2", metric, THIRD_MODEL)
                     + family(df, SECONDARY, "third secondary", metric, THIRD_MODEL))
        rows += family(df, V2_FAMILY, "two-model v2", metric, planned=False)
    return pd.DataFrame(rows), df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--out", default="results/confirm")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dialogues = {r["dialogue_id"]: r for r in read_jsonl(Path(DATA))}
    tests, df = planned_tests(root)
    accuracy = accuracy_table(df)
    extraction = extraction_table(root, dialogues)
    gold = gold_table(root)
    tables = dict(tests=tests, accuracy=accuracy, extraction=extraction, gold_errors=gold)
    for name, table in tables.items():
        table.to_csv(out / f"{name}.csv", index=False)

    accuracy_view = pct(accuracy, ["accuracy", "lo", "hi", "execute", "execute_lo", "execute_hi", "invalid"]).round({"memory_tokens": 0})
    tests_view = pct(tests, ["diff", "lo", "hi"]).round({"p": 4, "p_holm": 4})
    extraction_view = pct(extraction, ["ladl_bad_extraction", "ladl_wrong_action"]).round({"f1": 3, "approve_f1": 3})
    gold_view = pct(gold, ["gold_error_rate"])
    sections = [("Accuracy", accuracy_view), ("Planned tests", tests_view), ("Extraction and LADL errors", extraction_view),
                ("Errors with gold events", gold_view)]
    text = ["# Post-milestone confirmation results\n",
            "Rules: `docs/post_milestone_confirmation_plan.md` (Qwen, Llama) and `docs/third_model_plan.md` (Mistral). "
            "Rows with `planned` False are exploratory.\n"]
    for title, table in sections:
        text += [f"## {title}\n", table.to_markdown(index=False), ""]
    (out / "report.md").write_text("\n".join(text))
    for title, table in sections:
        print(f"\n{title}\n{table.to_string(index=False)}")


if __name__ == "__main__":
    main()
