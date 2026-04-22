"""Cross-kind JSON Schema registry.

The source of truth is a tree of **on-disk `*.schema.json` files** —
one per component or operation across every API kind we support. The
SQLite sidecar is a *thin index*: kind / api / category / name → file
path + sha256 + captured-at. No schema bodies in the index, no row
data anywhere. That keeps the registry's authority in the files
(which other tools can read, diff, commit, serve over HTTP) while
SQLite only answers "which files hold component X?" quickly.

Layout on disk (under `$XDG_CACHE_HOME/al.clk.api/schemas/`
or `$COMFYUI_SCHEMA_REGISTRY`):

    schemas/
      openapi/<api>/components/<name>.schema.json
      openapi/<api>/operations/<operationId>.schema.json
      openapi/<api>/endpoints/<server_url_template>.schema.json
      asyncapi/<api>/operations/<operationId>.schema.json
      jdbc/<uri-template>/tables/<table>.schema.json
      graphql/<api>/operations/<name>.schema.json
      mcp/<server>/tools/<name>.schema.json

Every file is a standard JSON Schema document. For operation files we
follow RFC-draft "operation schema" shape: top-level `input_schema` +
`output_schema` + `protocol` + `verb` + `path` annotations so a single
file fully describes the operation.

SQLite index (one table):

    CREATE TABLE schemas (
        kind        TEXT NOT NULL,
        api         TEXT NOT NULL,
        category    TEXT NOT NULL,       -- components | operations | tables | endpoints | tools
        name        TEXT NOT NULL,
        path        TEXT NOT NULL,       -- relative to the registry root
        sha256      TEXT NOT NULL,
        captured_at TEXT NOT NULL,
        PRIMARY KEY (kind, api, category, name)
    );

Public API:
    SchemaRegistry.open(root=None)
    reg.put(kind, api, category, name, schema, *, captured_at=None)
    reg.get(kind, api, category, name)  -> dict | None
    reg.find(kind=None, api=None, category=None, name=None) -> iterator[Row]
    reg.delete(kind, api, category, name)
    reg.clear(kind=None, api=None)

JDBC URI-template utilities stay here too — JDBC is *the* kind that
names its "api" with a URI template. Templating lets one Postgres
cluster = one cached schema across many host/port/db combos.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Mapping


DEFAULT_PATH_ENV = "COMFYUI_SCHEMA_REGISTRY"


def _default_root() -> Path:
    env = os.environ.get(DEFAULT_PATH_ENV)
    if env:
        return Path(env)
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "al.clk.api"


@dataclass(frozen=True)
class Row:
    kind: str
    api: str
    category: str
    name: str
    path: str
    sha256: str
    captured_at: str


def _slug(s: str) -> str:
    # Turn an arbitrary api / name string into a safe file path segment.
    # Keeps basic chars + slashes + dashes + dots + braces (templates).
    return re.sub(r"[^0-9A-Za-z._{}@/\\-]+", "_", s).strip("_") or "_"


class SchemaRegistry:
    # Uses SQLite's JSON1 built-ins (json_valid / json_extract /
    # json_patch / json_each) to query and merge across the index
    # without touching the on-disk files. `summary` is a compact
    # JSON {type, required, props: {name: type}} for each entry —
    # big enough for searches ("every schema with an 'isbn' property")
    # and small enough to keep the index thin.
    _DDL = (
        "CREATE TABLE IF NOT EXISTS schemas ("
        "  kind        TEXT NOT NULL,"
        "  api         TEXT NOT NULL,"
        "  category    TEXT NOT NULL,"
        "  name        TEXT NOT NULL,"
        "  path        TEXT NOT NULL,"
        "  sha256      TEXT NOT NULL,"
        "  captured_at TEXT NOT NULL,"
        "  summary     TEXT NOT NULL CHECK (json_valid(summary)),"
        "  PRIMARY KEY (kind, api, category, name)"
        ");",
        "CREATE INDEX IF NOT EXISTS schemas_by_api  ON schemas(kind, api);",
        "CREATE INDEX IF NOT EXISTS schemas_by_name ON schemas(name);",
        "CREATE TABLE IF NOT EXISTS uri_templates ("
        "  kind         TEXT NOT NULL,"
        "  uri_template TEXT NOT NULL,"
        "  pattern      TEXT NOT NULL,"
        "  PRIMARY KEY (kind, uri_template)"
        ");",
    )

    def __init__(self, root: Path, conn: sqlite3.Connection):
        self.root = root
        self._conn = conn
        root.mkdir(parents=True, exist_ok=True)
        (root / "schemas").mkdir(parents=True, exist_ok=True)
        for stmt in self._DDL:
            conn.execute(stmt)
        conn.commit()

    # --- factory / lifecycle -------------------------------------------
    @classmethod
    def open(cls, root: str | Path | None = None) -> "SchemaRegistry":
        r = Path(root) if root else _default_root()
        r.mkdir(parents=True, exist_ok=True)
        return cls(r, sqlite3.connect(str(r / "index.db")))

    def close(self) -> None:
        self._conn.close()

    # --- URI template matching (JDBC etc.) -----------------------------
    _VAR_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")

    @classmethod
    def _compile_template(cls, tmpl: str) -> str:
        pieces = cls._VAR_RE.split(tmpl)
        vars_  = cls._VAR_RE.findall(tmpl)
        out = [re.escape(pieces[0])]
        for i, var in enumerate(vars_):
            name = var[1:-1]
            out.append(f"(?P<{name}>.+?)")
            out.append(re.escape(pieces[i + 1]))
        return "^" + "".join(out) + "$"

    def register_template(self, kind: str, uri_template: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO uri_templates (kind, uri_template, pattern)"
            " VALUES (?, ?, ?)",
            (kind, uri_template, self._compile_template(uri_template)),
        )
        self._conn.commit()

    def resolve_api(self, kind: str, uri: str) -> str:
        """Return the registered URI template that matches `uri`, or
        `uri` itself if none does. Non-JDBC kinds usually just pass
        their api name through unchanged."""
        for tmpl, pattern in self._conn.execute(
            "SELECT uri_template, pattern FROM uri_templates WHERE kind = ?",
            (kind,),
        ).fetchall():
            if re.match(pattern, uri):
                return tmpl
        return uri

    # --- file helpers --------------------------------------------------
    def _rel_path(self, kind: str, api: str, category: str, name: str) -> Path:
        return Path("schemas") / _slug(kind) / _slug(api) / _slug(category) / f"{_slug(name)}.schema.json"

    def _abs_path(self, rel: Path) -> Path:
        return self.root / rel

    # --- put / get / find / delete / clear -----------------------------
    @staticmethod
    def _summarize(schema: dict) -> str:
        """Compact JSON sketch for SQL searches. Keeps just the fields
        we routinely query by — type, required[], and a name→type map."""
        s: dict = {"type": schema.get("type")}
        if isinstance(schema.get("required"), list):
            s["required"] = list(schema["required"])
        props = schema.get("properties")
        if isinstance(props, Mapping):
            s["properties"] = {
                k: (v.get("type") if isinstance(v, Mapping) else None)
                for k, v in props.items()
            }
        return json.dumps(s, ensure_ascii=False, sort_keys=True)

    def put(self, kind: str, api: str, category: str, name: str,
            schema: dict, *, captured_at: str | None = None) -> Row:
        api = self.resolve_api(kind, api)
        rel = self._rel_path(kind, api, category, name)
        abs_ = self._abs_path(rel)
        abs_.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(schema, ensure_ascii=False, indent=2,
                          sort_keys=True).encode("utf-8")
        sha = hashlib.sha256(body).hexdigest()
        abs_.write_bytes(body)
        now = captured_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._conn.execute(
            "INSERT OR REPLACE INTO schemas "
            "(kind, api, category, name, path, sha256, captured_at, summary)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (kind, api, category, name, str(rel), sha, now,
             self._summarize(schema)),
        )
        self._conn.commit()
        return Row(kind, api, category, name, str(rel), sha, now)

    def get(self, kind: str, api: str, category: str, name: str) -> dict | None:
        api = self.resolve_api(kind, api)
        row = self._conn.execute(
            "SELECT path FROM schemas "
            "WHERE kind=? AND api=? AND category=? AND name=?",
            (kind, api, category, name),
        ).fetchone()
        if row is None:
            return None
        abs_ = self._abs_path(Path(row[0]))
        if not abs_.is_file():
            return None
        return json.loads(abs_.read_text(encoding="utf-8"))

    def find(self, *, kind: str | None = None, api: str | None = None,
             category: str | None = None, name: str | None = None
             ) -> Iterator[Row]:
        clauses: list[str] = []
        params: list = []
        if kind is not None:
            clauses.append("kind = ?");     params.append(kind)
        if api is not None and kind is not None:
            api = self.resolve_api(kind, api)
        if api is not None:
            clauses.append("api = ?");      params.append(api)
        if category is not None:
            clauses.append("category = ?"); params.append(category)
        if name is not None:
            clauses.append("name = ?");     params.append(name)
        sql = "SELECT kind, api, category, name, path, sha256, captured_at FROM schemas"
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY kind, api, category, name"
        for row in self._conn.execute(sql, params).fetchall():
            yield Row(*row)

    def delete(self, kind: str, api: str, category: str, name: str) -> bool:
        api = self.resolve_api(kind, api)
        row = self._conn.execute(
            "SELECT path FROM schemas "
            "WHERE kind=? AND api=? AND category=? AND name=?",
            (kind, api, category, name),
        ).fetchone()
        if row is None:
            return False
        abs_ = self._abs_path(Path(row[0]))
        if abs_.is_file():
            abs_.unlink()
        self._conn.execute(
            "DELETE FROM schemas "
            "WHERE kind=? AND api=? AND category=? AND name=?",
            (kind, api, category, name),
        )
        self._conn.commit()
        return True

    def clear(self, *, kind: str | None = None, api: str | None = None) -> None:
        """Remove every entry matching (kind, api) — both the index
        rows and the backing files."""
        rows = list(self.find(kind=kind, api=api))
        for r in rows:
            abs_ = self._abs_path(Path(r.path))
            if abs_.is_file():
                abs_.unlink()
        q = "DELETE FROM schemas"
        params: list = []
        clauses: list[str] = []
        if kind is not None:
            clauses.append("kind = ?");  params.append(kind)
        if api is not None and kind is not None:
            api = self.resolve_api(kind, api)
        if api is not None:
            clauses.append("api = ?");   params.append(api)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        self._conn.execute(q, params)
        self._conn.commit()

    # --- SQLite JSON1-powered searches ---------------------------------
    def find_by_property(self, prop_name: str, *,
                         expected_type: str | None = None,
                         kind: str | None = None,
                         category: str | None = None) -> Iterator[Row]:
        """Yield every entry whose schema declares a property named
        `prop_name`. Optional `expected_type` narrows to entries where
        that property has the given JSON Schema type."""
        # json_extract(summary, '$.properties.<name>') returns the
        # stored type string if the property exists, NULL otherwise.
        pointer = f"$.properties.{self._jsonpath_escape(prop_name)}"
        clauses = [f"json_extract(summary, '{pointer}') IS NOT NULL"]
        params: list = []
        if expected_type is not None:
            clauses.append(f"json_extract(summary, '{pointer}') = ?")
            params.append(expected_type)
        if kind is not None:
            clauses.append("kind = ?");     params.append(kind)
        if category is not None:
            clauses.append("category = ?"); params.append(category)
        sql = (
            "SELECT kind, api, category, name, path, sha256, captured_at "
            "FROM schemas WHERE " + " AND ".join(clauses) +
            " ORDER BY kind, api, category, name"
        )
        for row in self._conn.execute(sql, params).fetchall():
            yield Row(*row)

    def find_by_type(self, type_name: str, *, kind: str | None = None
                     ) -> Iterator[Row]:
        """Yield every entry whose top-level JSON Schema type is
        `type_name` (object, array, string, integer, …)."""
        clauses = ["json_extract(summary, '$.type') = ?"]
        params: list = [type_name]
        if kind is not None:
            clauses.append("kind = ?"); params.append(kind)
        sql = (
            "SELECT kind, api, category, name, path, sha256, captured_at "
            "FROM schemas WHERE " + " AND ".join(clauses) +
            " ORDER BY kind, api, category, name"
        )
        for row in self._conn.execute(sql, params).fetchall():
            yield Row(*row)

    def json_merge_patch(self, kind: str, api: str, category: str, name: str,
                         patch: dict) -> dict:
        """Apply an RFC 7396 JSON Merge Patch to a stored schema using
        SQLite's json_patch() and persist the result. Returns the new
        schema dict."""
        api = self.resolve_api(kind, api)
        current = self.get(kind, api, category, name) or {}
        (merged,) = self._conn.execute(
            "SELECT json_patch(?, ?)",
            (json.dumps(current), json.dumps(patch)),
        ).fetchone()
        new_schema = json.loads(merged) if merged else {}
        self.put(kind, api, category, name, new_schema)
        return new_schema

    @staticmethod
    def _jsonpath_escape(s: str) -> str:
        # JSON path tokens that contain non-identifier chars must be
        # quoted. Simple check keeps queries short when possible.
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", s or ""):
            return s
        return '"' + s.replace('"', '\\"') + '"'

    # --- $ref resolution + cross-API unification -----------------------
    def resolve_ref(self, ref: str, *, container: Mapping | None = None
                    ) -> dict | None:
        """Resolve a JSON-Schema `$ref`.

        Supported forms:
          ``registry://<kind>/<api>/<category>/<name>``
              look the component up in this registry (URI-template
              aware — e.g. a JDBC concrete URI resolves via
              register_template).
          ``#/foo/bar/baz``
              standard JSON Pointer into `container`.
        """
        if ref.startswith("registry://"):
            rest = ref[len("registry://"):]
            parts = rest.split("/", 3)
            if len(parts) != 4:
                return None
            kind, api, category, name = parts
            return self.get(kind, api, category, name)
        if ref.startswith("#/") and container is not None:
            tokens = [
                t.replace("~1", "/").replace("~0", "~")
                for t in ref[2:].split("/")
            ]
            node: object = container
            for tok in tokens:
                if not isinstance(node, Mapping):
                    return None
                node = node.get(tok)
            return node if isinstance(node, dict) else None
        return None

    def unified_component(self, name: str, *, kind: str | None = None
                          ) -> dict | None:
        """Merge every registry entry that shares `name` (same slot name
        regardless of api) into one JSON Schema.

        Motivating use case: `Book` as declared by Google Books,
        Amazon, and Audible keys on ISBN but differs in optional
        fields — `unified_component("Book")` returns a single schema
        that any of the three APIs can produce, so the ComfyUI node is
        one slot on the canvas."""
        from .schema_patch import merge_schemas
        rows = list(self.find(kind=kind, name=name))
        if not rows:
            return None
        schemas: list[dict] = []
        for r in rows:
            s = self.get(r.kind, r.api, r.category, r.name)
            if isinstance(s, dict):
                s = dict(s)
                s.setdefault("$id", f"{r.kind}:{r.api}:{r.category}:{r.name}")
                schemas.append(s)
        return merge_schemas(schemas) if schemas else None
