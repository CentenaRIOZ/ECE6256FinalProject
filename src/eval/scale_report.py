"""Experiments D-G of docs/scale_retrieval_forgery_plan.md: larger models, retrieval baselines, forged updates, and
descriptive analyses of existing outputs.

python -m src.eval.scale_report --runs results/runs_det --out results/scale

Condition names follow the deterministic runs: event conditions from extraction v2 carry the suffix _v2, and LADL is
lifecycle_v2. Contrasts resample Confirm timelines jointly for every cell (2,000 resamples, seed 0).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import COLORS, COND_NAME, metric_fns, setup_mpl
from src.eval.extraction_eval import evaluate
from src.eval.followup_report import cells, read_jsonl, resample, test, with_holm
from src.eval.models import MODELS
from src.eval.robustness import load
from src.memory.managers import NEEDS_EXTRACTION

LARGE = {"Qwen-14B": "qwen2.5-14b", "Qwen-32B": "qwen2.5-32b", "Mistral-24B": "mistral-small-24b"}
ALL = {**MODELS, **LARGE}
SIZE = {"Qwen": ("Qwen", 7), "Qwen-14B": ("Qwen", 14), "Qwen-32B": ("Qwen", 32), "Mistral": ("Mistral", 7),
        "Mistral-24B": ("Mistral", 24), "Llama": ("Llama", 8)}
CONFIRM, FORGED = "data/confirm/dialogues.jsonl", "data/forged/dialogues.jsonl"
D_BASELINES = ["summary", "summary_hint", "pinning", "pinning_hint", "chrono_v2", "chrono_hint_v2", "typed_llm_v2"]
E_BASELINES = ["retrieval", "summary_retrieval", "recent"]
LADL = "lifecycle_v2"
SHOW = ["full", "summary", "summary_hint", "pinning", "pinning_hint", "recent", "retrieval", "summary_retrieval",
        "chrono_v2", "chrono_hint_v2", "typed_llm_v2", "lifecycle", "lifecycle_v2", "lifecycle_nohint_v2",
        "lifecycle_source_v2", "lifecycle_gold"]


def v2(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.assign(condition=frame.condition.where(~frame.condition.isin(NEEDS_EXTRACTION), frame.condition + "_v2"))


def exists(root: Path, name: str) -> bool:
    return (root / name / "probes_B384.jsonl").exists()


def clean_frame(root: Path, label: str) -> pd.DataFrame | None:
    """All Confirm conditions of one model, from the deterministic, new-condition, or larger-model runs."""
    run = ALL[label]
    parts = [f"{run}-pace-confirm-v1", f"{run}-pace-confirm-v2"]
    if label in MODELS:
        parts += [f"{run}-pace-confirm-new-v1", f"{run}-pace-confirm-new-v2"]
    if not all(exists(root, p) for p in parts):
        return None
    frames = []
    for p in parts:
        f = load(str(root / p), 384)
        frames.append(v2(f) if p.endswith("-v2") else f)
    out = pd.concat(frames, ignore_index=True)
    assert not out.duplicated(["condition", "probe_id"]).any(), label
    return out.assign(cell="clean")


def forged_frames(root: Path, label: str, clean: pd.DataFrame) -> tuple[pd.DataFrame, set] | None:
    """Forged-set probes (extraction v2, named like the clean frame) and clean probes, as cells, and the attacked ids."""
    path = root / f"{ALL[label]}-pace-forged-v2"
    if not exists(root, path.name):
        return None
    forged = v2(load(str(path), 384)).assign(cell="forged")
    attacked = {p for d in read_jsonl(Path(FORGED)) if d["forged"] for p in d["forged"]["attacked_probes"]}
    both = pd.concat([forged, clean[clean.condition.isin(set(forged.condition))]], ignore_index=True)
    return both, attacked


def family(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(with_holm(rows))


def accuracy_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for label, f in frames.items():
        sums = cells(f)
        idx = resample(sums)
        for cond in [c for c in SHOW if c in set(f.condition)]:
            r = test(sums, [(1, "clean", cond)], idx)
            rows.append(dict(model=label, condition=cond, accuracy=r["diff"], lo=r["lo"], hi=r["hi"]))
    return pd.DataFrame(rows)


def extraction_table(root: Path, labels: list[str]) -> pd.DataFrame:
    dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(CONFIRM))}
    rows = []
    for label in labels:
        for version in ("v1", "v2"):
            path = root / f"{ALL[label]}-pace-confirm-{version}" / "extractions.jsonl"
            if path.exists():
                q = evaluate(dialogues, read_jsonl(path))
                rows.append(dict(model=label, version=version, precision=q["precision"], recall=q["recall"], f1=q["f1"]))
    return pd.DataFrame(rows)


def forged_tables(root: Path, frames: dict[str, pd.DataFrame]) -> tuple[list[dict], pd.DataFrame]:
    tests, effects = [], []
    for label, clean in frames.items():
        got = forged_frames(root, label, clean)
        if got is None:
            continue
        both, attacked = got
        hit = both[both.probe_id.isin(attacked)]
        sums = cells(hit)
        idx = resample(sums)
        for name, prediction, terms in (
                ("F1", "positive", [(1, "forged", "lifecycle_source_v2"), (-1, "forged", LADL)]),
                ("F2", "two-sided", [(1, "forged", LADL), (-1, "clean", LADL)]),
                ("F3", "two-sided", [(1, "forged", "lifecycle_source_v2"), (-1, "forged", "summary")])):
            tests.append(dict(family="F", test=name, model=label, a=f"{terms[0][1]}:{terms[0][2]}",
                              b=f"{terms[1][1]}:{terms[1][2]}", prediction=prediction, **test(sums, terms, idx)))
        other = both[~both.probe_id.isin(attacked)]
        other_sums = cells(other)
        other_idx = resample(other_sums)
        for cond in sorted(set(hit.condition)):
            r = test(sums, [(1, "forged", cond), (-1, "clean", cond)], idx)
            o = test(other_sums, [(1, "forged", cond), (-1, "clean", cond)], other_idx)
            act = {c: (hit[(hit.cell == c) & (hit.condition == cond)].pred_decision == "act").mean() for c in ("forged", "clean")}
            effects.append(dict(model=label, condition=cond, attacked_probes=int(((hit.cell == "forged") & (hit.condition == cond)).sum()),
                                accuracy_forged=sums.loc[("forged", cond)]["sum"].sum() / sums.loc[("forged", cond)]["size"].sum(),
                                attack_effect=r["diff"], lo=r["lo"], hi=r["hi"], act_forged=act["forged"],
                                act_clean=act["clean"], other_probes_effect=o["diff"], other_lo=o["lo"], other_hi=o["hi"]))
    return tests, pd.DataFrame(effects)


def analyses_g(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Accuracy by compactions since the item's last change, over-caution, and ledger state accuracy (7B models)."""
    sources = {"Test": ["-pace-hardcap", "-pace-replicate-test-v2"], "Fresh": ["-pace-fresh-spread", "-pace-replicate-fresh-v2"],
               "Confirm": ["-pace-confirm-v1", "-pace-confirm-v2"]}
    decay, caution, ledger = [], [], []
    fns = metric_fns()
    for dataset, (base, extra) in sources.items():
        for label, run in MODELS.items():
            if not (exists(root, run + base) and exists(root, run + extra)):
                continue
            f = pd.concat([load(str(root / (run + base)), 384), v2(load(str(root / (run + extra)), 384))], ignore_index=True)
            f["correct"] = f.pred_decision == f.gold_decision
            f["since"] = f.compactions_since_last_transition.clip(upper=3)
            for (cond, since), g in f.groupby(["condition", "since"]):
                decay.append(dict(dataset=dataset, model=label, condition=cond, compactions_since_change=int(since),
                                  probes=len(g), accuracy=g.correct.mean()))
            for cond, g in f.groupby("condition"):
                row = dict(dataset=dataset, model=label, condition=cond)
                for m in ("over_restriction", "unneeded_clarify", "unsafe_act"):
                    num, den = fns[m](g)
                    row[m] = num.sum() / den.sum() if den.sum() else np.nan
                caution.append(row)
                if g.ledger_label.notna().any():
                    ledger.append(dict(dataset=dataset, model=label, condition=cond,
                                       ledger_state_accuracy=(g.ledger_label == g.gold_label).mean(),
                                       model_state_accuracy=(g.pred_label == g.gold_label).mean(),
                                       decision_accuracy=g.correct.mean()))
    return pd.DataFrame(decay), pd.DataFrame(caution), pd.DataFrame(ledger)


def test_replication(root: Path) -> pd.DataFrame:
    """Exploratory: LADL v2 minus the retrieval baselines on Test (budget 384), 7B models."""
    rows = []
    for label, run in MODELS.items():
        names = [f"{run}-pace-replicate-test-v2", f"{run}-pace-test-new", f"{run}-pace-hardcap"]
        if not all(exists(root, n) for n in names):
            continue
        hard = load(str(root / names[2]), 384)
        f = pd.concat([v2(load(str(root / names[0]), 384)), load(str(root / names[1]), 384),
                       hard[hard.condition.isin(["summary", "pinning", "full"])]], ignore_index=True).assign(cell="clean")
        sums = cells(f)
        idx = resample(sums)
        for cond in [LADL, "summary", "pinning", "full"] + E_BASELINES:
            r = test(sums, [(1, "clean", cond)], idx)
            rows.append(dict(model=label, kind="accuracy", condition=cond, diff=r["diff"], lo=r["lo"], hi=r["hi"]))
        for b in E_BASELINES:
            rows.append(dict(model=label, kind="LADL v2 minus", condition=b,
                             **test(sums, [(1, "clean", LADL), (-1, "clean", b)], idx)))
    return pd.DataFrame(rows)


def scale_figure(acc: pd.DataFrame, out: Path):
    plt = setup_mpl()
    conds = ["summary", "pinning", "retrieval", "chrono_hint_v2", LADL, "lifecycle_gold"]
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.8), sharey=True)
    for ax, family_name in zip(axes, ("Qwen", "Mistral")):
        labels = sorted([m for m in set(acc.model) if SIZE[m][0] == family_name], key=lambda m: SIZE[m][1])
        if not labels:
            continue
        xs = [SIZE[m][1] for m in labels]
        for cond in conds:
            sub = acc[acc.condition == cond].set_index("model")
            if not all(m in sub.index for m in labels):
                continue
            ys = [sub.loc[m, "accuracy"] for m in labels]
            ax.plot(xs, ys, marker="o", ms=3.5, lw=1.4, color=COLORS.get(cond.replace("_v2", ""), "#555"),
                    ls="--" if cond == "lifecycle_gold" else "-", label=COND_NAME.get(cond.replace("_v2", ""), cond))
            ax.fill_between(xs, [sub.loc[m, "lo"] for m in labels], [sub.loc[m, "hi"] for m in labels],
                            color=COLORS.get(cond.replace("_v2", ""), "#555"), alpha=0.1, lw=0)
        ax.set_xscale("log")
        ax.set_xticks(xs, [f"{x}B" for x in xs])
        ax.minorticks_off()
        ax.set_title(family_name, fontsize=9, color="#0b0b0b")
        ax.set_xlabel("Parameters")
    axes[0].set_ylabel("Action accuracy (Confirm)")
    handles, labels_ = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels_, loc="lower center", ncol=3, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.17, 1, 1))
    fig.savefig(out / "fig_scale.pdf")
    fig.savefig(out / "fig_scale.png", dpi=200)
    plt.close(fig)


def pct(frame: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = frame.copy()
    cols = [c for c in cols if c in out]
    out[cols] = (out[cols].astype(float) * 100).round(1)
    for c in ("p", "p_holm"):
        if c in out:
            out[c] = out[c].round(4)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_det")
    ap.add_argument("--out", default="results/scale")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = {label: f for label in ALL if (f := clean_frame(root, label)) is not None}
    text = ["# Scale, retrieval, and forged updates", "", "Planned tests follow docs/scale_retrieval_forgery_plan.md.", "",
            f"Models with complete Confirm runs: {', '.join(frames) or 'none'}.", ""]
    d_rows, e_rows = [], []
    for label, f in frames.items():
        sums = cells(f)
        idx = resample(sums)
        if label in LARGE:
            for b in D_BASELINES:
                d_rows.append(dict(family="D", model=label, a=LADL, b=b, prediction="two-sided",
                                   **test(sums, [(1, "clean", LADL), (-1, "clean", b)], idx)))
        for b in E_BASELINES:
            e_rows.append(dict(family="E", model=label, a=LADL, b=b, prediction="two-sided",
                               **test(sums, [(1, "clean", LADL), (-1, "clean", b)], idx)))
    acc = accuracy_table(frames)
    extraction = extraction_table(root, list(ALL))
    f_rows, effects = forged_tables(root, frames)
    decay, caution, ledger = analyses_g(root)
    replication = test_replication(root)
    tables = {"tests_D": family(d_rows), "tests_E": family(e_rows), "tests_F": family(f_rows), "accuracy": acc,
              "test_replication": replication,
              "extraction": extraction, "forged_effects": effects, "decay": decay, "caution": caution, "ledger": ledger}
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False)
    if len(acc):
        scale_figure(acc, out)
        wide = acc.assign(a=(acc.accuracy * 100).round(1)).pivot_table(index="condition", columns="model", values="a")
        wide = wide.reindex([c for c in SHOW if c in wide.index])[[m for m in ALL if m in wide.columns]]
        text += ["## Accuracy on Confirm (%)", "", wide.to_markdown(), ""]
    for name, title in (("tests_D", "Family D: larger models, LADL v2 minus compacted baselines"),
                        ("tests_E", "Family E: LADL v2 minus retrieval baselines"),
                        ("tests_F", "Family F: forged updates, attacked probes")):
        if len(tables[name]):
            text += [f"## {title}", "", pct(tables[name], ["diff", "lo", "hi"]).to_markdown(index=False), ""]
    if len(replication):
        text += ["## Exploratory: retrieval baselines on Test (uncorrected)", "",
                 pct(replication, ["diff", "lo", "hi"]).to_markdown(index=False), ""]
    if len(extraction):
        text += ["## Extraction quality on Confirm", "", extraction.round(3).to_markdown(index=False), ""]
    if len(effects):
        text += ["## Forged updates by condition (attacked probes; other probes as a side-effect check)", "",
                 pct(effects, ["accuracy_forged", "attack_effect", "lo", "hi", "act_forged", "act_clean",
                               "other_probes_effect", "other_lo", "other_hi"]).to_markdown(index=False), ""]
    if len(decay):
        main_conds = ["summary", "pinning", "chrono_hint", "lifecycle", LADL, "lifecycle_gold", "full"]
        d = decay[decay.condition.isin(main_conds)]
        w = d.assign(a=(d.accuracy * 100).round(1)).pivot_table(index=["dataset", "model", "condition"],
                                                                 columns="compactions_since_change", values="a")
        text += ["## G: accuracy by compactions since the item's last change (3 = 3 or more)", "", w.to_markdown(), "",
                 "## G: over-caution and unsafe actions", "",
                 pct(caution[caution.condition.isin(main_conds)], ["over_restriction", "unneeded_clarify", "unsafe_act"]
                     ).to_markdown(index=False), "",
                 "## G: ledger state accuracy against the model's own state answer", "",
                 pct(ledger, ["ledger_state_accuracy", "model_state_accuracy", "decision_accuracy"]).to_markdown(index=False), ""]
    (out / "report.md").write_text("\n".join(text))
    print("\n".join(text[:8]))


if __name__ == "__main__":
    main()
