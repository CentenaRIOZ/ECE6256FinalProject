"""Model labels and run-name prefixes shared by the post-milestone reports."""
from __future__ import annotations

from pathlib import Path

MODELS = {"Qwen": "qwen2.5-7b", "Llama": "llama3.1-8b", "Mistral": "mistral-7b-v0.3"}


def available(root: Path, suffixes: list[str], budget: int = 384) -> dict[str, str]:
    """Models whose runs exist for every suffix, so a report still works before the Mistral runs finish."""
    return {label: run for label, run in MODELS.items()
            if all((root / f"{run}{s}" / f"probes_B{budget}.jsonl").exists() for s in suffixes)}
