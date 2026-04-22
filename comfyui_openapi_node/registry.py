"""ComfyUI NODE_CLASS_MAPPINGS entry point.

Registers:
  * `OpenAPINode` — the universal node (generic values_json input)
  * One typed subclass per operation of each bundled preset. The
    subclass's INPUT_TYPES / RETURN_TYPES / RETURN_NAMES are produced
    by binding.py from the operation's JSON Schema — so each slot is
    properly typed (STRING / INT / FLOAT / BOOLEAN / enum) instead of
    a values_json blob.

The generation is cheap — parse YAML once at import — and tolerates
broken specs (logs + skips, never blocks import).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Type

from .binding import (
    operation_to_input_types,
    operation_to_return_types,
)
from .node import OpenAPINode, find_operation
from .presets import PRESETS
from .protocols import get_executor

log = logging.getLogger(__name__)

NODE_CLASS_MAPPINGS: Dict[str, Type] = {"OpenAPINode": OpenAPINode}
NODE_DISPLAY_NAME_MAPPINGS: Dict[str, str] = {"OpenAPINode": "API — Generic"}


def _make_typed_subclass(preset_name: str, spec: dict, op_id: str,
                         path: str, method: str) -> type:
    op, _, _ = find_operation(spec, op_id)
    components = spec.get("components") or {}
    input_types = operation_to_input_types(op, components)
    return_types, return_names = operation_to_return_types(op, components)
    server_url_default = (spec.get("servers") or [{}])[0].get("url", "")

    class _Typed(OpenAPINode):  # type: ignore[misc]
        CATEGORY = f"API/{preset_name}"
        FUNCTION = "invoke_typed"
        RETURN_TYPES = return_types
        RETURN_NAMES = return_names

        @classmethod
        def INPUT_TYPES(cls, _it=input_types, _server=server_url_default):
            it = {
                "required": dict(_it["required"]),
                "optional": dict(_it["optional"]),
            }
            it["optional"]["server_url"] = ("STRING", {"default": _server})
            it["optional"]["auth_scheme"] = ("STRING", {"default": ""})
            it["optional"]["credentials_json"] = ("STRING", {"default": "{}", "multiline": True})
            return it

        def invoke_typed(self, _op=op, _spec=spec, _method=method,
                         _path=path, server_url="", auth_scheme="",
                         credentials_json="{}", **values) -> tuple:
            try:
                chosen_server = server_url or (
                    (_spec.get("servers") or [{}])[0].get("url", "") or ""
                )
                creds = json.loads(credentials_json or "{}")
                scheme = None
                if auth_scheme:
                    scheme = (_spec.get("components", {})
                                    .get("securitySchemes", {})
                                    .get(auth_scheme))

                # Reassemble: parameters stay top-level; requestBody
                # properties nest under "body" for the HTTP executor.
                param_names = {p.get("name") for p in (_op.get("parameters") or [])}
                body_props = {}
                top_level = {}
                for k, v in values.items():
                    if k in param_names:
                        top_level[k] = v
                    else:
                        body_props[k] = v
                call_values = dict(top_level)
                if body_props:
                    call_values["body"] = body_props

                resp = get_executor("http")(
                    operation=_op, method=_method, server_url=chosen_server,
                    path=_path, values=call_values,
                    auth_scheme=scheme, credentials=creds,
                )
                # Extract typed outputs from the JSON body if possible.
                typed_slots: list = []
                try:
                    decoded = json.loads(resp.body) if resp.body else {}
                except (ValueError, TypeError):
                    decoded = {}
                for name in self.RETURN_NAMES[:-3]:  # exclude canonical tail
                    typed_slots.append(decoded.get(name, "") if isinstance(decoded, dict) else "")
                tail = resp.as_tuple()  # (body, stats, headers)
                return tuple(typed_slots) + tail
            except Exception as e:  # noqa: BLE001
                tail = (f"Error: {e}", "HTTP 0\nBytes: 0", "{}")
                blanks = tuple("" for _ in self.RETURN_NAMES[:-3])
                return blanks + tail

    return _Typed


def _register_preset(preset_name: str, spec: dict) -> None:
    for path, item in (spec.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if not isinstance(op, dict) or not op.get("operationId"):
                continue
            op_id = op["operationId"]
            cls_name = f"OpenAPI_{preset_name.replace('-', '_')}_{op_id}"
            try:
                cls = _make_typed_subclass(preset_name, spec, op_id, path, method.upper())
            except Exception as e:  # noqa: BLE001
                log.warning("could not bind %s:%s — %s", preset_name, op_id, e)
                continue
            cls.__name__ = cls_name
            NODE_CLASS_MAPPINGS[cls_name] = cls
            NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"API · {preset_name} · {op_id}"


for _name, _preset in PRESETS.items():
    try:
        _register_preset(_name, _preset.spec())
    except Exception as e:  # noqa: BLE001
        log.warning("preset %r failed to register: %s", _name, e)
