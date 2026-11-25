"""Expose tagged runs under the standard run names, so every report can read them with --runs.

python -m src.eval.tagged_runs --tag=-det1 --out results/runs_det

For each run folder <model><tag>-pace-..., the output folder gets a link named <model>-pace-.... Runs without a tagged
version are linked unchanged; this covers the original local runs, which were never rerun on PACE-ICE.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.eval.models import MODELS


def is_tagged(name: str) -> bool:
    """True for <model><something>-pace-..., such as reruns; the original local runs have no -pace- part."""
    return any(name.startswith(f"{m}-") and not name.startswith(f"{m}-pace-") and "-pace-" in name for m in MODELS.values())


def build(runs: Path, tag: str, out: Path) -> dict[str, str]:
    out.mkdir(parents=True, exist_ok=True)
    for link in out.iterdir():
        if link.is_symlink():
            link.unlink()
    folders = sorted(p for p in runs.iterdir() if p.is_dir())
    chosen = {p.name: p for p in folders if not is_tagged(p.name)}
    for run in folders:
        for model in MODELS.values():
            # A tagged run replaces the original only once it has finished writing probes.
            if run.name.startswith(f"{model}{tag}-pace-") and any(run.glob("probes_B*.jsonl")):
                chosen[run.name.replace(f"{model}{tag}-pace-", f"{model}-pace-", 1)] = run
    for name, target in chosen.items():
        os.symlink(os.path.relpath(target.resolve(), out.resolve()), out / name)
    return {name: target.name for name, target in chosen.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/runs")
    ap.add_argument("--tag", required=True, help="run-name tag, for example -det1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    mapping = build(Path(a.runs), a.tag, Path(a.out))
    tagged = sum(1 for k, v in mapping.items() if k != v)
    print(f"{len(mapping)} runs linked in {a.out}, {tagged} from tag {a.tag}")


if __name__ == "__main__":
    main()
