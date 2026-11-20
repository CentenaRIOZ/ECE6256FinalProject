"""Metrics, timeline-cluster bootstrap CIs, paired comparisons, RQ1/RQ3 analyses, tables and figures.

python -m src.eval.analyze --runs results/runs/qwen2.5-7b results/runs/llama3.1-8b --budget 384 --out results
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.extraction_eval import ev_key, evaluate as extraction_eval

COND_ORDER = ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_gold", "abl_noguard",
              "abl_noreceipt"]
COND_NAME = {"full": "Full history (no compaction)", "summary": "Ordinary compaction", "pinning": "Constraint pinning",
             "chrono": "Chronological event ledger", "typed_llm": "Typed ledger, LLM transitions",
             "lifecycle": "Lifecycle ledger (ours)", "lifecycle_gold": "Lifecycle ledger, gold events",
             "abl_noguard": "Ours - guard logic", "abl_noreceipt": "Ours - receipt evidence"}
MAIN = ["summary", "pinning", "chrono", "typed_llm", "lifecycle"]
COLORS = {"summary": "#2a78d6", "pinning": "#eb6834", "chrono": "#1baf7a", "typed_llm": "#eda100",
          "lifecycle": "#e87ba4", "lifecycle_gold": "#008300", "full": "#898781",
          "abl_noguard": "#6250d6", "abl_noreceipt": "#e34948"}
MARKERS = {"summary": "o", "pinning": "s", "chrono": "^", "typed_llm": "D", "lifecycle": "*", "full": "x",
           "lifecycle_gold": "P"}

PROHIBITED = {"prohibited_active", "cancelled"}


# ------------------------------------------------------------------------- metrics
def metric_fns() -> dict:
    """Each metric = (numerator mask, denominator mask) over a probe dataframe."""
    def m(num, den):
        return lambda d: (num(d) & den(d), den(d))
    act = lambda d: d.pred_decision == "act"
    return {
        "accuracy": m(lambda d: d.pred_decision == d.gold_decision, lambda d: d.gold_decision.notna()),
        "violation": m(act, lambda d: d.gold_reason.isin(PROHIBITED)),
        "over_restriction": m(lambda d: d.pred_decision.isin(["wait", "decline"]), lambda d: d.gold_decision == "act"),
        "premature": m(act, lambda d: d.gold_reason == "guard_unmet"),
        "duplicate": m(act, lambda d: d.gold_reason == "completed"),
        "missed_clarify": m(act, lambda d: d.gold_decision == "clarify"),
        "unneeded_clarify": m(lambda d: d.pred_decision == "clarify", lambda d: d.gold_decision != "clarify"),
        "unsafe_act": m(act, lambda d: d.gold_decision != "act"),
        "state_recall": m(lambda d: d.pred_label == d.gold_label, lambda d: d.gold_label.notna()),
    }


def rate(df: pd.DataFrame, name: str) -> float:
    num, den = metric_fns()[name](df)
    return num.sum() / den.sum() if den.sum() else np.nan


def cluster_boot(df: pd.DataFrame, name: str, reps: int = 2000, seed: int = 0) -> tuple[float, float, float]:
    """Point estimate + 95% percentile CI, resampling timelines (all dialogues/probes of a timeline together)."""
    num, den = metric_fns()[name](df)
    g = pd.DataFrame({"t": df.timeline_id.values, "n": num.values.astype(float), "d": den.values.astype(float)})
    agg = g.groupby("t")[["n", "d"]].sum()
    n, d = agg.n.values, agg.d.values
    if d.sum() == 0:
        return np.nan, np.nan, np.nan
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(n), size=(reps, len(n)))
    with np.errstate(invalid="ignore", divide="ignore"):
        bs = n[idx].sum(1) / d[idx].sum(1)
    bs = bs[~np.isnan(bs)]
    return n.sum() / d.sum(), *np.percentile(bs, [2.5, 97.5])


def paired_diff(df: pd.DataFrame, a: str, b: str, name: str = "accuracy", reps: int = 2000, seed: int = 0):
    """Diff metric(a) - metric(b) on the same probes, timeline-cluster bootstrap CI + two-sided bootstrap p."""
    rows = []
    for c in (a, b):
        num, den = metric_fns()[name](df[df.condition == c])
        sub = df[df.condition == c]
        rows.append(pd.DataFrame({"t": sub.timeline_id.values, "n": num.values.astype(float),
                                  "d": den.values.astype(float)}).groupby("t")[["n", "d"]].sum())
    j = rows[0].join(rows[1], lsuffix="_a", rsuffix="_b", how="inner")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(j), size=(reps, len(j)))
    with np.errstate(invalid="ignore", divide="ignore"):
        A = j.n_a.values[idx].sum(1) / j.d_a.values[idx].sum(1)
        B = j.n_b.values[idx].sum(1) / j.d_b.values[idx].sum(1)
    diff = (A - B)[~np.isnan(A - B)]
    if j.d_a.sum() == 0 or len(diff) == 0:
        return np.nan, np.nan, np.nan, np.nan
    point = j.n_a.sum() / j.d_a.sum() - j.n_b.sum() / j.d_b.sum()
    p = 2 * min((diff <= 0).mean(), (diff >= 0).mean())
    return point, *np.percentile(diff, [2.5, 97.5]), min(1.0, p)


# ------------------------------------------------------------------------- RQ1 / RQ3
def recall_error_type(r) -> str:
    if r.pred_label == r.gold_label:
        return "correct"
    if r.pred_label == "unknown":
        return "missing"
    if r.pred_label in (r.prior_labels or []):
        return "stale"
    return "other"


def attribute(r, dlg: dict | None, extracted: list | None) -> str:
    """Why was a decision wrong? (RQ3)"""
    if r.pred_decision == r.gold_decision:
        return "correct"
    if r.condition == "lifecycle_gold":
        return "wrong action | correct state"
    if r.ledger_label is not None and isinstance(r.ledger_label, str):
        if r.ledger_label == r.gold_label:
            return "wrong action | correct state"
        if r.ledger_truncated and r.ledger_label == "unknown":
            return "lost ledger state"
        if dlg is None or extracted is None:
            return "bad state (unattributed)"
        item = dlg["items"][r["item"]]
        gold_seq = [ev_key(e, item["tool"]) for t in dlg["turns"][:r.after_turn + 1] for e in t["gold_events"]
                    if e["item"] == r["item"]]
        pred_seq = [ev_key(e, e.get("tool")) for evs in extracted[:r.after_turn + 1] for e in evs
                    if e.get("tool") == item["tool"]]
        return "bad transition" if gold_seq == pred_seq else "bad extraction"
    # no explicit state: use the model's own recall of the state
    return "wrong action | correct recall" if r.pred_label == r.gold_label else "wrong recall"


# ------------------------------------------------------------------------- figures
def setup_mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#c3c2b7", "axes.labelcolor": "#52514e", "xtick.color": "#52514e",
                         "ytick.color": "#52514e", "axes.grid": True, "grid.color": "#e1e0d9", "grid.linewidth": 0.6,
                         "axes.axisbelow": True, "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb",
                         "savefig.facecolor": "#fcfcfb", "legend.frameon": False})
    return plt


def fig_main(summ: pd.DataFrame, out: Path):
    plt = setup_mpl()
    models = list(summ.model.unique())
    conds = [c for c in COND_ORDER if c in set(summ.condition) and not c.startswith("abl")]
    fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 2.9), sharey=True, squeeze=False)
    for ax, mdl in zip(axes[0], models):
        s = summ[(summ.model == mdl)].set_index("condition")
        y = np.arange(len(conds))
        for i, c in enumerate(conds):
            v, lo, hi = s.loc[c, ["accuracy", "accuracy_lo", "accuracy_hi"]]
            ax.barh(i, v, color=COLORS[c], height=0.62, hatch="///" if c in ("full", "lifecycle_gold") else None,
                    edgecolor="#fcfcfb", linewidth=0)
            ax.errorbar(v, i, xerr=[[v - lo], [hi - v]], color="#0b0b0b", capsize=2, lw=0.9)
            ax.text(hi + 0.01, i, f"{v:.2f}", va="center", fontsize=8, color="#0b0b0b")
        ax.set_yticks(y, [COND_NAME[c] for c in conds])
        if ax is axes[0][0]:
            ax.invert_yaxis()  # shared y: invert once
        ax.set_xlim(0.3, 1.0)
        ax.set_title(mdl, fontsize=9, color="#0b0b0b")
        ax.set_xlabel("Action accuracy (95% CI)")
        ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(out / "fig_main_accuracy.pdf")
    fig.savefig(out / "fig_main_accuracy.png", dpi=200)
    plt.close(fig)


def fig_decay(df: pd.DataFrame, out: Path):
    plt = setup_mpl()
    models = list(df.model.unique())
    fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 2.6), sharey=True, squeeze=False)
    df = df.assign(bucket=df.compactions_since_last_transition.clip(upper=3))
    conds = [c for c in ["full", "summary", "pinning", "chrono", "typed_llm", "lifecycle"] if c in set(df.condition)]
    for ax, mdl in zip(axes[0], models):
        d = df[df.model == mdl]
        for c in conds:
            ys = [rate(d[(d.condition == c) & (d.bucket == b)], "accuracy") for b in range(4)]
            ax.plot(range(4), ys, marker=MARKERS[c], color=COLORS[c], lw=2, ms=6, label=COND_NAME[c],
                    ls="--" if c == "full" else "-")
        ax.set_xticks(range(4), ["0", "1", "2", "3+"])
        ax.set_xlabel("Compactions since the item's last state change")
        ax.set_title(mdl, fontsize=9)
    axes[0][0].set_ylabel("Action accuracy")
    axes[0][-1].legend(fontsize=7, loc="lower left", bbox_to_anchor=(1.0, 0.0))
    fig.tight_layout()
    fig.savefig(out / "fig_decay.pdf")
    fig.savefig(out / "fig_decay.png", dpi=200)
    plt.close(fig)


def fig_errors(summ: pd.DataFrame, out: Path):
    plt = setup_mpl()
    models = list(summ.model.unique())
    mets = ["violation", "over_restriction", "premature", "duplicate"]
    conds = [c for c in ["full"] + MAIN if c in set(summ.condition)]
    fig, axes = plt.subplots(1, len(models), figsize=(3.4 * len(models), 2.6), sharey=True, squeeze=False)
    w = 0.8 / len(conds)
    for ax, mdl in zip(axes[0], models):
        s = summ[summ.model == mdl].set_index("condition")
        for i, c in enumerate(conds):
            ax.bar(np.arange(len(mets)) + (i - len(conds) / 2 + 0.5) * w, [s.loc[c, m] for m in mets], width=w * 0.9,
                   color=COLORS[c], label=COND_NAME[c], hatch="///" if c == "full" else None, linewidth=0)
        ax.set_xticks(range(len(mets)), ["Violation", "Over-restriction", "Premature", "Duplicate"], fontsize=8)
        ax.set_title(mdl, fontsize=9)
        ax.grid(axis="x", visible=False)
    axes[0][0].set_ylabel("Error rate")
    axes[0][-1].legend(fontsize=7, loc="upper left", bbox_to_anchor=(1.0, 1.0))
    fig.tight_layout()
    fig.savefig(out / "fig_error_rates.pdf")
    fig.savefig(out / "fig_error_rates.png", dpi=200)
    plt.close(fig)


def fig_rq1(rq1: pd.DataFrame, out: Path):
    plt = setup_mpl()
    kinds = ["stale", "missing", "other"]
    colors = {"stale": "#2a78d6", "missing": "#eb6834", "other": "#898781"}
    rq1 = rq1[rq1.condition.isin(["summary", "pinning", "lifecycle"])]
    labels = [f"{r.model.split('-')[0]}\n{COND_NAME[r.condition].split(' (')[0]}\n{'mutable' if r.mutable else 'static'}"
              for r in rq1.itertuples()]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    bottom = np.zeros(len(rq1))
    for k in kinds:
        v = rq1[k].values
        ax.bar(range(len(rq1)), v, bottom=bottom, color=colors[k], label=k, width=0.7, edgecolor="#fcfcfb", linewidth=1)
        bottom += v
    ax.set_xticks(range(len(rq1)), labels, fontsize=6)
    ax.set_ylabel("State-recall error rate")
    ax.legend(fontsize=8)
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(out / "fig_rq1_stale_missing.pdf")
    fig.savefig(out / "fig_rq1_stale_missing.png", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------------- main
def fmt_ci(v, lo, hi, pct=True):
    f = (lambda x: f"{100 * x:.1f}") if pct else (lambda x: f"{x:.2f}")
    return f"{f(v)} [{f(lo)}, {f(hi)}]" if not np.isnan(v) else "-"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--budget", type=int, default=384)
    ap.add_argument("--data", default="data/dialogues/dialogues.jsonl")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    out = Path(a.out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    dlgs = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open(a.data)}

    frames, extractions, metas = [], {}, {}
    for run in a.runs:
        run = Path(run)
        meta = json.loads((run / f"meta_B{a.budget}.json").read_text())
        mdl = meta["config"]["model"].split("/")[-1]
        metas[mdl] = meta
        d = pd.read_json(run / f"probes_B{a.budget}.jsonl", lines=True)
        d["model"] = mdl
        frames.append(d)
        ex_path = run / "extractions.jsonl"
        if ex_path.exists():
            extractions[mdl] = {json.loads(l)["dialogue_id"]: json.loads(l)["events"] for l in open(ex_path)}
    df = pd.concat(frames, ignore_index=True)
    df["recall_error"] = [recall_error_type(r) for r in df.itertuples()]
    df["attribution"] = [attribute(r, dlgs.get(r.dialogue_id), extractions.get(r.model, {}).get(r.dialogue_id))
                         for _, r in df.iterrows()]

    report = [f"# Results (budget B={a.budget} tokens, test split)\n"]
    # ---- main table
    rows = []
    for (mdl, c), d in df.groupby(["model", "condition"]):
        row = dict(model=mdl, condition=c, n=len(d))
        for name in metric_fns():
            v, lo, hi = cluster_boot(d, name)
            row.update({name: v, f"{name}_lo": lo, f"{name}_hi": hi})
        row["memory_tokens"] = d.memory_tokens.mean()
        row["prompt_tokens"] = d.prompt_tokens.mean()
        row["invalid"] = (d.pred_decision == "invalid").mean()
        rows.append(row)
    summ = pd.DataFrame(rows)
    summ["order"] = summ.condition.map(COND_ORDER.index)
    summ = summ.sort_values(["model", "order"])
    summ.to_csv(out / "tables" / "summary.csv", index=False)

    show = ["accuracy", "violation", "over_restriction", "premature", "duplicate", "missed_clarify", "state_recall"]
    for mdl, s in summ.groupby("model", sort=False):
        report.append(f"\n## {mdl}\n")
        report.append("| Condition | " + " | ".join(show) + " | mem tok |\n|---|" + "---|" * (len(show) + 1))
        for r in s.itertuples():
            cells = [fmt_ci(getattr(r, m), getattr(r, f"{m}_lo"), getattr(r, f"{m}_hi")) for m in show]
            report.append(f"| {COND_NAME[r.condition]} | " + " | ".join(cells) + f" | {r.memory_tokens:.0f} |")

    # ---- paired comparisons vs ours
    report.append("\n## Paired differences: lifecycle (ours) minus baseline (timeline-cluster bootstrap)\n")
    report.append("| Model | Baseline | metric | diff (pp) | 95% CI | p |\n|---|---|---|---|---|---|")
    pair_rows = []
    for mdl, d in df.groupby("model"):
        for b in ["summary", "pinning", "chrono", "typed_llm", "full", "abl_noguard", "abl_noreceipt", "lifecycle_gold"]:
            if b not in set(d.condition):
                continue
            for name in ["accuracy", "violation", "over_restriction", "premature", "duplicate"]:
                pt, lo, hi, p = paired_diff(d, "lifecycle", b, name)
                pair_rows.append(dict(model=mdl, baseline=b, metric=name, diff=pt, lo=lo, hi=hi, p=p))
                if name == "accuracy" or b in ("summary", "pinning"):
                    report.append(f"| {mdl} | {COND_NAME[b]} | {name} | {100 * pt:+.1f} | [{100 * lo:+.1f}, {100 * hi:+.1f}] | {p:.3f} |")
    pd.DataFrame(pair_rows).to_csv(out / "tables" / "paired.csv", index=False)

    # ---- per category / reason
    cat = df.groupby(["model", "condition", "category"]).apply(lambda d: rate(d, "accuracy")).unstack("category")
    cat.to_csv(out / "tables" / "accuracy_by_category.csv")
    reason = df.groupby(["model", "condition", "gold_reason"]).apply(lambda d: rate(d, "accuracy")).unstack("gold_reason")
    reason.to_csv(out / "tables" / "accuracy_by_reason.csv")
    for mdl in df.model.unique():
        report.append(f"\n## Accuracy by category / gold reason - {mdl}\n")
        t = pd.concat([cat.loc[mdl], reason.loc[mdl]], axis=1).reindex([c for c in COND_ORDER if c in cat.loc[mdl].index])
        report.append((100 * t).round(1).to_markdown())

    # ---- compaction analyses
    df["bucket"] = df.compactions_since_last_transition.clip(upper=3)
    dec = df.groupby(["model", "condition", "bucket"]).apply(lambda d: rate(d, "accuracy")).unstack("bucket")
    dec.to_csv(out / "tables" / "accuracy_by_compactions_since_transition.csv")
    nc = df.groupby(["model", "condition", "n_compactions"]).apply(lambda d: rate(d, "accuracy")).unstack("n_compactions")
    nc.to_csv(out / "tables" / "accuracy_by_n_compactions.csv")
    report.append("\n## Accuracy by compactions since the item's last transition (0,1,2,3+)\n")
    report.append((100 * dec).round(1).to_markdown())
    report.append("\n## Accuracy by number of compactions in the dialogue\n")
    report.append((100 * nc).round(1).to_markdown())

    # ---- RQ1: stale vs missing, mutable vs static
    rq = []
    for (mdl, c, mut), d in df.groupby(["model", "condition", "item_mutable"]):
        n = len(d)
        cnt = d.recall_error.value_counts()
        rq.append(dict(model=mdl, condition=c, mutable=mut, n=n, **{k: cnt.get(k, 0) / n for k in
                                                                    ["correct", "stale", "missing", "other"]}))
    rq1 = pd.DataFrame(rq)
    rq1["order"] = rq1.condition.map(COND_ORDER.index)
    rq1 = rq1.sort_values(["model", "order", "mutable"]).drop(columns="order")
    rq1.to_csv(out / "tables" / "rq1_recall_errors.csv", index=False)
    report.append("\n## RQ1: state-recall error composition (share of probes)\n")
    report.append(rq1.round(3).to_markdown(index=False))
    # mutable items with >=1 compaction since creation
    sub = df[df.compactions_since_creation >= 1]
    rq1b = sub.groupby(["model", "condition", "item_mutable"]).recall_error.value_counts(normalize=True).unstack().fillna(0)
    report.append("\n### Same, restricted to probes with >=1 compaction since the item was created\n")
    report.append(rq1b.round(3).to_markdown())

    # ---- RQ3: error attribution
    att = df[df.attribution != "correct"].groupby(["model", "condition"]).attribution.value_counts().unstack().fillna(0)
    att_share = att.div(df.groupby(["model", "condition"]).size(), axis=0).reindex(att.index)
    att.to_csv(out / "tables" / "rq3_attribution_counts.csv")
    report.append("\n## RQ3: error attribution (share of all probes)\n")
    report.append((100 * att_share).round(1).to_markdown())

    # ---- extraction quality
    report.append("\n## Extraction quality (turn-level, vs gold events)\n")
    for mdl, ex in extractions.items():
        e = extraction_eval(dlgs, [dict(dialogue_id=k, events=v) for k, v in ex.items()])
        report.append(f"- {mdl}: P={e['precision']:.3f} R={e['recall']:.3f} F1={e['f1']:.3f}; per-op F1 "
                      + ", ".join(f"{k}={v['f1']:.2f}" for k, v in e["per_op"].items()))

    # ---- cost
    report.append("\n## Cost (per run)\n")
    report.append("| Model | wall time (min) | GPU | calls | prompt tokens | completion tokens |\n|---|---|---|---|---|---|")
    for mdl, m in metas.items():
        u = m["usage"]
        report.append(f"| {mdl} | {m['wall_seconds'] / 60:.1f} | {m['gpu'].splitlines()[0] if m['gpu'] else '?'} | "
                      f"{sum(v['calls'] for v in u.values()):.0f} | {sum(v['prompt_tokens'] for v in u.values()):.0f} | "
                      f"{sum(v['completion_tokens'] for v in u.values()):.0f} |")
        report.append("  - per component calls: " + ", ".join(f"{k}={v['calls']:.0f}" for k, v in u.items()))

    (out / f"report_B{a.budget}.md").write_text("\n".join(report) + "\n")
    df.drop(columns=["ledger_item", "summary"], errors="ignore").to_json(out / "tables" / f"all_probes_B{a.budget}.jsonl",
                                                                         orient="records", lines=True)
    fig_main(summ, out / "figures")
    fig_decay(df, out / "figures")
    fig_errors(summ, out / "figures")
    fig_rq1(rq1, out / "figures")
    print("\n".join(report[:40]))
    print(f"\n... full report: {out / f'report_B{a.budget}.md'}")


if __name__ == "__main__":
    main()
