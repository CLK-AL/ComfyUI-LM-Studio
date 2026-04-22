"""al.clk.api — OpenAPI-driven ComfyUI node package.

Moved out of `comfyui_openapi_node/` into a KMP-style layout
(`src/pyMain/py/al/clk/api/`) that mirrors the Kotlin side at
`api/src/commonMain/kotlin/al/clk/api/` and the proto at
`api/src/proto/al/clk/api/types.proto`. The ComfyUI-facing package
`comfyui_openapi_node/` stays on disk as a thin shell that
re-exports from here so ComfyUI's `custom_nodes/` discovery keeps
working.
"""
from .registry import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
