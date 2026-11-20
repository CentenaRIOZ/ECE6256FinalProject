"""Generate LaTeX tables for the paper directly from results/tables/*.csv (no hand-copied numbers).

python -m src.eval.latex_tables --results results --out paper/tables
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.eval.analyze import COND_NAME, COND_ORDER, recall_error_type
from src.eval.extraction_eval import evaluate

MODELS = ["Qwen2.5-7B-Instruct", "Llama-3.1-8B-Instruct"]
SHORT = {"Qwen2.5-7B-Instruct": "Qwen2.5-7B", "Llama-3.1-8B-Instruct": "Llama-3.1-8B"}
COMPACTED = ["summary", "pinning", "chrono", "typed_llm", "lifecycle"]


def pct(x):
    return "--" if pd.isna(x) else f"{100 * x:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results")
    ap.add_argument("--out", default="paper/tables")
    ap.add_argument("--data", default="data/dialogues/dialogues.jsonl")
    a = ap.parse_args()
    R, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    s = pd.read_csv(R / "tables" / "summary.csv")
    paired = pd.read_csv(R / "tables" / "paired.csv")

    # ---------------- Table: main accuracy + error rates
    conds = [c for c in COND_ORDER if c in set(s.condition)]
    lines = [r"\begin{tabular}{l" + "r" * 6 + "}", r"\toprule",
             r" & \multicolumn{3}{c}{Qwen2.5-7B} & \multicolumn{3}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
             r"Condition & Acc. & 95\% CI & State & Acc. & 95\% CI & State \\", r"\midrule"]
    best = {m: s[(s.model == m) & s.condition.isin(COMPACTED)].accuracy.max() for m in MODELS}
    for c in conds:
        cells = []
        for m in MODELS:
            r = s[(s.model == m) & (s.condition == c)].iloc[0]
            acc = pct(r.accuracy)
            if c in COMPACTED and abs(r.accuracy - best[m]) < 1e-9:
                acc = r"\textbf{" + acc + "}"
            cells += [acc, f"[{pct(r.accuracy_lo)}, {pct(r.accuracy_hi)}]", pct(r.state_recall)]
        name = COND_NAME[c].replace("(ours)", r"(\textit{ours})")
        if c == "lifecycle_gold":
            lines.append(r"\midrule")
        lines.append(f"{name} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "main.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: error rates
    mets = [("violation", "Viol."), ("over_restriction", "Over."), ("premature", "Prem."), ("duplicate", "Dup.")]
    lines = [r"\begin{tabular}{l" + "r" * 8 + "}", r"\toprule",
             r" & \multicolumn{4}{c}{Qwen2.5-7B} & \multicolumn{4}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-5}\cmidrule(lr){6-9}",
             "Condition & " + " & ".join([m[1] for m in mets] * 2) + r" \\", r"\midrule"]
    for c in ["full"] + COMPACTED + ["lifecycle_gold"]:
        cells = []
        for m in MODELS:
            r = s[(s.model == m) & (s.condition == c)].iloc[0]
            cells += [pct(getattr(r, k)) for k, _ in mets]
        lines.append(f"{COND_NAME[c].replace('(ours)', '')} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "errors.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: paired differences (ours vs baselines)
    lines = [r"\begin{tabular}{lrrrr}", r"\toprule",
             r"Ours $-$ baseline & \multicolumn{2}{c}{Qwen2.5-7B} & \multicolumn{2}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}", r" & $\Delta$ (pp) & $p$ & $\Delta$ (pp) & $p$ \\", r"\midrule"]
    for b in ["summary", "pinning", "chrono", "typed_llm", "full", "lifecycle_gold"]:
        cells = []
        for m in MODELS:
            r = paired[(paired.model == m) & (paired.baseline == b) & (paired.metric == "accuracy")].iloc[0]
            cells += [f"{100 * r['diff']:+.1f} [{100 * r.lo:+.1f}, {100 * r.hi:+.1f}]",
                      "$<$0.001" if r.p < 0.001 else f"{r.p:.3f}"]
        lines.append(f"{COND_NAME[b].replace('(ours)', '')} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "paired.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: ablations
    lines = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r" & \multicolumn{3}{c}{Qwen2.5-7B} & \multicolumn{3}{c}{Llama-3.1-8B} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
             r"Variant & Acc. & Prem. & Over. & Acc. & Prem. & Over. \\", r"\midrule"]
    for c in ["lifecycle", "abl_noguard", "abl_noreceipt", "lifecycle_strict"]:
        if c not in set(s.condition):
            continue
        cells = []
        for m in MODELS:
            r = s[(s.model == m) & (s.condition == c)].iloc[0]
            cells += [pct(r.accuracy), pct(r.premature), pct(r.over_restriction)]
        lines.append(f"{COND_NAME[c].replace('(ours)', '')} & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "ablations.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: RQ1 recall errors (stale vs missing) for static vs mutable items
    df = pd.read_json(R / "tables" / "all_probes_B384.jsonl", lines=True)
    df = df[df.compactions_since_creation >= 1]
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule", r"Model & Condition / items & Correct & Stale & Missing & Other \\",
             r"\midrule"]
    for m in MODELS:
        for c in ["full", "summary", "pinning", "lifecycle"]:
            for mut in (False, True):
                d = df[(df.model == m) & (df.condition == c) & (df.item_mutable == mut)]
                vc = d.recall_error.value_counts(normalize=True)
                lines.append(f"{SHORT[m] if (c == 'full' and not mut) else ''} & {COND_NAME[c].split(' (')[0]}, "
                             f"{'mutable' if mut else 'static'} & " +
                             " & ".join(pct(vc.get(k, 0)) for k in ["correct", "stale", "missing", "other"]) + r" \\")
        if m != MODELS[-1]:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "rq1.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: RQ3 attribution
    att = pd.read_csv(R / "tables" / "rq3_attribution_counts.csv")
    n = df.groupby(["model", "condition"]).size()  # placeholder (overwritten below with full counts)
    full = pd.read_json(R / "tables" / "all_probes_B384.jsonl", lines=True)
    n = full.groupby(["model", "condition"]).size()
    cols = ["bad extraction", "bad transition", "lost ledger state", "wrong recall", "wrong action | correct recall",
            "wrong action | correct state"]
    cols = [c for c in cols if c in att.columns]
    hdr = {"bad extraction": "Extr.", "bad transition": "Trans.", "lost ledger state": "Lost",
           "wrong recall": "Recall", "wrong action | correct recall": "Act|recall",
           "wrong action | correct state": "Act|state"}
    lines = [r"\begin{tabular}{ll" + "r" * len(cols) + "}", r"\toprule",
             "Model & Condition & " + " & ".join(hdr[c] for c in cols) + r" \\", r"\midrule"]
    for m in MODELS:
        for c in ["summary", "pinning", "chrono", "typed_llm", "lifecycle", "lifecycle_strict", "lifecycle_gold"]:
            r = att[(att.model == m) & (att.condition == c)]
            if r.empty:
                continue
            r = r.iloc[0]
            lines.append(f"{SHORT[m] if c == 'summary' else ''} & {COND_NAME[c].replace('(ours)', '').split(' (post')[0]} & " +
                         " & ".join(pct(r[k] / n[(m, c)]) if r[k] else "--" for k in cols) + r" \\")
        if m != MODELS[-1]:
            lines.append(r"\midrule")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "rq3.tex").write_text("\n".join(lines) + "\n")

    # ---------------- Table: extraction quality
    dlgs = {json.loads(l)["dialogue_id"]: json.loads(l) for l in open(a.data)}
    ops = ["prohibit", "revoke", "ambiguous", "commit", "approve", "cancel", "tool_result"]
    lines = [r"\begin{tabular}{l" + "r" * (len(ops) + 1) + "}", r"\toprule",
             "Extractor & " + " & ".join(o.replace("_", r"\_") for o in ops) + r" & All \\", r"\midrule"]
    for run, m in [("qwen2.5-7b", MODELS[0]), ("llama3.1-8b", MODELS[1])]:
        ex = [json.loads(l) for l in open(R / "runs" / run / "extractions.jsonl")]
        e = evaluate(dlgs, ex)
        lines.append(f"{SHORT[m]} & " + " & ".join(f"{e['per_op'].get(o, {}).get('f1', 0):.2f}" for o in ops) +
                     f" & {e['f1']:.2f}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    (out / "extraction.tex").write_text("\n".join(lines) + "\n")
    print("wrote", sorted(p.name for p in out.glob("*.tex")))


if __name__ == "__main__":
    main()
