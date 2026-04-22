"""Schema-only SQLite cache for JDBC discovery.

Not a data store — just a schema *registry*. When the Python side or
the jbang facade discovers a DB through `DatabaseMetaData`, the
resulting `{"tables": [...]}` descriptor is cached here keyed by a
**JDBC URI template**, so a cold start against a known database is
instant and a later run against the same template skips the full
introspection round-trip.

URI templating is the usual Spring-flavoured `{var}` style:
    jdbc:postgresql://{host}:{port}/{db}
    jdbc:sqlite:{path}
Concrete URIs are normalised by matching against known templates —
`register_template()` lets callers declare them. A URI that doesn't
match any template becomes its own template (the URI itself).

Schema of the registry DB (three tables, zero user data):

    CREATE TABLE connections (
        uri_template TEXT PRIMARY KEY,
        captured_at  TEXT NOT NULL,
        driver       TEXT
    );

    CREATE TABLE tables_cache (
        uri_template TEXT NOT NULL,
        name         TEXT NOT NULL,
        primary_key  TEXT NOT NULL,
        PRIMARY KEY (uri_template, name)
    );

    CREATE TABLE columns_cache (
        uri_template TEXT NOT NULL,
        table_name   TEXT NOT NULL,
        name         TEXT NOT NULL,
        sql_type     TEXT NOT NULL,
        pg_type      TEXT,
        nullable     INTEGER NOT NULL,
        size         INTEGER,
        precision_   INTEGER,
        scale        INTEGER,
        default_     TEXT,
        geotype      TEXT,
        ordinal      INTEGER NOT NULL,
        PRIMARY KEY (uri_template, table_name, name)
    );

Default location: $XDG_CACHE_HOME/comfyui_openapi_node/schema-registry.db
Override with env `COMFYUI_SCHEMA_REGISTRY`.

Public API:
    SchemaRegistry.open(path=None) -> SchemaRegistry
    reg.register_template(uri_template)
    reg.template_for(uri)    -> matching template, or the uri itself
    reg.get(uri_or_template) -> descriptor | None
    reg.put(uri_or_template, descriptor, *, driver=None)
    reg.clear(uri_or_template=None)
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from pathlib import Path
from typing import Iterable


DEFAULT_PATH_ENV = "COMFYUI_SCHEMA_REGISTRY"


def _default_path() -> Path:
    env = os.environ.get(DEFAULT_PATH_ENV)
    if env:
        return Path(env)
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "comfyui_openapi_node" / "schema-registry.db"


class SchemaRegistry:
    # DDL runs once at open() — cheap on re-open because CREATE IF NOT EXISTS.
    _DDL = (
        "CREATE TABLE IF NOT EXISTS connections ("
        "  uri_template TEXT PRIMARY KEY,"
        "  captured_at  TEXT NOT NULL,"
        "  driver       TEXT"
        ");",
        "CREATE TABLE IF NOT EXISTS tables_cache ("
        "  uri_template TEXT NOT NULL,"
        "  name         TEXT NOT NULL,"
        "  primary_key  TEXT NOT NULL,"
        "  PRIMARY KEY (uri_template, name)"
        ");",
        "CREATE TABLE IF NOT EXISTS columns_cache ("
        "  uri_template TEXT NOT NULL,"
        "  table_name   TEXT NOT NULL,"
        "  name         TEXT NOT NULL,"
        "  sql_type     TEXT NOT NULL,"
        "  pg_type      TEXT,"
        "  nullable     INTEGER NOT NULL,"
        "  size         INTEGER,"
        "  precision_   INTEGER,"
        "  scale        INTEGER,"
        "  default_     TEXT,"
        "  geotype      TEXT,"
        "  ordinal      INTEGER NOT NULL,"
        "  PRIMARY KEY (uri_template, table_name, name)"
        ");",
        "CREATE TABLE IF NOT EXISTS uri_templates ("
        "  uri_template TEXT PRIMARY KEY,"
        "  pattern      TEXT NOT NULL"
        ");",
    )

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        for stmt in self._DDL:
            conn.execute(stmt)
        conn.commit()

    # --- factory ---------------------------------------------------------
    @classmethod
    def open(cls, path: str | Path | None = None) -> "SchemaRegistry":
        p = Path(path) if path else _default_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        return cls(sqlite3.connect(str(p)))

    def close(self) -> None:
        self._conn.close()

    # --- URI templating --------------------------------------------------
    _VAR_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")

    @classmethod
    def _compile(cls, tmpl: str) -> str:
        # Split on {var} spans; escape the literal pieces, replace each
        # {var} with a non-greedy capture group. Non-greedy so that
        # adjacent literals still anchor correctly
        # (e.g. `{host}:{port}` in jdbc:postgresql://h:5432).
        pieces = cls._VAR_RE.split(tmpl)
        vars_  = cls._VAR_RE.findall(tmpl)
        out = [re.escape(pieces[0])]
        for i, var in enumerate(vars_):
            name = var[1:-1]
            out.append(f"(?P<{name}>.+?)")
            out.append(re.escape(pieces[i + 1]))
        return "^" + "".join(out) + "$"

    def register_template(self, uri_template: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO uri_templates (uri_template, pattern) VALUES (?, ?)",
            (uri_template, self._compile(uri_template)),
        )
        self._conn.commit()

    def template_for(self, uri: str) -> str:
        for tmpl, pattern in self._conn.execute(
            "SELECT uri_template, pattern FROM uri_templates"
        ).fetchall():
            if re.match(pattern, uri):
                return tmpl
        # Fall back to the URI itself — it's its own template.
        return uri

    # --- get / put -------------------------------------------------------
    def get(self, uri_or_template: str) -> dict | None:
        tmpl = self.template_for(uri_or_template)
        rows = self._conn.execute(
            "SELECT name, primary_key FROM tables_cache WHERE uri_template = ? "
            "ORDER BY name",
            (tmpl,),
        ).fetchall()
        if not rows:
            return None
        tables = []
        for name, pk_json in rows:
            cols = self._conn.execute(
                "SELECT name, sql_type, pg_type, nullable, size, precision_, "
                "scale, default_, geotype FROM columns_cache "
                "WHERE uri_template = ? AND table_name = ? ORDER BY ordinal",
                (tmpl, name),
            ).fetchall()
            columns = [
                {k: v for k, v in {
                    "name":      c[0],
                    "sql_type":  c[1],
                    "pg_type":   c[2],
                    "nullable":  bool(c[3]),
                    "size":      c[4],
                    "precision": c[5],
                    "scale":     c[6],
                    "default":   c[7],
                    "geotype":   c[8],
                }.items() if v is not None}
                for c in cols
            ]
            tables.append({
                "name": name,
                "primary_key": json.loads(pk_json),
                "columns": columns,
            })
        return {"tables": tables}

    def put(self, uri_or_template: str, descriptor: dict,
            *, driver: str | None = None) -> None:
        tmpl = self.template_for(uri_or_template)
        now  = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._conn.execute(
            "INSERT OR REPLACE INTO connections (uri_template, captured_at, driver)"
            " VALUES (?, ?, ?)", (tmpl, now, driver))
        # Wipe this template's cache then replace — semantics match a
        # fresh DatabaseMetaData snapshot.
        self._conn.execute("DELETE FROM tables_cache  WHERE uri_template = ?", (tmpl,))
        self._conn.execute("DELETE FROM columns_cache WHERE uri_template = ?", (tmpl,))
        for tbl in descriptor.get("tables") or []:
            self._conn.execute(
                "INSERT INTO tables_cache (uri_template, name, primary_key)"
                " VALUES (?, ?, ?)",
                (tmpl, tbl["name"], json.dumps(tbl.get("primary_key") or [])),
            )
            for i, col in enumerate(tbl.get("columns") or []):
                self._conn.execute(
                    "INSERT INTO columns_cache "
                    "(uri_template, table_name, name, sql_type, pg_type, "
                    " nullable, size, precision_, scale, default_, geotype, ordinal)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        tmpl, tbl["name"], col["name"],
                        str(col.get("sql_type", "VARCHAR")),
                        col.get("pg_type"),
                        int(bool(col.get("nullable", True))),
                        col.get("size"),
                        col.get("precision"),
                        col.get("scale"),
                        (None if col.get("default") is None else str(col["default"])),
                        col.get("geotype"),
                        i,
                    ),
                )
        self._conn.commit()

    def clear(self, uri_or_template: str | None = None) -> None:
        if uri_or_template is None:
            self._conn.execute("DELETE FROM tables_cache")
            self._conn.execute("DELETE FROM columns_cache")
            self._conn.execute("DELETE FROM connections")
        else:
            tmpl = self.template_for(uri_or_template)
            self._conn.execute("DELETE FROM tables_cache  WHERE uri_template = ?", (tmpl,))
            self._conn.execute("DELETE FROM columns_cache WHERE uri_template = ?", (tmpl,))
            self._conn.execute("DELETE FROM connections  WHERE uri_template = ?", (tmpl,))
        self._conn.commit()

    # --- iteration -------------------------------------------------------
    def templates(self) -> list[str]:
        return [r[0] for r in self._conn.execute(
            "SELECT uri_template FROM connections ORDER BY captured_at DESC"
        ).fetchall()]
