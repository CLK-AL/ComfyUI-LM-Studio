"""Every supported spec kind converges here first.

Each module in this package knows how to pull **JSON Schema** out of
one kind of API spec. After that, `binding.py` is the single layer
that translates JSON Schema → ComfyUI node spec — a stable pivot
that keeps protocol add-ons small and decoupled.

    [OpenAPI|AsyncAPI|gRPC|GraphQL|MCP|RSocket|…]
                     │  each converter writes:
                     ▼
             ┌─────────────────────┐
             │  canonical form:    │
             │  {                   │
             │    "operations": [  │
             │       { id, input_schema, output_schema, … } ]
             │    "components": {…}
             │  }                   │
             └─────────────────────┘
                     │
                     ▼
              binding.py (one layer)
                     │
                     ▼
        ComfyUI INPUT_TYPES / RETURN_TYPES

Adding gRPC looks like `grpc2jsonschema2comfyui`:
 1. write `to_jsonschema/grpc.py` — protoc descriptor → canonical dict
 2. register it in `spec_kinds.py`
 3. nothing else changes.
"""
from __future__ import annotations

from typing import Any, TypedDict


class OperationSchema(TypedDict, total=False):
    id:            str     # operationId / tool name / RPC method
    protocol:      str     # http | ws | sse | grpc | rsocket | mcp
    verb:          str     # HTTP method, or "query" | "mutation" | "subscribe" | …
    path:          str     # HTTP path, GraphQL field path, channel name, proto name
    input_schema:  dict    # JSON Schema for the request/input payload
    output_schema: dict    # JSON Schema for the 2xx response / output
    parameters:    list    # OpenAPI-style parameter list (optional; path/query/header)
    security:      list    # list of security scheme names (OpenAPI style)
    raw:           dict    # the original operation object for pass-through


class Canonical(TypedDict, total=False):
    title:       str
    version:     str
    server_url:  str
    components:  dict           # JSON Schema components (shared across ops)
    operations:  list[OperationSchema]
