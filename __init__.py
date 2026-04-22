"""ComfyUI custom-node entry: exports LMStudioNode + the generic OpenAPI nodes."""
try:
    from .node import NODE_CLASS_MAPPINGS as _LMS_CLS, NODE_DISPLAY_NAME_MAPPINGS as _LMS_DNS
except ImportError:
    from node import NODE_CLASS_MAPPINGS as _LMS_CLS, NODE_DISPLAY_NAME_MAPPINGS as _LMS_DNS

try:
    from .comfyui_openapi_node import (
        NODE_CLASS_MAPPINGS as _OAS_CLS,
        NODE_DISPLAY_NAME_MAPPINGS as _OAS_DNS,
    )
except Exception:  # noqa: BLE001
    _OAS_CLS, _OAS_DNS = {}, {}

NODE_CLASS_MAPPINGS = {**_LMS_CLS, **_OAS_CLS}
NODE_DISPLAY_NAME_MAPPINGS = {**_LMS_DNS, **_OAS_DNS}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
