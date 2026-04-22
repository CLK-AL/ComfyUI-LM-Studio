"""Built-in spec presets. LM Studio is intentionally first — drop the
node into a workflow, pick `preset:lm-studio`, and everything wires up
against the LM Studio REST API on localhost.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from ..loader import load_spec


@dataclass
class Preset:
    name: str
    title: str
    description: str
    spec: Callable[[], dict]
    kind: str = "openapi"


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
API_ROOT = REPO / "api"


def _file(p: Path) -> Callable[[], dict]:
    return lambda: load_spec(p)


def _sqlite_from_ddl(p: Path) -> Callable[[], dict]:
    """Return a zero-arg callable that applies a .sq / .sql file's DDL
    to an in-memory SQLite and yields a JDBC-shaped `{"tables": ...}`
    descriptor — the exact shape `to_jsonschema.jdbc.convert()` eats."""
    def _load():
        from ..to_jsonschema.sqlite import from_ddl
        return from_ddl(p.read_text())
    return _load


# The spec bodies live under /api/<kind>/spec/ — single source of truth
# shared with the jbang mock facade. Each preset names its kind so new
# spec types (AsyncAPI / GraphQL / MCP manifests) slot in next to it.
PRESETS: dict[str, Preset] = {
    "lm-studio": Preset(
        name="lm-studio",
        title="LM Studio",
        description="Local LM Studio REST API (chat/completions + models).",
        spec=_file(API_ROOT / "openapi" / "spec" / "lm-studio.yaml"),
        kind="openapi",
    ),
    "simple-chat": Preset(
        name="simple-chat",
        title="Simple Chat (AsyncAPI)",
        description="Stub AsyncAPI 2.x showing publish/subscribe → WS nodes.",
        spec=_file(API_ROOT / "asyncapi" / "spec" / "simple-chat.yaml"),
        kind="asyncapi",
    ),
    "lm-studio-stream": Preset(
        name="lm-studio-stream",
        title="LM Studio — streaming (AsyncAPI)",
        description=(
            "AsyncAPI projection of LM Studio's SSE chat-completion stream. "
            "Same JSON Schema as the OpenAPI preset, modelled as publish/subscribe."
        ),
        spec=_file(API_ROOT / "asyncapi" / "spec" / "lm-studio-stream.yaml"),
        kind="asyncapi",
    ),
    "sample-tables": Preset(
        name="sample-tables",
        title="Sample JDBC tables (users + PostGIS places)",
        description=(
            "Two-table JDBC schema showing every column family: bigint, varchar, "
            "timestamptz, boolean, array, jsonb, and PostGIS geometry/geography "
            "returned as GeoJSON. Binds to select/insert/update/delete operations."
        ),
        spec=_file(API_ROOT / "jdbc" / "spec" / "sample-tables.yaml"),
        kind="jdbc",
    ),
    "sample-tables-local": Preset(
        name="sample-tables-local",
        title="Sample tables (local SQLite via SQLDelight .sq)",
        description=(
            "Same two tables, sourced from the SQLDelight .sq file. Python "
            "applies the DDL to an in-memory SQLite and introspects it — "
            "identical to what `jbang api.mock.jbang.kt jdbc serve "
            "--jdbc-url jdbc:sqlite::memory: --sql-file …sample-tables.sq` "
            "does on the server side. One source of truth, both sides."
        ),
        spec=_sqlite_from_ddl(API_ROOT / "jdbc" / "spec" / "sample-tables.sq"),
        kind="jdbc",
    ),
}
