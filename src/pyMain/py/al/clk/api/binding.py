"""Bind API-spec operations to the ComfyUI node spec.

Input:  one operation from an OpenAPI spec, plus its spec's components.
Output: (INPUT_TYPES, RETURN_TYPES, RETURN_NAMES) that ComfyUI can consume.

The translation is the heart of the project: arbitrary JSON Schema →
ComfyUI's tiny closed vocabulary (STRING/INT/FLOAT/BOOLEAN + enum
tuples). What doesn't fit cleanly (nested objects, oneOf, $ref chains
with cycles, etc.) falls through to a multiline STRING JSON blob so
nothing is silently dropped.

Extension points — add another spec kind (AsyncAPI channel, GraphQL
field, gRPC method, MCP tool) by writing a small adapter that produces
the same (operation-like dict, components-like dict) pair and calling
operation_to_input_types / operation_to_return_types here.
"""
from __future__ import annotations

import re
from typing import Any, Mapping

from .schema import json_schema_to_comfy


def resolve_ref(ref: str, components: Mapping[str, Any]) -> dict:
    """Resolve a local `#/components/...` $ref. Remote refs not supported."""
    if not ref.startswith("#/"):
        return {}
    parts = ref[2:].split("/")
    node: Any = {"components": components}
    for p in parts:
        if not isinstance(node, Mapping):
            return {}
        node = node.get(p, {})
    return node if isinstance(node, dict) else {}


def expand(schema: Any, components: Mapping[str, Any], depth: int = 0) -> dict:
    """Inline $refs up to a shallow depth so the caller sees plain dicts."""
    if not isinstance(schema, Mapping) or depth > 4:
        return schema if isinstance(schema, dict) else {}
    if "$ref" in schema:
        return expand(resolve_ref(schema["$ref"], components), components, depth + 1)
    out = dict(schema)
    if "properties" in out:
        out["properties"] = {
            k: expand(v, components, depth + 1)
            for k, v in (out["properties"] or {}).items()
        }
    if "items" in out:
        out["items"] = expand(out["items"], components, depth + 1)
    return out


def _safe_id(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z_]", "_", name or "")
    return s or "param"


def operation_to_input_types(operation: Mapping[str, Any],
                             components: Mapping[str, Any] | None = None) -> dict:
    """Return ComfyUI INPUT_TYPES (required + optional) for the operation."""
    comps = components or {}
    required: dict[str, Any] = {}
    optional: dict[str, Any] = {}

    # parameters: path / query / header / cookie
    for p in operation.get("parameters") or []:
        name = _safe_id(p.get("name", ""))
        if not name:
            continue
        schema = expand(p.get("schema") or {}, comps)
        slot = json_schema_to_comfy(schema, name)
        bucket = required if p.get("required") else optional
        bucket[name] = slot

    # requestBody: expand one content type's schema into per-property inputs
    rb = operation.get("requestBody") or {}
    required_body = bool(rb.get("required"))
    content = rb.get("content") or {}
    if content:
        # Prefer application/json; otherwise first declared content.
        ct = "application/json" if "application/json" in content else next(iter(content))
        schema = expand((content[ct] or {}).get("schema") or {}, comps)
        if schema.get("type") == "object" and schema.get("properties"):
            req_props = set(schema.get("required") or [])
            for pname, pschema in (schema.get("properties") or {}).items():
                slot = json_schema_to_comfy(expand(pschema, comps), pname)
                (required if pname in req_props else optional)[_safe_id(pname)] = slot
        else:
            # Non-object / array / free-form — let the user paste JSON.
            (required if required_body else optional)["body"] = (
                "STRING", {"default": "", "multiline": True}
            )

    return {"required": required, "optional": optional}


def canonical_op_to_input_types(op: Mapping[str, Any],
                                components: Mapping[str, Any] | None = None) -> dict:
    """Same output shape as operation_to_input_types, but sourced from a
    `to_jsonschema` canonical `OperationSchema` — protocol-agnostic."""
    comps = components or {}
    required: dict[str, Any] = {}
    optional: dict[str, Any] = {}

    for p in op.get("parameters") or []:
        name = _safe_id(p.get("name", ""))
        if not name:
            continue
        slot = json_schema_to_comfy(expand(p.get("schema") or {}, comps), name)
        (required if p.get("required") else optional)[name] = slot

    schema = expand(op.get("input_schema") or {}, comps)
    if schema.get("type") == "object" and schema.get("properties"):
        req_props = set(schema.get("required") or [])
        for pname, pschema in (schema.get("properties") or {}).items():
            slot = json_schema_to_comfy(expand(pschema, comps), pname)
            (required if pname in req_props else optional)[_safe_id(pname)] = slot
    elif schema:
        # Non-object body → let the user paste it.
        optional["body"] = ("STRING", {"default": "", "multiline": True})

    return {"required": required, "optional": optional}


def canonical_op_to_return_types(op: Mapping[str, Any],
                                 components: Mapping[str, Any] | None = None
                                 ) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Typed output slots + canonical (body, stats, headers) tail."""
    comps = components or {}
    base_types = ("STRING", "STRING", "STRING")
    base_names = ("body", "stats", "headers")
    schema = expand(op.get("output_schema") or {}, comps)
    if schema.get("type") != "object" or not schema.get("properties"):
        return base_types, base_names
    typed: list[str] = []
    names: list[str] = []
    for pname, pschema in schema["properties"].items():
        pschema = expand(pschema, comps)
        t = pschema.get("type")
        if t == "integer":
            typed.append("INT")
        elif t == "number":
            typed.append("FLOAT")
        elif t == "boolean":
            typed.append("BOOLEAN")
        else:
            typed.append("STRING")
        names.append(_safe_id(pname))
    return tuple(typed) + base_types, tuple(names) + base_names


def operation_to_return_types(operation: Mapping[str, Any],
                              components: Mapping[str, Any] | None = None
                              ) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (RETURN_TYPES, RETURN_NAMES) from the operation's 2xx schema.

    Every operation keeps the last three slots reserved — (body, stats,
    headers) — so tests and old workflows stay wired. Fields from the
    response schema are prepended as typed outputs.
    """
    comps = components or {}
    base_types  = ("STRING", "STRING", "STRING")
    base_names  = ("body", "stats", "headers")

    resps = operation.get("responses") or {}
    ok = None
    for code, resp in resps.items():
        if str(code).startswith("2"):
            ok = resp
            break
    if not ok:
        return base_types, base_names

    content = (ok or {}).get("content") or {}
    if "application/json" not in content:
        return base_types, base_names
    schema = expand((content["application/json"] or {}).get("schema") or {}, comps)
    if schema.get("type") != "object" or not schema.get("properties"):
        return base_types, base_names

    typed: list[str] = []
    names: list[str] = []
    for pname, pschema in schema["properties"].items():
        pschema = expand(pschema, comps)
        t = pschema.get("type")
        if t == "integer":
            typed.append("INT")
        elif t == "number":
            typed.append("FLOAT")
        elif t == "boolean":
            typed.append("BOOLEAN")
        else:
            typed.append("STRING")
        names.append(_safe_id(pname))

    # Surface typed outputs first, then the canonical tail.
    return (tuple(typed) + base_types,
            tuple(names) + base_names)
