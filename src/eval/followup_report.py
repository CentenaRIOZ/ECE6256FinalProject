"""Experiments B (extraction-noise dose-response) and C (extractor/decision swap) of docs/followup_experiments_plan.md.

python -m src.eval.followup_report --runs results/runs_det --out results/followup

Runs: <model>-pace-confirm-noise-<setting> and <model>-pace-confirm-swap-<extractor>-<version>, plus the deterministic
Confirm runs <model>-pace-confirm-v1 and -v2 for references, real extraction, and the cells where a model uses its own
extraction. All contrasts resample the 52 Confirm timelines jointly for every cell, with 2,000 resamples and seed 0.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.analyze import COLORS, COND_NAME, setup_mpl
from src.eval.extraction_eval import evaluate
from src.eval.followup_settings import CONDITIONS, MATCHED, PRECISIONS, RUNS, noise_settings, suffix, swap_cells
from src.eval.models import MODELS
from src.eval.robustness import REPS, holm, load
from src.extraction.noise import false_events, noisy_gold_events

DATA = "data/confirm/dialogues.jsonl"
FLOOR = 2 / (REPS + 1)
LABEL = {run: label for label, run in MODELS.items()}
REFERENCES = ["summary", "pinning", "summary_hint", "pinning_hint"]
# The gold-event condition of the deterministic run; it differs from perfect extraction only in the item IDs shown.
GOLD = "lifecycle_gold"


def read_jsonl(path: Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f]


def cells(frame: pd.DataFrame) -> pd.DataFrame:
    """Correct and total probes per timeline for every (cell, condition), on the timelines that every cell covers.
    Full runs cover all 52 timelines; a pilot with fewer dialogues is cut to its own timelines."""
    f = frame.assign(correct=(frame.pred_decision == frame.gold_decision).astype(float))
    sums = f.groupby(["cell", "condition", "timeline_id"]).correct.agg(["sum", "size"])
    groups = sums.groupby(level=["cell", "condition"]).ngroups
    seen = sums.groupby(level="timeline_id").size()
    return sums[sums.index.get_level_values("timeline_id").isin(seen[seen == groups].index)]


def contrast(sums: pd.DataFrame, terms: list[tuple[float, str, str]], idx: np.ndarray) -> tuple[float, np.ndarray]:
    """Weighted sum of accuracies, e.g. [(1, s, a), (-1, s, b)], with the same timeline resample for every term."""
    point, boot = 0.0, 0.0
    for w, cell, cond in terms:
        g = sums.loc[(cell, cond)]
        n, m = g["sum"].to_numpy(float), g["size"].to_numpy(float)
        point += w * n.sum() / m.sum()
        boot = boot + w * n[idx].sum(1) / m[idx].sum(1)
    return point, boot


def test(sums: pd.DataFrame, terms, idx) -> dict:
    point, boot = contrast(sums, terms, idx)
    p = 2 * min((boot <= 0).mean(), (boot >= 0).mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return dict(diff=point, lo=lo, hi=hi, p=max(min(1.0, p), FLOOR))


def resample(sums: pd.DataFrame, seed: int = 0) -> np.ndarray:
    timelines = sums.index.get_level_values("timeline_id").unique()
    n = len(timelines)
    # Every (cell, condition) covers the same timelines in the same sorted order, so one index array fits all.
    assert all(len(g) == n for _, g in sums.groupby(level=["cell", "condition"]))
    return np.random.default_rng(seed).integers(0, n, size=(REPS, n))


def with_holm(rows: list[dict]) -> list[dict]:
    for row, adjusted in zip(rows, holm(np.array([r["p"] for r in rows]))):
        row["p_holm"] = adjusted
        sign = {"positive": row["diff"] > 0, "negative": row["diff"] < 0, "two-sided": True}[row["prediction"]]
        row["result"] = bool(adjusted < 0.05 and sign)
    return rows


def det_run(root: Path, run: str, version: str) -> pd.DataFrame:
    return load(str(root / f"{run}-pace-confirm-{version}"), 384)


# --------------------------------------------------------------------------------------------- experiment B
def noise_frame(root: Path, run: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Probes of every noise setting, the real-extraction runs, and the event-free references; and a settings table."""
    frames, settings = [], []
    dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(DATA))}
    for p, r, seed, kind in noise_settings(run):
        name = suffix(p, r, seed)
        path = root / f"{run}-pace-confirm-noise-{name}"
        if not (path / "probes_B384.jsonl").exists():
            continue
        extracted = {x["dialogue_id"]: x["events"] for x in read_jsonl(path / "extractions.jsonl")}
        regenerated = all(noisy_gold_events(dialogues[k], p, r, seed)[0] == v for k, v in extracted.items())
        q = evaluate(dialogues, [dict(dialogue_id=k, events=v) for k, v in extracted.items()])
        settings.append(dict(model=LABEL[run], cell=name, kind=kind, precision=p, recall=r, seed=seed,
                             realized_precision=q["precision"], realized_recall=q["recall"],
                             events_match_generator=regenerated))
        frames.append(load(str(path), 384).assign(cell=name))
    for version in ("v1", "v2"):
        real = det_run(root, run, version)
        frames.append(real[real.condition.isin(CONDITIONS)].assign(cell=f"real-{version}"))
    v1 = det_run(root, run, "v1")
    frames.append(v1[v1.condition.isin(REFERENCES + [GOLD])].assign(cell="reference"))
    return pd.concat(frames, ignore_index=True), pd.DataFrame(settings)


def false_event_exposure(frame: pd.DataFrame, run: str) -> pd.DataFrame:
    """Accuracy on probes whose item got a false event before the probe, against all other probes."""
    dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(DATA))}
    rows = []
    for p, r, seed, kind in noise_settings(run):
        if p == 1.0:
            continue
        name = suffix(p, r, seed)
        sub = frame[frame.cell == name]
        if sub.empty:
            continue
        added = {k: false_events(d, p, r, seed) for k, d in dialogues.items()}

        def hit(row):
            item = dialogues[row.dialogue_id]["items"][row["item"]]
            return any(t <= row.after_turn and (ev["item"] == row["item"]
                                               or (ev["op"] in ("commit", "prohibit") and ev["tool"] == item["tool"]))
                       for t, ev in added[row.dialogue_id])

        exposed = sub.apply(hit, axis=1)
        correct = sub.pred_decision == sub.gold_decision
        for cond in CONDITIONS:
            c = sub.condition == cond
            rows.append(dict(model=LABEL[run], cell=name, condition=cond, exposed_share=exposed[c].mean(),
                             accuracy_exposed=correct[c & exposed].mean(), accuracy_other=correct[c & ~exposed].mean(),
                             wrong_share_exposed=(~correct[c] & exposed[c]).sum() / max(1, (~correct[c]).sum())))
    return pd.DataFrame(rows)


def break_even(sums: pd.DataFrame, idx: np.ndarray, reference: str) -> dict:
    """Precision at which LADL equals a reference, by linear interpolation over the precision grid (recall 1)."""
    grid = [(1.0, suffix(1.0, 1.0))] + [(p, suffix(p, 1.0)) for p in PRECISIONS]
    diffs = [contrast(sums, [(1, cell, "lifecycle"), (-1, "reference", reference)], idx) for _, cell in grid]

    def cross(values: list[float]) -> float:
        if values[0] < 0:
            return 1.0  # LADL is below the reference even with perfect extraction
        for (p0, _), (p1, _), d0, d1 in zip(grid, grid[1:], values, values[1:]):
            if d1 < 0:
                return p1 + (p0 - p1) * (0 - d1) / (d0 - d1)
        return grid[-1][0]  # never below the reference on the grid
    point = cross([d[0] for d in diffs])
    boot = np.array([cross([d[1][i] for d in diffs]) for i in range(len(idx))])
    return dict(reference=reference, break_even=point, lo=np.percentile(boot, 2.5), hi=np.percentile(boot, 97.5),
                at_grid_floor=point == grid[-1][0], above_grid=point == 1.0)


def noise_figure(curves: pd.DataFrame, settings: pd.DataFrame, out: Path):
    """Accuracy against nominal precision (top) and recall (bottom), with event-free references and real extractors."""
    plt = setup_mpl()
    models = [m for m in MODELS if m in set(curves.model)]
    fig, axes = plt.subplots(2, len(models), figsize=(3.3 * len(models), 5.2), sharey=True, squeeze=False)
    for col, model in enumerate(models):
        c = curves[curves.model == model].set_index(["cell", "condition"])
        st = settings[(settings.model == model) & (settings.seed == 0)]
        run = MODELS[model]
        for row, (kind, axis) in enumerate((("false events", "precision"), ("missed events", "recall"))):
            ax = axes[row][col]
            pts = st[st.kind.isin(["perfect", kind])].sort_values(axis)
            for cond in CONDITIONS:
                y = [c.loc[(cell, cond)] for cell in pts.cell]
                ax.plot(pts[axis], [v.accuracy for v in y], marker="o", ms=3, lw=1.3, color=COLORS[cond],
                        ls="--" if cond.endswith("nohint") or cond == "chrono" else "-", label=COND_NAME[cond])
                ax.fill_between(pts[axis], [v.lo for v in y], [v.hi for v in y], color=COLORS[cond], alpha=0.12, lw=0)
            for ref, ls in (("summary", ":"), ("pinning", "-.")):
                ax.axhline(c.loc[("reference", ref)].accuracy, color=COLORS[ref], ls=ls, lw=1, label=COND_NAME[ref])
            if axis == "precision":
                for version, (p, _) in MATCHED[run].items():
                    v = c.loc[(f"real-{version}", "lifecycle")].accuracy
                    ax.scatter([p], [v], marker="*", s=60, color="#0b0b0b", zorder=5,
                               label="LADL, real extraction" if version == "v1" else None)
                    ax.annotate(version, (p, v), textcoords="offset points", xytext=(4, -9), fontsize=7)
            ax.set_xlim(1.02, 0.38 if axis == "precision" else 0.48)
            ax.set_xlabel(f"Event {axis} ({kind}, other rate 1.0)")
            if col == 0:
                ax.set_ylabel("Action accuracy")
            if row == 0:
                ax.set_title(model, fontsize=9, color="#0b0b0b")
    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=7.5)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(out / "fig_noise.pdf")
    fig.savefig(out / "fig_noise.png", dpi=200)
    plt.close(fig)


def experiment_b(root: Path, out: Path) -> list[str]:
    tests, curves, settings, extra, exposure = [], [], [], [], []
    for run in RUNS:
        if not (root / f"{run}-pace-confirm-noise-{suffix(1.0, 1.0)}" / "probes_B384.jsonl").exists():
            continue
        frame, setting_table = noise_frame(root, run)
        settings.append(setting_table)
        sums = cells(frame)
        idx = resample(sums)
        label, perfect = LABEL[run], suffix(1.0, 1.0)
        for (cell, cond), g in sums.groupby(level=["cell", "condition"]):
            r = test(sums, [(1, cell, cond)], idx)
            curves.append(dict(model=label, cell=cell, condition=cond, accuracy=r["diff"], lo=r["lo"], hi=r["hi"]))
        planned = {"B1": ("negative", suffix(0.5, 1.0), "lifecycle_nohint"),
                   "B2": ("two-sided", suffix(0.5, 1.0), "chrono_hint"),
                   "B3": ("two-sided", suffix(1.0, 0.7), "chrono_hint")}
        for name, (prediction, cell, other) in planned.items():
            if cell not in sums.index.get_level_values("cell"):
                continue
            terms = [(1, cell, "lifecycle"), (-1, cell, other), (-1, perfect, "lifecycle"), (1, perfect, other)]
            tests.append(dict(family="B", test=name, model=label, setting=cell, a="lifecycle", b=other,
                              prediction=prediction, **test(sums, terms, idx)))
        for ref in ("summary", "pinning"):
            if suffix(0.4, 1.0) in sums.index.get_level_values("cell"):
                extra.append(dict(model=label, analysis="break-even precision", **break_even(sums, idx, ref)))
        for version, (p, r) in MATCHED[run].items():
            cell = suffix(p, r)
            if cell in sums.index.get_level_values("cell"):
                for cond in CONDITIONS:
                    extra.append(dict(model=label, analysis=f"real minus matched {version}", condition=cond,
                                      **test(sums, [(1, f"real-{version}", cond), (-1, cell, cond)], idx)))
        # Exploratory, added after results were seen: gold item IDs (such as F0P) against I1, I2, ...
        extra.append(dict(model=label, analysis="perfect extraction minus gold condition (exploratory)",
                          condition="lifecycle", **test(sums, [(1, perfect, "lifecycle"), (-1, "reference", GOLD)], idx)))
        if suffix(0.5, 1.0, 1) in sums.index.get_level_values("cell"):
            for cond in CONDITIONS:
                extra.append(dict(model=label, analysis="seed 1 minus seed 0 at precision 0.5", condition=cond,
                                  **test(sums, [(1, suffix(0.5, 1.0, 1), cond), (-1, suffix(0.5, 1.0), cond)], idx)))
        exposure.append(false_event_exposure(frame, run))
    if not curves:
        return []
    tests = pd.DataFrame(with_holm(tests))
    curves, settings = pd.DataFrame(curves), pd.concat(settings, ignore_index=True)
    extra, exposure = pd.DataFrame(extra), pd.concat(exposure, ignore_index=True)
    for name, table in (("noise_tests", tests), ("noise_curves", curves), ("noise_settings", settings),
                        ("noise_analyses", extra), ("noise_exposure", exposure)):
        table.to_csv(out / f"{name}.csv", index=False)
    noise_figure(curves, settings, out)
    wide = curves.assign(acc=(curves.accuracy * 100).round(1)).pivot_table(index=["model", "cell"], columns="condition",
                                                                            values="acc").reset_index()
    return ["## Experiment B: extraction-noise dose-response", "",
            "### Planned tests (family B, Holm over all tests below)", "", pct(tests).to_markdown(index=False), "",
            "### Settings", "", settings.round(3).to_markdown(index=False), "",
            "### Accuracy (%)", "", wide.to_markdown(index=False), "",
            "### Break-even, matched noise, and seed check", "", pct(extra).to_markdown(index=False), "",
            "### Probes whose item received a false event", "", exposure.round(3).to_markdown(index=False), ""]


# --------------------------------------------------------------------------------------------- experiment C
def swap_frame(root: Path, decider: str) -> pd.DataFrame:
    frames = []
    for version in ("v1", "v2"):
        own = det_run(root, decider, version)
        frames.append(own[own.condition.isin(CONDITIONS)].assign(cell=f"{decider}-{version}"))
    for extractor, version in swap_cells(decider):
        path = root / f"{decider}-pace-confirm-swap-{extractor}-{version}"
        if (path / "probes_B384.jsonl").exists():
            frames.append(load(str(path), 384).assign(cell=f"{extractor}-{version}"))
    v1 = det_run(root, decider, "v1")
    frames.append(v1[v1.condition.isin(REFERENCES)].assign(cell="reference"))
    return pd.concat(frames, ignore_index=True)


def swap_sources(root: Path) -> pd.DataFrame:
    dialogues = {d["dialogue_id"]: d for d in read_jsonl(Path(DATA))}
    rows = []
    for run in RUNS:
        for version in ("v1", "v2"):
            ex = read_jsonl(root / f"{run}-pace-confirm-{version}" / "extractions.jsonl")
            q = evaluate(dialogues, ex)
            rows.append(dict(extractor=LABEL[run], version=version, precision=q["precision"], recall=q["recall"],
                             f1=q["f1"]))
    return pd.DataFrame(rows)


def experiment_c(root: Path, out: Path) -> list[str]:
    if not any((root / f"{d}-pace-confirm-swap-{e}-{v}" / "probes_B384.jsonl").exists()
               for d in RUNS for e, v in swap_cells(d)):
        return []
    frames = {d: swap_frame(root, d) for d in RUNS}
    tests, table = [], []
    for decider, frame in frames.items():
        sums = cells(frame)
        idx = resample(sums)
        present = set(sums.index.get_level_values("cell"))
        for (cell, cond), _ in sums.groupby(level=["cell", "condition"]):
            if cell == "reference":
                continue
            r = test(sums, [(1, cell, cond)], idx)
            extractor, version = cell.rsplit("-", 1)
            table.append(dict(decider=LABEL[decider], extractor=LABEL[extractor], version=version, condition=cond,
                              accuracy=r["diff"], lo=r["lo"], hi=r["hi"]))
        planned = []
        if decider == "mistral-7b-v0.3":
            for other in ("qwen2.5-7b", "llama3.1-8b"):
                for v in ("v1", "v2"):
                    planned.append(("positive", f"{other}-{v}", "lifecycle", f"{decider}-{v}", "lifecycle"))
            for other in ("qwen2.5-7b", "llama3.1-8b"):
                for ref in ("summary", "pinning"):
                    planned.append(("positive", f"{other}-v2", "lifecycle", "reference", ref))
        else:
            for v in ("v1", "v2"):
                planned.append(("negative", f"mistral-7b-v0.3-{v}", "lifecycle", f"{decider}-{v}", "lifecycle"))
        for prediction, cell_a, cond_a, cell_b, cond_b in planned:
            if {cell_a, cell_b} <= present:
                tests.append(dict(family="C", decider=LABEL[decider], a=f"{cell_a}:{cond_a}", b=f"{cell_b}:{cond_b}",
                                  prediction=prediction, **test(sums, [(1, cell_a, cond_a), (-1, cell_b, cond_b)], idx)))
    tests, table = pd.DataFrame(with_holm(tests)), pd.DataFrame(table)
    sources = swap_sources(root)
    ladl = table[table.condition == "lifecycle"].copy()
    ladl["source"] = ladl.extractor + " " + ladl.version
    grid = ladl.pivot_table(index="decider", columns="source", values="accuracy")
    # Additive decomposition of the LADL table: how much of the spread follows the extractor or the decider.
    centered = grid - grid.values.mean()
    ss_decider = (centered.mean(axis=1) ** 2).sum() * grid.shape[1]
    ss_source = (centered.mean(axis=0) ** 2).sum() * grid.shape[0]
    ss_total = (centered.values ** 2).sum()
    decomposition = pd.DataFrame([dict(share_decider=ss_decider / ss_total, share_extraction=ss_source / ss_total,
                                       share_interaction=1 - (ss_decider + ss_source) / ss_total)])
    for name, t in (("swap_tests", tests), ("swap_accuracy", table), ("swap_sources", sources),
                    ("swap_decomposition", decomposition)):
        t.to_csv(out / f"{name}.csv", index=False)
    wide = table.assign(acc=(table.accuracy * 100).round(1)).pivot_table(
        index=["decider", "condition"], columns=["extractor", "version"], values="acc")
    return ["## Experiment C: swapping extractor and decision model", "",
            "### Planned tests (family C, Holm over all tests below)", "", pct(tests).to_markdown(index=False), "",
            "### Extraction sources", "", sources.round(3).to_markdown(index=False), "",
            "### Accuracy (%) by decision model and extraction source", "", wide.to_markdown(), "",
            "### Share of the LADL accuracy spread (exploratory)", "", decomposition.round(3).to_markdown(index=False), ""]


def pct(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    cols = [c for c in ("diff", "lo", "hi") if c in out]
    out[cols] = (out[cols].astype(float) * 100).round(1)
    for c in ("p", "p_holm"):
        if c in out:
            out[c] = out[c].round(4)
    if "break_even" in out:
        out["break_even"] = out.break_even.round(3)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs_det")
    ap.add_argument("--out", default="results/followup")
    ap.add_argument("--experiment", choices=["noise", "swap", "all"], default="all")
    a = ap.parse_args()
    root, out = Path(a.runs), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    text = ["# Follow-up experiments B and C", "", "Planned tests follow docs/followup_experiments_plan.md.", ""]
    if a.experiment in ("noise", "all"):
        text += experiment_b(root, out)
    if a.experiment in ("swap", "all"):
        text += experiment_c(root, out)
    (out / f"report_{a.experiment}.md").write_text("\n".join(text))
    print("\n".join(text))


if __name__ == "__main__":
    main()
