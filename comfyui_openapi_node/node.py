"""Thin shell — the real `OpenAPINode` lives at
`src/pyMain/py/al/clk/api/node.py`. Kept here because many downstream
scripts and ComfyUI workflow JSONs import `comfyui_openapi_node.node`
by path. New code should `from al.clk.api.node import OpenAPINode`.

Importing `comfyui_openapi_node.node` triggers the parent package's
`__init__.py` first, which registers `src/pyMain/py/` on `sys.path`.
"""
from __future__ import annotations

from al.clk.api.node import *  # noqa: F401,F403
from al.clk.api.node import OpenAPINode  # noqa: F401
