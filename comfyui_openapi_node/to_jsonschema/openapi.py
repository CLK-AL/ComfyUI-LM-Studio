"""OpenAPI → JSON Schema canonical form.

OpenAPI 3.x already speaks JSON Schema (Draft 2020-12 dialect in 3.1,
a close cousin in 3.0). This converter is mostly a shape-shuffle: pull
each operation's request body + responses into `input_schema` /
`output_schema`, reuse `components.schemas` unchanged.

It's intentionally tiny so the pattern is obvious when someone writes
`to_jsonschema/asyncapi.py` tomorrow.
"""
from __future__ import annotations

from typing import Mapping

from . import Canonical, OperationSchema


def _first_json_schema(content: Mapping) -> dict:
    for ct, entry in (content or {}).items():
        if "json" in ct.lower():
            return (entry or {}).get("schema") or {}
    # Fall back to the first content type's schema — still JSON Schema-shaped.
    for _, entry in (content or {}).items():
        return (entry or {}).get("schema") or {}
    return {}


def convert(spec: Mapping) -> Canonical:
    ops: list[OperationSchema] = []
    for path, item in (spec.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if not isinstance(op, Mapping) or not op.get("operationId"):
                continue

            rb = op.get("requestBody") or {}
            input_schema = _first_json_schema(rb.get("content") or {})

            output_schema: dict = {}
            for code, resp in (op.get("responses") or {}).items():
                if str(code).startswith("2"):
                    output_schema = _first_json_schema((resp or {}).get("content") or {})
                    break

            ops.append(OperationSchema(
                id=op["operationId"],
                protocol="http",
                verb=method.upper(),
                path=path,
                input_schema=input_schema,
                output_schema=output_schema,
                parameters=list(op.get("parameters") or []),
                security=list(op.get("security") or []),
                raw=dict(op),
            ))

    return Canonical(
        title=((spec.get("info") or {}).get("title") or ""),
        version=((spec.get("info") or {}).get("version") or ""),
        server_url=((spec.get("servers") or [{}])[0] or {}).get("url", ""),
        components=dict(spec.get("components") or {}),
        operations=ops,
    )
