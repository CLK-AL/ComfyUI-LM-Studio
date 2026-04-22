"""ComfyUI NODE_CLASS_MAPPINGS entry point.

Registers:
  * `OpenAPINode`               — the universal node (pick spec at runtime)
  * `OpenAPI:<preset>:<opId>`   — one convenience subclass per operation
                                   of each bundled preset, with spec /
                                   operation / protocol / method pre-filled.

The subclass generation is cheap — parsing YAML once at import time —
and stays silent on bad specs (errors are logged and the subclass is
skipped so one broken preset doesn't take out the whole module).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Type

from .node import OpenAPINode
from .presets import PRESETS

log = logging.getLogger(__name__)

NODE_CLASS_MAPPINGS: Dict[str, Type] = {"OpenAPINode": OpenAPINode}
NODE_DISPLAY_NAME_MAPPINGS: Dict[str, str] = {"OpenAPINode": "OpenAPI — Generic"}


def _register_preset(preset_name: str, spec: dict) -> None:
    for path, item in (spec.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if not isinstance(op, dict) or not op.get("operationId"):
                continue
            op_id = op["operationId"]
            cls_name = f"OpenAPI_{preset_name.replace('-', '_')}_{op_id}"

            class _Pre(OpenAPINode):  # type: ignore[misc]
                @classmethod
                def INPUT_TYPES(cls, _method=method.upper(),
                                _preset=preset_name, _op=op_id,
                                _base=OpenAPINode):
                    base = _base.INPUT_TYPES()
                    # Pre-fill the three routing inputs so the user only
                    # needs to supply values_json (and optional auth).
                    base["required"]["spec_source"]  = ("STRING", {"default": f"preset:{_preset}", "multiline": False})
                    base["required"]["operation_id"] = ("STRING", {"default": _op, "multiline": False})
                    base["required"]["method"]       = (["GET", "POST", "PUT", "DELETE", "PATCH",
                                                         "HEAD", "OPTIONS", "PROPFIND", "PROPPATCH",
                                                         "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK",
                                                         "REPORT"], {"default": _method})
                    return base

            _Pre.__name__ = cls_name
            NODE_CLASS_MAPPINGS[cls_name] = _Pre
            NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"OpenAPI · {preset_name} · {op_id}"


for _name, _preset in PRESETS.items():
    try:
        _register_preset(_name, _preset.spec())
    except Exception as e:  # noqa: BLE001
        log.warning("preset %r failed to register: %s", _name, e)
