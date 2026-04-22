"""Built-in spec presets. LM Studio is intentionally first — drop the
node into a workflow, pick `preset:lm-studio`, and everything wires up
against the LM Studio REST API on localhost.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..loader import load_spec


@dataclass
class Preset:
    name: str
    title: str
    description: str
    spec: Callable[[], dict]


HERE = Path(__file__).resolve().parent


def _file(p: Path) -> Callable[[], dict]:
    return lambda: load_spec(p)


PRESETS: dict[str, Preset] = {
    "lm-studio": Preset(
        name="lm-studio",
        title="LM Studio",
        description="Local LM Studio REST API (chat/completions + models).",
        spec=_file(HERE / "lm-studio.yaml"),
    ),
}
