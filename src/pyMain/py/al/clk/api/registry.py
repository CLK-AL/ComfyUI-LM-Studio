"""ComfyUI NODE_CLASS_MAPPINGS entry point.

Registers:
  * `OpenAPINode`                               — universal generic node
  * `API_<preset>_<operationId>` subclasses      — one per operation of
                                                   each bundled preset

Both routes through the JSON-Schema pivot:

    preset.spec()  ──▶  to_jsonschema.<kind>.convert()  ──▶  Canonical
                                                         │
                       binding.canonical_op_to_*         ▼
                                            ComfyUI INPUT_TYPES /
                                            RETURN_TYPES / RETURN_NAMES

That means adding AsyncAPI needs nothing here — the `kind` on the
preset picks the converter and the rest is identical to OpenAPI.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Type

from typing import Mapping

from .binding import (
    canonical_op_to_input_types,
    canonical_op_to_return_types,
)
from .node import OpenAPINode
from .presets import PRESETS
from .protocols import get_executor
from .security import apply as apply_security
from .to_jsonschema import Canonical, OperationSchema
from .to_jsonschema import asyncapi as conv_asyncapi
from .to_jsonschema import jdbc     as conv_jdbc
from .to_jsonschema import openapi  as conv_openapi

log = logging.getLogger(__name__)

NODE_CLASS_MAPPINGS: Dict[str, Type] = {"OpenAPINode": OpenAPINode}
NODE_DISPLAY_NAME_MAPPINGS: Dict[str, str] = {"OpenAPINode": "API — Generic"}

_CONVERTERS = {
    "openapi":  conv_openapi.convert,
    "asyncapi": conv_asyncapi.convert,
    "jdbc":     conv_jdbc.convert,
}

# Protocol hint per spec kind. The per-op record can override.
_DEFAULT_PROTOCOL = {
    "openapi":  "http",
    "asyncapi": "wss",
    "graphql":  "http",
    "mcp":      "http",
    "jdbc":     "jdbc",   # protocols/jdbc.py delegates to the Spring Kotlin mock
}


def _make_typed_subclass(preset_name: str, canon: Canonical,
                         op: OperationSchema, kind: str) -> type:
    components = dict(canon.get("components") or {})
    input_types = canonical_op_to_input_types(op, components)
    return_types, return_names = canonical_op_to_return_types(op, components)
    server_url_default = canon.get("server_url", "") or ""
    protocol_default = op.get("protocol") or _DEFAULT_PROTOCOL.get(kind, "http")
    method_default   = op.get("verb") or "POST"
    path_default     = op.get("path") or "/"

    # Security surface for this operation: op-level `security` overrides
    # top-level; fall back to every scheme declared in the spec so the
    # user still has a choice when the op has no explicit requirement.
    all_schemes = dict(canon.get("security_schemes") or {})
    op_reqs = op.get("raw", {}).get("security") or canon.get("default_security") or []
    op_scheme_names: list[str] = []
    for req in op_reqs:
        if isinstance(req, Mapping):
            for n in req.keys():
                if n in all_schemes and n not in op_scheme_names:
                    op_scheme_names.append(n)
    scheme_choices = ([""] + op_scheme_names) if op_scheme_names else ([""] + list(all_schemes.keys()))

    class _Typed(OpenAPINode):  # type: ignore[misc]
        CATEGORY = f"API/{preset_name}"
        FUNCTION = "invoke_typed"
        RETURN_TYPES = return_types
        RETURN_NAMES = return_names

        @classmethod
        def INPUT_TYPES(cls, _it=input_types, _server=server_url_default,
                         _choices=scheme_choices):
            it = {"required": dict(_it["required"]),
                  "optional": dict(_it["optional"])}
            it["optional"]["server_url"]       = ("STRING", {"default": _server})
            it["optional"]["auth_scheme"]      = (list(_choices),)
            it["optional"]["credentials_json"] = ("STRING", {"default": "{}", "multiline": True})
            return it

        def invoke_typed(self, _op=op, _kind=kind, _protocol=protocol_default,
                         _method=method_default, _path=path_default,
                         _server=server_url_default,
                         _schemes=all_schemes,
                         server_url="", auth_scheme="",
                         credentials_json="{}", **values):
            try:
                chosen_server = server_url or _server
                creds = json.loads(credentials_json or "{}")

                # Demux: parameter names vs. request-body properties.
                param_names = {p.get("name") for p in (_op.get("parameters") or [])}
                body_props, top_level = {}, {}
                for k, v in values.items():
                    (top_level if k in param_names else body_props)[k] = v
                call_values = dict(top_level)
                if body_props:
                    call_values["body"] = body_props

                # Synthesize a minimal OpenAPI-flavoured operation for the
                # HTTP/WS executors (they expect that shape).
                exec_op = dict(_op.get("raw") or {})
                if _kind == "asyncapi" and "parameters" not in exec_op:
                    # Channels don't have classical parameters; carry the
                    # template placeholders if any.
                    exec_op["parameters"] = _op.get("parameters") or []

                # Resolve the selected auth scheme (dropdown) from the
                # spec and hand it to the executor. Empty string → no auth.
                scheme = _schemes.get(auth_scheme) if auth_scheme else None

                executor = get_executor(_protocol)
                resp = executor(
                    operation=exec_op, method=_method, server_url=chosen_server,
                    path=_path, values=call_values,
                    auth_scheme=scheme, credentials=creds,
                )

                try:
                    decoded = json.loads(resp.body) if resp.body else {}
                except (ValueError, TypeError):
                    decoded = {}
                typed_slots: list = []
                for name in self.RETURN_NAMES[:-3]:
                    typed_slots.append(decoded.get(name, "") if isinstance(decoded, dict) else "")
                tail = resp.as_tuple()
                return tuple(typed_slots) + tail
            except Exception as e:  # noqa: BLE001
                tail = (f"Error: {e}", "HTTP 0\nBytes: 0", "{}")
                blanks = tuple("" for _ in self.RETURN_NAMES[:-3])
                return blanks + tail

    return _Typed


def _register_preset(preset_name: str, preset) -> None:
    kind = preset.kind
    conv = _CONVERTERS.get(kind)
    if conv is None:
        log.warning("no converter for kind=%r; skipping preset %r", kind, preset_name)
        return
    canon = conv(preset.spec())
    for op in canon.get("operations") or []:
        op_id = op.get("id")
        if not op_id:
            continue
        cls_name = f"API_{preset_name.replace('-', '_')}_{op_id}"
        try:
            cls = _make_typed_subclass(preset_name, canon, op, kind)
        except Exception as e:  # noqa: BLE001
            log.warning("could not bind %s:%s — %s", preset_name, op_id, e)
            continue
        cls.__name__ = cls_name
        NODE_CLASS_MAPPINGS[cls_name] = cls
        NODE_DISPLAY_NAME_MAPPINGS[cls_name] = f"API · {preset_name} · {op_id}"


for _name, _preset in PRESETS.items():
    try:
        _register_preset(_name, _preset)
    except Exception as e:  # noqa: BLE001
        log.warning("preset %r failed to register: %s", _name, e)
