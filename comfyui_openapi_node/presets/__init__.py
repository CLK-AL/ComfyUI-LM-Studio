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
REPO = HERE.parents[1]
API_ROOT = REPO / "api"


def _file(p: Path) -> Callable[[], dict]:
    return lambda: load_spec(p)


# The spec bodies live under /api/<kind>/spec/ — single source of truth
# shared with the jbang mock facade. Each preset names its kind so new
# spec types (AsyncAPI / GraphQL / MCP manifests) slot in next to it.
PRESETS: dict[str, Preset] = {
    "lm-studio": Preset(
        name="lm-studio",
        title="LM Studio",
        description="Local LM Studio REST API (chat/completions + models).",
        spec=_file(API_ROOT / "openapi" / "spec" / "lm-studio.yaml"),
    ),
}
