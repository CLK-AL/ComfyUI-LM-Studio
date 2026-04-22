"""Single naming convention across every API kind.

The whole stack is API-first: JSON Schema first, every other surface
follows. This module is the one-liner lookup between them.

    OpenAPI   components.schemas.<Name>      ⇄  JDBC table  <name_snake>
    AsyncAPI  messages.<MessageName>         ≡  JSON Patch  <message_name>
    GraphQL   type <Name>                    ⇐  JSON Schema
    MCP       tools.<name>                   ─▶ SSE events with
                                                {before, after} payloads
    ComfyUI   node "API · <api> · <op>"      ⇐  JSON Schema / op

Round-trip helpers:

    component_name("book")      → "Book"        Pascal for schema/component
    table_name("Book")          → "book"        snake for tables
    message_name("Book")        → "BookUpdated" verbose for messages
    patch_op_to_sse(audit_event)→ SSE frame with {before, after}
    sse_frame(event)            → text/event-stream bytes

The goal: someone looks at a JSON Schema called `Book` and knows,
without guessing, that the SQLite table is `book`, the AsyncAPI
message is `BookUpdated`, the MCP SSE `event: entity.*` will carry
`{"before": …, "after": …}`, and the ComfyUI node is
"API · <preset> · <operationId>".
"""
from __future__ import annotations

import json
import re
from typing import Any, Mapping


# ---- identifier case conversions ---------------------------------------
_PASCAL_SPLIT_RE  = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
_NON_IDENT_RE     = re.compile(r"[^A-Za-z0-9]+")


def _tokenise(s: str) -> list[str]:
    pieces = _PASCAL_SPLIT_RE.split(s or "")
    return [t for piece in pieces for t in _NON_IDENT_RE.split(piece) if t]


def snake(name: str) -> str:
    return "_".join(t.lower() for t in _tokenise(name))


def pascal(name: str) -> str:
    return "".join(t[:1].upper() + t[1:].lower() for t in _tokenise(name))


def camel(name: str) -> str:
    p = pascal(name)
    return p[:1].lower() + p[1:] if p else p


# ---- named-surface helpers ---------------------------------------------
def component_name(any_case: str) -> str:
    """Canonical JSON Schema component name (PascalCase)."""
    return pascal(any_case)


def table_name(any_case: str) -> str:
    """SQLite / JDBC table (snake_case)."""
    return snake(any_case)


def message_name(component: str, *, verb: str = "Updated") -> str:
    """AsyncAPI message name for a mutation on `component`.

    The verb ("Updated" / "Created" / "Deleted" / "Patched") pairs up
    with an op in the SSE audit (`entity.put` → Created,
    `entity.replace` → Updated, `entity.remove` → Deleted,
    `entity.add` → Patched). Defaults to "Updated"."""
    return pascal(component) + pascal(verb)


def patch_name(component: str) -> str:
    """Stable name for a JSON Patch applied to a component.

    We keep it snake-case to match table names so SSE event ids and
    JDBC writes share a vocabulary: `book.patch → book row`."""
    return snake(component) + ".patch"


def node_display(api: str, operation_id: str) -> str:
    """ComfyUI canvas title for an auto-generated node."""
    return f"API · {api} · {operation_id}"


def node_class(api: str, operation_id: str) -> str:
    """Python class name registered in NODE_CLASS_MAPPINGS."""
    return f"API_{api.replace('-', '_')}_{operation_id}"


# ---- audit → {before, after} payload ----------------------------------
# Translate our own audit event record (or EntityStore's AuditEvent)
# into the shape MCP tool-callers and SSE consumers want.
_OP_TO_VERB = {
    "put":     "Created",
    "add":     "Created",     # RFC 6902 add on a fresh path
    "replace": "Updated",
    "remove":  "Deleted",
}


def patch_op_to_sse(event: Mapping[str, Any]) -> dict:
    """Return the SSE `data:` payload for an audit event.

    `event` may be either an `EntityStore.AuditEvent` dict-view or a
    `ComponentDB` audit row — both have {op, path, old, new, api,
    component/type, id/pk}. Output:

        {
          "component": "Book",
          "pk":        "9780000000001",
          "op":        "replace",
          "path":      "/title",
          "before":    "old title",
          "after":     "new title",
          "message":   "BookUpdated",
          "api":       "openapi/google-books",
          "ts":        "…"
        }
    """
    component = event.get("component") or event.get("type")
    pk        = event.get("pk")        or event.get("id")
    op        = str(event.get("op", ""))
    out = {
        "component": component,
        "pk":        pk,
        "op":        op,
        "path":      event.get("path", ""),
        "before":    event.get("old", event.get("old_value")),
        "after":     event.get("new", event.get("new_value")),
        "message":   message_name(component or "",
                                  verb=_OP_TO_VERB.get(op, "Patched")),
        "api":       event.get("api"),
        "ts":        event.get("ts"),
    }
    return out


def sse_frame(payload: Mapping[str, Any], *,
              event: str | None = None, id_: int | str | None = None) -> str:
    """Serialise a payload as a text/event-stream frame."""
    event = event or f"entity.{payload.get('op', 'put')}"
    lines: list[str] = []
    if id_ is not None:
        lines.append(f"id: {id_}")
    lines.append(f"event: {event}")
    lines.append("data: " + json.dumps(payload, ensure_ascii=False))
    return "\n".join(lines) + "\n\n"
