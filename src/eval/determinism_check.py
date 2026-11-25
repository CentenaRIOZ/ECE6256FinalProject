"""Check that two runs of the same experiment produced identical outputs.

python -m src.eval.determinism_check results/runs/qwen2.5-7b-det1-pace-confirm-v1 results/runs/qwen2.5-7b-det2-pace-confirm-v1

Every probe field except latency must match, and so must the extracted events. Prints one line per run pair and exits
with status 1 if any pair differs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IGNORED = {"latency"}


def records(path: Path) -> dict:
    with path.open() as f:
        rows = [json.loads(line) for line in f]
    return {(r["condition"], r["probe_id"]): {k: v for k, v in r.items() if k not in IGNORED} for r in rows}


def compare(a: Path, b: Path, common_only: bool = False) -> dict:
    out = dict(a=a.name, b=b.name)
    names_a, names_b = {p.name for p in a.glob("probes_B*.jsonl")}, {p.name for p in b.glob("probes_B*.jsonl")}
    unmatched = sorted(names_a ^ names_b)
    if unmatched:
        out["unmatched_files"] = unmatched
    for name in sorted(names_a & names_b):
        probes = a / name
        ra, rb = records(probes), records(b / probes.name)
        differing = [k for k in ra.keys() | rb.keys() if ra.get(k) != rb.get(k)]
        fields = sorted({f for k in differing if k in ra and k in rb for f in ra[k] if ra[k][f] != rb[k].get(f)})
        out[probes.stem] = dict(rows=len(ra), other_rows=len(rb), differing=len(differing), fields=fields)
    ea, eb = a / "extractions.jsonl", b / "extractions.jsonl"
    if ea.exists() or eb.exists():
        out["extractions_identical"] = ea.exists() and eb.exists() and ea.read_bytes() == eb.read_bytes()
    out["identical"] = (all(v["differing"] == 0 and v["rows"] == v["other_rows"]
                            for k, v in out.items() if k.startswith("probes_"))
                        and out.get("extractions_identical", True) and (common_only or not unmatched))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+", help="run directories, two per comparison")
    ap.add_argument("--common-only", action="store_true", help="compare only budgets present in both runs")
    a = ap.parse_args()
    if len(a.pairs) % 2:
        ap.error("give run directories in pairs")
    ok = True
    for x, y in zip(a.pairs[::2], a.pairs[1::2]):
        result = compare(Path(x), Path(y), a.common_only)
        ok &= result["identical"]
        print(json.dumps(result))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
