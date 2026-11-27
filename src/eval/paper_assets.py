"""All paper and poster figures and LaTeX tables, from the deterministic runs.

python -m src.eval.paper_assets --runs results/runs_det --out paper

Writes paper/figures/*.pdf and paper/tables/*.tex (listed in README under "Figures and tables"). Every number comes from
the run directories under --runs; nothing is typed in by hand. Accuracy intervals resample the 52 Confirm (or 48 Test)
timelines with 2,000 resamples and seed 0, as in the reports. Event conditions use extraction v2 unless marked v1.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import COLORS, attribute, cluster_boot, metric_fns, recall_error_type, setup_mpl
from src.eval.confirm_report import planned_tests
from src.eval.dialogue_report import cost_table, dialogues, latency_table, rate_ci
from src.eval.extraction_eval import evaluate
from src.eval.followup_report import experiment_b, experiment_c
from src.eval.models import MODELS
from src.eval.robustness import load
from src.eval.scale_report import ALL, LARGE, analyses_g, clean_frame, scale_figure, accuracy_table, v2

NAME = {"full": "Full history (reference)", "summary": "Ordinary compaction", "summary_hint": "Compaction + hints",
        "pinning": "Constraint pinning", "pinning_hint": "Pinning + hints", "recent": "Recent turns, verbatim",
        "retrieval": "BM25 retrieval", "summary_retrieval": "Compaction + retrieval",
        "chrono_v2": "Chronological ledger", "chrono_hint_v2": "Chronological + hints",
        "typed_llm_v2": "LLM-written transitions", "lifecycle": "LADL, extraction v1", "lifecycle_v2": "LADL (ours)",
        "lifecycle_nohint_v2": "LADL without hints", "lifecycle_source_v2": "LADL + speaker check",
        "lifecycle_gold": "LADL, gold events", "abl_noguard": "LADL v1 without guard logic",
        "abl_noreceipt": "LADL v1 without receipt evidence", "lifecycle_strict": "LADL v1, strict hedging (post hoc)",
        "lifecycle_nohint": "LADL v1 without hints", "chrono": "Chronological ledger, v1",
        "chrono_hint": "Chronological + hints, v1", "typed_llm": "LLM-written transitions, v1"}
MAIN = ["full", "summary", "summary_hint", "pinning", "pinning_hint", "recent", "retrieval", "summary_retrieval",
        "chrono_v2", "chrono_hint_v2", "typed_llm_v2", "lifecycle", "lifecycle_v2", "lifecycle_nohint_v2", "lifecycle_gold"]
SMALL = list(MODELS)  # Qwen, Llama, Mistral (7-8B)
SIZE_NAME = {"Qwen": "Qwen2.5-7B", "Llama": "Llama-3.1-8B", "Mistral": "Mistral-7B", "Qwen-14B": "Qwen2.5-14B",
             "Qwen-32B": "Qwen2.5-32B", "Mistral-24B": "Mistral-Small-24B"}
DATA = {"Confirm": "data/confirm/dialogues.jsonl", "Test": "data/dialogues/dialogues.jsonl"}


PREVIEW: Path | None = None  # set by --preview: PNG copies of every figure, for checking and for the poster


def save(fig, path: Path):
    fig.savefig(path)
    if PREVIEW is not None:
        fig.savefig(PREVIEW / path.with_suffix(".png").name, dpi=150)


def color(cond: str) -> str:
    return COLORS.get(cond.replace("_v2", ""), "#555555")


# ------------------------------------------------------------------------------------------ data
def test_frame(root: Path, label: str) -> pd.DataFrame | None:
    run = MODELS[label]
    parts = ["-pace-hardcap", "-pace-replicate-test-hints", "-pace-replicate-test-v2", "-pace-test-new"]
    if not all((root / f"{run}{p}" / "probes_B384.jsonl").exists() for p in parts):
        return None
    frames = [load(str(root / f"{run}{p}"), 384) for p in parts]
    frames[2] = v2(frames[2])
    out = pd.concat(frames, ignore_index=True).assign(cell="clean")
    return out.drop_duplicates(["condition", "probe_id"])


def accuracy_rows(frames: dict[str, pd.DataFrame], conds: list[str]) -> pd.DataFrame:
    rows = []
    for label, f in frames.items():
        for c in conds:
            d = f[f.condition == c]
            if len(d):
                v, lo, hi = cluster_boot(d, "accuracy")
                rows.append(dict(model=label, condition=c, accuracy=v, lo=lo, hi=hi))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ latex helpers
def pc(x) -> str:
    return "--" if x is None or pd.isna(x) else f"{100 * x:.1f}"


def ci(v, lo, hi) -> str:
    return f"{pc(v)} {{\\scriptsize [{pc(lo)}, {pc(hi)}]}}"


def diff_ci(r) -> str:
    return f"{100 * r['diff']:+.1f} {{\\scriptsize [{100 * r['lo']:+.1f}, {100 * r['hi']:+.1f}]}}"


def tabular(header: list[str], rows: list[list[str]], align: str | None = None) -> str:
    align = align or "l" + "r" * (len(header) - 1)
    out = [f"\\begin{{tabular}}{{{align}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in rows]
    return "\n".join(out + ["\\bottomrule", "\\end{tabular}", ""])


# ------------------------------------------------------------------------------------------ figures
def fig_accuracy(acc: pd.DataFrame, conds: list[str], out: Path, name: str, dataset: str):
    plt = setup_mpl()
    models = [m for m in SMALL if m in set(acc.model)]
    conds = [c for c in conds if c in set(acc.condition)]
    fig, axes = plt.subplots(1, len(models), figsize=(3.0 * len(models), 0.26 * len(conds) + 1.1), sharey=True,
                             squeeze=False)
    for ax, m in zip(axes[0], models):
        s = acc[acc.model == m].set_index("condition")
        for i, c in enumerate(conds):
            if c not in s.index:
                continue
            v, lo, hi = s.loc[c, ["accuracy", "lo", "hi"]]
            ax.barh(i, v, color=color(c), height=0.64, hatch="///" if c in ("full", "lifecycle_gold") else None,
                    edgecolor="#fcfcfb", linewidth=0, alpha=1.0 if c == "lifecycle_v2" else 0.85)
            ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], color="#0b0b0b", capsize=1.5, lw=0.8)
            ax.text(hi + 0.01, i, f"{100 * v:.1f}", va="center", fontsize=7, color="#0b0b0b")
        ax.set_yticks(range(len(conds)), [NAME[c] for c in conds], fontsize=7.5)
        ax.set_xlim(0.4, 1.0)
        ax.set_title(SIZE_NAME[m], fontsize=9, color="#0b0b0b")
        ax.set_xlabel(f"Action accuracy, {dataset} (95% CI)", fontsize=8)
        ax.grid(axis="y", visible=False)
    axes[0][0].invert_yaxis()
    fig.tight_layout()
    save(fig, out / name)
    plt.close(fig)


def fig_decay(decay: pd.DataFrame, out: Path):
    plt = setup_mpl()
    conds = ["full", "summary", "pinning", "chrono_hint", "lifecycle_v2"]
    d = decay[(decay.dataset == "Confirm") & decay.condition.isin(conds)]
    fig, axes = plt.subplots(1, len(SMALL), figsize=(7.2, 2.9), sharey=True)
    for ax, m in zip(axes, SMALL):
        s = d[d.model == m]
        for c in conds:
            x = s[s.condition == c].sort_values("compactions_since_change")
            ax.plot(x.compactions_since_change, x.accuracy, marker="o", ms=3, lw=1.4, color=color(c),
                    ls="--" if c == "full" else "-", label=NAME.get(c, c).replace(", v1", ""))
        ax.set_xticks([0, 1, 2, 3], ["0", "1", "2", "3+"])
        ax.set_title(SIZE_NAME[m], fontsize=9, color="#0b0b0b")
        ax.set_xlabel("Compactions since last change", fontsize=8)
    axes[0].set_ylabel("Action accuracy (Confirm)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    save(fig, out / "fig_decay.pdf")
    plt.close(fig)


def fig_errors(err: pd.DataFrame, out: Path):
    plt = setup_mpl()
    metrics = [("violation", "Violation"), ("premature", "Premature"), ("duplicate", "Duplicate"),
               ("missed_clarify", "Missed clarify"), ("over_restriction", "Over-restriction"),
               ("unneeded_clarify", "Unneeded clarify")]
    conds = ["summary", "pinning", "retrieval", "chrono_hint_v2", "lifecycle_v2", "lifecycle_gold"]
    fig, axes = plt.subplots(1, len(SMALL), figsize=(7.2, 3.1), sharey=True)
    w = 0.8 / len(conds)
    for ax, m in zip(axes, SMALL):
        s = err[err.model == m].set_index("condition")
        for j, c in enumerate(conds):
            ax.bar(np.arange(len(metrics)) + (j - len(conds) / 2 + 0.5) * w, [s.loc[c, k] for k, _ in metrics], w,
                   color=color(c), label=NAME[c], hatch="///" if c == "lifecycle_gold" else None, edgecolor="#fcfcfb",
                   linewidth=0)
        ax.set_xticks(range(len(metrics)), [n for _, n in metrics], rotation=35, ha="right", fontsize=7)
        ax.set_title(SIZE_NAME[m], fontsize=9, color="#0b0b0b")
    axes[0].set_ylabel("Error rate (Confirm)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7)
    fig.tight_layout(rect=(0, 0.15, 1, 1))
    save(fig, out / "fig_error_rates.pdf")
    plt.close(fig)


def fig_rq1(rq1: pd.DataFrame, out: Path):
    plt = setup_mpl()
    conds = ["summary", "pinning", "chrono_v2", "retrieval", "lifecycle_v2", "full"]
    fig, axes = plt.subplots(1, len(SMALL), figsize=(7.2, 3.0), sharey=True)
    for ax, m in zip(axes, SMALL):
        s = rq1[(rq1.model == m) & rq1.mutable].set_index("condition")
        x = np.arange(len(conds))
        stale = [s.loc[c, "stale"] for c in conds]
        missing = [s.loc[c, "missing"] for c in conds]
        ax.bar(x, stale, 0.6, color="#b5507a", label="Stale (an earlier status)")
        ax.bar(x, missing, 0.6, bottom=stale, color="#c3c2b7", label="Missing (unknown)")
        ax.set_xticks(x, [NAME[c].replace(" (reference)", "") for c in conds], rotation=40, ha="right", fontsize=7)
        ax.set_title(SIZE_NAME[m], fontsize=9, color="#0b0b0b")
    axes[0].set_ylabel("Share of state answers\n(mutable items)", fontsize=8)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    save(fig, out / "fig_rq1_stale_missing.pdf")
    plt.close(fig)


def budget_rows(root: Path) -> pd.DataFrame:
    rows = []
    for label, run in MODELS.items():
        for b in (256, 384, 768):
            v1 = load(str(root / f"{run}-pace-hardcap"), b)
            v2r = v2(load(str(root / f"{run}-pace-replicate-test-v2"), b))
            f = pd.concat([v1, v2r], ignore_index=True)
            for c in ("summary", "pinning", "chrono_v2", "lifecycle", "lifecycle_v2", "lifecycle_gold"):
                v, lo, hi = cluster_boot(f[f.condition == c], "accuracy")
                rows.append(dict(model=label, budget=b, condition=c, accuracy=v, lo=lo, hi=hi))
    return pd.DataFrame(rows)


def fig_budget(bud: pd.DataFrame, out: Path):
    plt = setup_mpl()
    fig, axes = plt.subplots(1, len(SMALL), figsize=(7.2, 2.9), sharey=True)
    for ax, m in zip(axes, SMALL):
        s = bud[bud.model == m]
        for c in ("summary", "pinning", "chrono_v2", "lifecycle", "lifecycle_v2", "lifecycle_gold"):
            x = s[s.condition == c].sort_values("budget")
            ax.plot(x.budget, x.accuracy, marker="o", ms=3, lw=1.4, color=color(c) if c != "lifecycle" else "#e8a7c3",
                    ls="--" if c == "lifecycle_gold" else "-", label=NAME[c])
        ax.set_xscale("log")
        ax.set_xticks([256, 384, 768], ["256", "384", "768"])
        ax.minorticks_off()
        ax.set_title(SIZE_NAME[m], fontsize=9, color="#0b0b0b")
        ax.set_xlabel("Memory budget (tokens)", fontsize=8)
    axes[0].set_ylabel("Action accuracy (Test)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7)
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    save(fig, out / "fig_budget.pdf")
    plt.close(fig)


def fig_forged(effects: pd.DataFrame, out: Path):
    plt = setup_mpl()
    conds = ["full", "summary", "pinning", "retrieval", "chrono_hint_v2", "lifecycle_v2", "lifecycle_source_v2"]
    models = [m for m in ALL if m in set(effects.model)]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    w = 0.8 / len(conds)
    for j, c in enumerate(conds):
        s = effects[effects.condition == c].set_index("model")
        x = np.arange(len(models)) + (j - len(conds) / 2 + 0.5) * w
        ax.bar(x, [s.loc[m, "act_forged"] for m in models], w, color=color(c), label=NAME[c], edgecolor="#fcfcfb",
               linewidth=0, hatch="///" if c == "full" else None)
        ax.scatter(x, [s.loc[m, "act_clean"] for m in models], s=6, color="#0b0b0b", zorder=3,
                   label="Same decisions without the forged message" if j == 0 else None)
    ax.set_xticks(range(len(models)), [SIZE_NAME[m].replace("-", "\n", 1) for m in models], fontsize=7.5)
    ax.set_ylabel("Acted on the forged claim")
    ax.set_ylim(0, 1)
    h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=3, fontsize=7)
    fig.tight_layout(rect=(0, 0.2, 1, 1))
    save(fig, out / "fig_forged.pdf")
    plt.close(fig)


def fig_swap(swap: pd.DataFrame, out: Path):
    plt = setup_mpl()
    ladl = swap[swap.condition == "lifecycle"].copy()
    ladl["source"] = ladl.extractor + " " + ladl.version
    order = ["Qwen v1", "Qwen v2", "Llama v1", "Llama v2", "Mistral v1", "Mistral v2"]
    grid = ladl.pivot_table(index="decider", columns="source", values="accuracy").reindex(index=SMALL, columns=order)
    fig, ax = plt.subplots(figsize=(4.8, 2.3))
    im = ax.imshow(grid.values, cmap="RdPu", vmin=0.6, vmax=0.9)
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            ax.text(j, i, f"{100 * grid.values[i, j]:.1f}", ha="center", va="center", fontsize=7,
                    color="#fcfcfb" if grid.values[i, j] > 0.8 else "#0b0b0b")
    ax.set_xticks(range(len(order)), [o.replace(" ", "\n") for o in order], fontsize=7)
    ax.set_yticks(range(len(SMALL)), [SIZE_NAME[m] for m in SMALL], fontsize=7)
    ax.set_xlabel("Extracted events from", fontsize=8)
    ax.set_ylabel("Decision model", fontsize=8)
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02).ax.tick_params(labelsize=6)
    fig.tight_layout()
    save(fig, out / "fig_swap.pdf")
    plt.close(fig)


# ------------------------------------------------------------------------------------------ tables
def table_accuracy(acc: pd.DataFrame, conds: list[str], models: list[str]) -> str:
    rows = []
    for c in conds:
        s = acc[acc.condition == c].set_index("model")
        if s.empty:
            continue
        rows.append([NAME[c]] + [ci(*s.loc[m, ["accuracy", "lo", "hi"]]) if m in s.index else "--" for m in models])
    return tabular(["Condition"] + [SIZE_NAME[m] for m in models], rows)


def table_tests(tests: pd.DataFrame) -> str:
    t = tests[(tests.metric == "four_way") & tests.planned]
    label = {"primary": "Primary", "secondary": "Secondary", "third primary": "Primary (Mistral)",
             "third v2": "v2 family (Mistral)", "third secondary": "Secondary (Mistral)"}
    rows = []
    for _, r in t.iterrows():
        b = r.b.replace("_v2", " v2")
        a = "LADL v2" if r.a == "lifecycle_v2" else ("Strict hedging" if r.a == "lifecycle_strict" else "LADL v1")
        rows.append([label.get(r.family, r.family), SIZE_NAME[r.model], f"{a} $-$ {NAME.get(r.b, b)}", diff_ci(r),
                     f"{r.p_holm:.3f}", "yes" if r.confirmed else "no"])
    return tabular(["Family", "Model", "Comparison", "Difference", "Holm $p$", "Confirmed"], rows, "lllrrc")


def table_errors(err: pd.DataFrame) -> str:
    conds = ["full", "summary", "pinning", "retrieval", "chrono_hint_v2", "typed_llm_v2", "lifecycle_v2", "lifecycle_gold"]
    metrics = ["violation", "premature", "duplicate", "missed_clarify", "over_restriction", "unneeded_clarify"]
    rows = []
    for m in SMALL:
        s = err[err.model == m].set_index("condition")
        for c in conds:
            rows.append([SIZE_NAME[m] if c == conds[0] else "", NAME[c]] + [pc(s.loc[c, k]) for k in metrics])
    return tabular(["Model", "Condition", "Violation", "Premature", "Duplicate", "Missed clarify", "Over-restriction",
                    "Unneeded clarify"], rows, "llrrrrrr")


def table_ablations(frames: dict[str, pd.DataFrame]) -> str:
    conds = ["lifecycle", "abl_noguard", "abl_noreceipt", "lifecycle_nohint", "lifecycle_strict", "lifecycle_gold"]
    fns = metric_fns()
    rows = []
    for c in conds:
        row = [NAME[c]]
        for m in SMALL:
            d = frames[m][frames[m].condition == c]
            num, den = fns["premature"](d)
            retry = d[d.gold_reason == "retry_after_failure"]
            row += [pc((d.pred_decision == d.gold_decision).mean()), pc(num.sum() / den.sum()),
                    pc((retry.pred_decision == retry.gold_decision).mean())]
        rows.append(row)
    # Premature: act while the condition is unmet (guard logic). Retry: correct act after a failed attempt (receipts).
    head = ["Condition (extraction v1)"] + [f"{SIZE_NAME[m]} {k}" for m in SMALL for k in ("Acc.", "Premature", "Retry")]
    return tabular(head, rows, "l" + "r" * 9)


def table_extraction(root: Path) -> str:
    rows = []
    dlg = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open(DATA["Confirm"])}
    for label, run in ALL.items():
        cells = [SIZE_NAME[label]]
        for v in ("v1", "v2"):
            p = root / f"{run}-pace-confirm-{v}" / "extractions.jsonl"
            if not p.exists():
                cells += ["--"] * 3
                continue
            q = evaluate(dlg, [json.loads(l) for l in open(p)])
            cells += [f"{q['precision']:.3f}", f"{q['recall']:.3f}", f"{q['f1']:.3f}"]
        rows.append(cells)
    return tabular(["Model", "P (v1)", "R (v1)", "F1 (v1)", "P (v2)", "R (v2)", "F1 (v2)"], rows)


def rq1_rows(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for m, f in frames.items():
        f = f.assign(err=[recall_error_type(r) for r in f.itertuples()])
        for (c, mut), d in f.groupby(["condition", "item_mutable"]):
            cnt = d.err.value_counts(normalize=True)
            rows.append(dict(model=m, condition=c, mutable=bool(mut), **{k: cnt.get(k, 0.0) for k in
                                                                         ("correct", "stale", "missing", "other")}))
    return pd.DataFrame(rows)


def table_rq1(rq1: pd.DataFrame) -> str:
    conds = ["full", "summary", "pinning", "retrieval", "chrono_v2", "lifecycle_v2", "lifecycle_gold"]
    rows = []
    for m in SMALL:
        for c in conds:
            mu = rq1[(rq1.model == m) & (rq1.condition == c) & rq1.mutable].iloc[0]
            st = rq1[(rq1.model == m) & (rq1.condition == c) & ~rq1.mutable].iloc[0]
            rows.append([SIZE_NAME[m] if c == conds[0] else "", NAME[c], pc(mu.correct), pc(mu.stale), pc(mu.missing),
                         pc(st.correct), pc(st.stale), pc(st.missing)])
    return tabular(["Model", "Condition", "Mutable: correct", "stale", "missing", "Static: correct", "stale", "missing"],
                   rows, "llrrrrrr")


def table_rq3(frames: dict[str, pd.DataFrame], root: Path) -> str:
    dlg = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open(DATA["Confirm"])}
    kinds = ["bad extraction", "bad transition", "lost ledger state", "wrong action | correct state"]
    rows = []
    for m in SMALL:
        for cond, version in (("lifecycle", "v1"), ("lifecycle_v2", "v2")):
            ex = {json.loads(l)["dialogue_id"]: json.loads(l)["events"]
                  for l in open(root / f"{MODELS[m]}-pace-confirm-{version}" / "extractions.jsonl")}
            d = frames[m][frames[m].condition == cond]
            labels = pd.Series([attribute(r, dlg[r.dialogue_id], ex[r.dialogue_id]) for _, r in d.iterrows()])
            share = labels.value_counts(normalize=True)
            rows.append([SIZE_NAME[m], version, pc(1 - share.get("correct", 0))] + [pc(share.get(k, 0)) for k in kinds])
    return tabular(["Model", "Extraction", "Wrong", "Bad extraction", "Bad transition", "Lost state",
                    "Wrong action, correct state"], rows, "llrrrrr")


def table_dialogue(frames: dict[str, pd.DataFrame]) -> str:
    conds = ["full", "summary", "summary_hint", "pinning_hint", "retrieval", "chrono_hint_v2", "lifecycle",
             "lifecycle_v2", "lifecycle_gold"]
    rows = []
    per = {m: dialogues(f[f.condition.isin(conds)]) for m, f in frames.items()}
    for c in conds:
        row = [NAME[c]]
        for m in SMALL:
            d = per[m][per[m].condition == c]
            row += [pc(rate_ci(d, "success")[0]), pc(rate_ci(d, "safe")[0])]
        rows.append(row)
    head = ["Condition"] + [f"{SIZE_NAME[m]} {k}" for m in SMALL for k in ("all correct", "no unsafe act")]
    return tabular(head, rows, "l" + "r" * 6)


def span(values: pd.Series, fmt: str) -> str:
    """Range over the three models, or one value when they agree; 0 when there is no such cost."""
    lo, hi = fmt.format(values.min()), fmt.format(values.max())
    if values.max() == 0:
        return "0"
    return lo if lo == hi else f"{lo}--{hi}"


def table_cost(root: Path, replays: Path) -> str:
    """Calls and tokens per Confirm dialogue (v1 runs, state questions excluded) and one-request-at-a-time latency."""
    cost = cost_table(root, replays)
    latency, _ = latency_table(root)
    conds = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle"]
    names = {"chrono": "Chronological ledger", "typed_llm": "LLM-written transitions", "lifecycle": "LADL (ours)"}
    rows = []
    for c in conds:
        cs = cost[(cost.condition == c) & (cost.extraction == "v1")]
        ls = latency[latency.condition == c]
        rows.append([names.get(c, NAME.get(c, c)), span(cs.calls, "{:.1f}"),
                     span(cs.prompt_tokens / 1000, "{:.1f}k"), span(cs.upkeep_tokens / 1000, "{:.1f}k"),
                     span(cs.memory_tokens, "{:.0f}"), span(ls.seconds_per_dialogue, "{:.1f}")])
    return tabular(["Condition", "Calls", "Prompt tokens", "Upkeep tokens", "Memory tokens", "Seconds"], rows)


def table_scale(acc: pd.DataFrame) -> str:
    conds = ["full", "summary", "pinning", "retrieval", "summary_retrieval", "chrono_hint_v2", "typed_llm_v2",
             "lifecycle_v2", "lifecycle_gold"]
    order = ["Qwen", "Qwen-14B", "Qwen-32B", "Llama", "Mistral", "Mistral-24B"]
    rows = []
    for c in conds:
        s = acc[acc.condition == c].set_index("model")
        rows.append([NAME[c]] + [pc(s.loc[m, "accuracy"]) if m in s.index else "--" for m in order])
    return tabular(["Condition"] + [SIZE_NAME[m] for m in order], rows)


def table_forged(effects: pd.DataFrame) -> str:
    conds = ["full", "summary", "pinning", "retrieval", "chrono_hint_v2", "lifecycle_v2", "lifecycle_source_v2"]
    order = [m for m in ["Qwen", "Qwen-14B", "Qwen-32B", "Llama", "Mistral", "Mistral-24B"] if m in set(effects.model)]
    rows = []
    for c in conds:
        s = effects[effects.condition == c].set_index("model")
        rows.append([NAME[c]] + [f"{pc(s.loc[m, 'act_forged'])} ({pc(s.loc[m, 'act_clean'])})" for m in order])
    return tabular(["Condition"] + [SIZE_NAME[m] for m in order], rows)


def table_swap(swap: pd.DataFrame) -> str:
    ladl = swap[swap.condition == "lifecycle"]
    rows = []
    for m in SMALL:
        s = ladl[ladl.decider == m]
        rows.append([SIZE_NAME[m]] + [pc(s[(s.extractor == e) & (s.version == v)].accuracy.iloc[0])
                                      for e in SMALL for v in ("v1", "v2")])
    return tabular(["Decision model"] + [f"{e} {v}" for e in SMALL for v in ("v1", "v2")], rows)


def error_rows(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    fns = metric_fns()
    rows = []
    for m, f in frames.items():
        for c, d in f.groupby("condition"):
            row = dict(model=m, condition=c)
            for k in ("violation", "premature", "duplicate", "missed_clarify", "over_restriction", "unneeded_clarify"):
                num, den = fns[k](d)
                row[k] = num.sum() / den.sum() if den.sum() else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_det")
    ap.add_argument("--out", default="paper")
    ap.add_argument("--preview", help="also write PNG copies of the figures to this folder")
    ap.add_argument("--replays", default="results/replay_followup/det_confirm",
                    help="cache replays of the deterministic Confirm runs, which count usage per condition")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    figs, tabs = out / "figures", out / "tables"
    global PREVIEW
    if a.preview:
        PREVIEW = Path(a.preview)
        PREVIEW.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)
    tabs.mkdir(parents=True, exist_ok=True)

    confirm = {m: f for m in ALL if (f := clean_frame(root, m)) is not None}
    small = {m: confirm[m] for m in SMALL}
    test = {m: f for m in SMALL if (f := test_frame(root, m)) is not None}
    acc_c = accuracy_rows(small, MAIN)
    acc_t = accuracy_rows(test, MAIN)
    err = error_rows(small)
    rq1 = rq1_rows(small)
    decay, _, _ = analyses_g(root)
    bud = budget_rows(root)
    with tempfile.TemporaryDirectory() as tmp:
        experiment_b(root, Path(tmp))
        experiment_c(root, Path(tmp))
        shutil.copy(Path(tmp) / "fig_noise.pdf", figs / "fig_noise.pdf")
        if PREVIEW is not None:
            shutil.copy(Path(tmp) / "fig_noise.png", PREVIEW / "fig_noise.png")
        swap = pd.read_csv(Path(tmp) / "swap_accuracy.csv")
    from src.eval.scale_report import forged_tables
    _, effects = forged_tables(root, confirm)
    scale_acc = accuracy_table(confirm)
    scale_figure(scale_acc, figs)
    if PREVIEW is not None:
        shutil.copy(figs / "fig_scale.png", PREVIEW / "fig_scale.png")
    (figs / "fig_scale.png").unlink(missing_ok=True)
    tests, _ = planned_tests(root)

    fig_accuracy(acc_c, MAIN, figs, "fig_main_accuracy.pdf", "Confirm")
    fig_accuracy(acc_t, MAIN, figs, "fig_main_accuracy_test.pdf", "Test")
    fig_decay(decay, figs)
    fig_errors(err, figs)
    fig_rq1(rq1, figs)
    fig_budget(bud, figs)
    fig_forged(effects, figs)
    fig_swap(swap, figs)

    tables = {"main": table_accuracy(acc_c, MAIN, SMALL), "main_test": table_accuracy(acc_t, MAIN, SMALL),
              "paired": table_tests(tests), "errors": table_errors(err), "ablations": table_ablations(small),
              "extraction": table_extraction(root), "rq1": table_rq1(rq1), "rq3": table_rq3(small, root),
              "dialogue": table_dialogue(small), "scale": table_scale(scale_acc), "forged": table_forged(effects),
              "swap": table_swap(swap), "cost": table_cost(root, Path(a.replays))}
    for name, text in tables.items():
        (tabs / f"{name}.tex").write_text(f"% Generated by python -m src.eval.paper_assets; do not edit.\n{text}")
    print(f"wrote {len(list(figs.glob('fig_*.pdf')))} figures to {figs} and {len(tables)} tables to {tabs}")


if __name__ == "__main__":
    main()
