"""Open (or build) a SQLite DB and return a table descriptor dict
compatible with `to_jsonschema.jdbc.convert()`.

The point: when we run the Python node registration AND the jbang
Spring server locally, they should share one source of truth for the
schema. That source is a `.sq` file (SQLDelight-style) or plain `.sql`
DDL. Python applies its CREATE TABLE statements to an in-memory
SQLite and introspects via PRAGMA; jbang applies the same file to
`jdbc:sqlite::memory:` and serves `/jdbc/__schema` + CRUD. Both sides
see the same tables.

Usage:

    # 1) in-memory from DDL text (tests / fast local)
    descriptor = from_ddl(Path("api/jdbc/spec/sample-tables.sq").read_text())

    # 2) attach to an existing file / :memory: connection
    descriptor = introspect(sqlite3.connect("/tmp/sample.db"))

    # 3) chain with the JDBC canonical converter
    from .jdbc import convert
    canon = convert(descriptor)
"""
from __future__ import annotations

import re
import sqlite3
from typing import Iterable


# SQLite type strings → (sql_type, pg_type-ish) we feed into
# sql_types.column_to_json_schema. SQLite is loosely typed; we look
# at the declared `type` string and pick the closest java.sql.Types
# name that our sql_types module already handles.
def _map_sqlite_type(decl: str) -> tuple[str, str | None]:
    t = (decl or "").upper().strip()
    # Pull off (size) / (p,s) modifiers
    size = None
    m = re.match(r"^([A-Z]+)\s*(?:\(\s*(\d+)\s*(?:,\s*\d+)?\s*\))?\s*$", t)
    if m:
        head = m.group(1)
        if m.group(2):
            size = int(m.group(2))
    else:
        head = t
    mapping = {
        "INTEGER": ("INTEGER", None),
        "INT":     ("INTEGER", None),
        "TINYINT": ("TINYINT", None),
        "SMALLINT":("SMALLINT", None),
        "BIGINT":  ("BIGINT",  "int8"),
        "REAL":    ("DOUBLE",  None),
        "DOUBLE":  ("DOUBLE",  None),
        "FLOAT":   ("FLOAT",   None),
        "NUMERIC": ("NUMERIC", None),
        "DECIMAL": ("DECIMAL", None),
        "TEXT":    ("VARCHAR", None),
        "VARCHAR": ("VARCHAR", None),
        "CHAR":    ("CHAR",    None),
        "CLOB":    ("CLOB",    None),
        "BLOB":    ("BLOB",    None),
        "BOOLEAN": ("BOOLEAN", None),
        "DATE":    ("DATE",    None),
        "TIME":    ("TIME",    None),
        "TIMESTAMP": ("TIMESTAMP", None),
        "DATETIME":("TIMESTAMP", None),
    }
    return mapping.get(head, ("VARCHAR", None)) + (size,)[0:0]  # ignore size via tuple


def _col(cid: int, name: str, decl: str, notnull: int, default, pk: int) -> dict:
    sql_type, pg_type = _map_sqlite_type(decl)
    col = {
        "name": name,
        "sql_type": sql_type,
        "nullable": not bool(notnull),
    }
    if pg_type is not None:
        col["pg_type"] = pg_type
    if default is not None:
        col["default"] = default
    return col


def introspect(conn: sqlite3.Connection) -> dict:
    """Return `{"tables": [...]}` from an already-open connection."""
    tables = conn.execute(
        "SELECT name FROM sqlite_schema "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    ).fetchall()
    out = []
    for (name,) in tables:
        col_rows = conn.execute(f"PRAGMA table_info({name!r})").fetchall()
        columns: list[dict] = []
        pks: list[str] = []
        for cid, col_name, col_type, notnull, default, pk in col_rows:
            columns.append(_col(cid, col_name, col_type, notnull, default, pk))
            if pk:
                pks.append(col_name)
        out.append({"name": name, "primary_key": pks, "columns": columns})
    return {"tables": out}


_CREATE_RE = re.compile(
    r"(CREATE\s+TABLE[^;]*;)",
    flags=re.IGNORECASE | re.DOTALL,
)


def extract_create_statements(ddl: str) -> list[str]:
    """Pull CREATE TABLE statements out of a `.sql` / `.sq` file.

    Ignores SQLDelight-named-query blocks (those look like
    `someName:\nSELECT …;`) — we only want the executable DDL.
    """
    return [m.strip() for m in _CREATE_RE.findall(ddl or "")]


def from_ddl(ddl: str) -> dict:
    """Apply CREATE TABLE statements to an in-memory SQLite and
    introspect the result. One function you can hand to
    `jdbc.convert(...)` for a fully-local flow."""
    conn = sqlite3.connect(":memory:")
    try:
        for stmt in extract_create_statements(ddl):
            conn.execute(stmt)
        conn.commit()
        return introspect(conn)
    finally:
        conn.close()
