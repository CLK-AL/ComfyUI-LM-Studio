"""ComfyUI custom-node entry point — thin shell.

ComfyUI scans `custom_nodes/<package>/__init__.py` for
`NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`. This file
keeps the expected discovery surface while delegating every class
definition to the KMP-laid-out `al.clk.api` package in
`src/pyMain/py/al/clk/api/`.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src" / "pyMain" / "py"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from al.clk.api import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS  # noqa: E402

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
