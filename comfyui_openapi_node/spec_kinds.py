"""Dispatch a spec source to the right loader/executor family.

The node is ultimately just dynamic UI driven by an API spec — OpenAPI
today; AsyncAPI and GraphQL are natural next steps with the same
shape (spec → operations → IO types → executor).

Adding a new kind is:
  1. implement a `Handler` subclass (operations(), execute())
  2. register it here

Until they land, picking "asyncapi" or "graphql" raises a clear
NotImplementedError so nothing fails silently.
"""
from __future__ import annotations

from typing import Any, Iterable, Protocol

SpecKind = str  # "openapi" | "asyncapi" | "graphql"


class Handler(Protocol):
    kind: SpecKind

    def operations(self, spec: dict) -> Iterable[tuple[str, str, str]]:
        """Yield (operationId, routing_key, verb) triples.

        For OpenAPI this is (opId, path, httpMethod); AsyncAPI would
        map to (opId, channel, action); GraphQL to (opName, "/graphql",
        "query"|"mutation"|"subscription").
        """

    def execute(self, spec: dict, operation_id: str, values: dict, **kw) -> Any:
        ...


# --- OpenAPI -------------------------------------------------------------
class OpenAPIHandler:
    kind = "openapi"

    def operations(self, spec):
        for path, item in (spec.get("paths") or {}).items():
            for method, op in (item or {}).items():
                if isinstance(op, dict) and op.get("operationId"):
                    yield op["operationId"], path, method.upper()

    def execute(self, spec, operation_id, values, **kw):
        from .node import find_operation
        from .protocols import get_executor
        op, path, method = find_operation(spec, operation_id)
        protocol = kw.pop("protocol", "http")
        server_url = kw.pop("server_url", "") or \
            ((spec.get("servers") or [{}])[0].get("url", ""))
        return get_executor(protocol)(
            operation=op, method=method, server_url=server_url,
            path=path, values=values, **kw,
        )


# --- AsyncAPI / GraphQL --------------------------------------------------
class _Stub:
    def __init__(self, kind, docs_url):
        self.kind, self._docs = kind, docs_url

    def operations(self, spec):
        return iter(())

    def execute(self, *a, **kw):
        raise NotImplementedError(
            f"{self.kind} support is not yet implemented. "
            f"See {self._docs} for the spec, or pin a version that has it."
        )


HANDLERS: dict[SpecKind, Handler] = {
    "openapi":  OpenAPIHandler(),
    "asyncapi": _Stub("AsyncAPI",  "https://www.asyncapi.com/docs/reference/specification/v3.0.0"),
    "graphql":  _Stub("GraphQL",   "https://spec.graphql.org/October2021/"),
}


def for_kind(kind: SpecKind) -> Handler:
    try:
        return HANDLERS[kind.lower()]
    except KeyError:
        raise ValueError(
            f"Unknown spec kind {kind!r}. Known: {sorted(HANDLERS.keys())}"
        )
