"""GraphQL → JSON Schema canonical form.

Pipeline:
  1. Introspect the schema (or parse SDL) to get types, queries,
     mutations, subscriptions.
  2. For each root field, emit one OperationSchema:
     - input_schema  : object made of its argument types
     - output_schema : return type projected into JSON Schema
  3. `binding.py` renders ComfyUI slots; the executor sends
     `POST /graphql` with `{ query, variables }`.

Status: scaffold. `graphql-core` handles parse/introspection; mapping
GraphQL types → JSON Schema is straightforward (and already done by
e.g. `graphql-to-json-schema` in npm).
"""
from __future__ import annotations

from typing import Mapping

from . import Canonical


def convert(schema_source: str | Mapping) -> Canonical:
    raise NotImplementedError(
        "GraphQL → JSON Schema converter is not yet implemented. "
        "Parse SDL or introspection JSON, walk root types, and emit "
        "OperationSchema entries (verb = 'query'|'mutation'|'subscription')."
    )
