"""ComfyUI-OpenAPI-Node — turn any OpenAPI spec into ComfyUI nodes.

This package is laid out so it can be split into its own repository
later. Nothing here depends on the sibling `node.py` (LMStudioNode) —
but `node.py`'s LM Studio stub OpenAPI is bundled as the first preset
so a user can drop the node into a workflow and hit LM Studio without
writing any YAML.

Public API:
    from comfyui_openapi_node import NODE_CLASS_MAPPINGS,
                                      NODE_DISPLAY_NAME_MAPPINGS
"""
from .registry import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
