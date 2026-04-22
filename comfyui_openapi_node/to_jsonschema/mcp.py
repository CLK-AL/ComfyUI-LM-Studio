"""MCP (Model Context Protocol) → JSON Schema canonical form.

MCP tools already declare `inputSchema` and `outputSchema` as JSON
Schema — this converter is the simplest of the bunch.

Pipeline:
  1. An MCP server advertises tools via `tools/list`, each carrying
     `{ name, description, inputSchema, outputSchema? }`.
  2. Emit one OperationSchema per tool.
  3. `binding.py` handles the rest; the executor does JSON-RPC
     (`tools/call`) over the MCP transport (stdio / SSE / WS).

Status: scaffold. The Kotlin MCP SDK in /api/mcp/ is the counterpart.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from . import Canonical, OperationSchema


def convert(tools_list: Iterable[Mapping]) -> Canonical:
    ops: list[OperationSchema] = []
    for tool in tools_list or []:
        name = tool.get("name") or ""
        if not name:
            continue
        ops.append(OperationSchema(
            id=name,
            protocol="mcp",
            verb="tools/call",
            path=name,
            input_schema=dict(tool.get("inputSchema") or {}),
            output_schema=dict(tool.get("outputSchema") or {}),
            parameters=[],
            security=[],
            raw=dict(tool),
        ))
    return Canonical(
        title="MCP tools",
        version="",
        server_url="",
        components={},
        operations=ops,
    )
