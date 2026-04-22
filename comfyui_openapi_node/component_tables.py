"""Each component name → one SQLite table.

Same mapping run in both directions:

    JSON Schema (object)  ──▶  CREATE TABLE <name>
                              (per-property columns typed via sql_types)
    PRAGMA table_info     ──▶  JSON Schema (object)

    Any row is a body blob in a JSON1-validated TEXT column — mutations
    arrive as RFC 7396 merge patches and land via SQL json_patch().
    Per-property diffs hit the append-only audit log that `EntityStore`
    already knows how to stream over SSE.

    Cross-API unification: `unified_component("Book")` from
    schema_registry hands us a union JSON Schema; `ensure("Book",
    unified)` materialises it as one SQLite table with every property
    column present, and each API projection is a `json_extract` away.

Primary-key discovery order:
    1. `x-primary-key: [...]`        explicit (array of property names)
    2. `"required": [...]` with `"id"` present → `id`
    3. first `required` entry
    4. fallback: `rowid` (SQLite implicit)

The module is intentionally thin — only the parts that have to live
in Python for the tests and the ComfyUI registry side. The Kotlin
mock does the same thing via Spring JdbcTemplate + DatabaseMetaData
so both halves converge on identical DDL.
"""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Iterable, Mapping

from .schema_patch import diff


# --- JSON Schema → SQL type ---------------------------------------------
def sql_type_for(schema: Mapping) -> str:
    """Pick the SQLite affinity that best represents a JSON Schema
    fragment. SQLite is loosely typed — we lean on CHECK constraints
    for JSON shape, not column types."""
    if not isinstance(schema, Mapping):
        return "TEXT"
    t = schema.get("type")
    if t == "integer":
        return "INTEGER"
    if t == "number":
        return "REAL"
    if t == "boolean":
        return "INTEGER"    # 0 / 1
    if t == "string":
        fmt = schema.get("format") or ""
        if fmt in ("byte", "binary"):
            return "BLOB"
        return "TEXT"
    # array / object / oneOf / allOf / anyOf / $ref → TEXT(JSON)
    return "TEXT"


def _safe_ident(name: str) -> str:
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name or ""):
        return name
    return '"' + name.replace('"', '""') + '"'


def _primary_key(schema: Mapping) -> list[str]:
    xpk = schema.get("x-primary-key")
    if isinstance(xpk, list) and xpk:
        return [str(k) for k in xpk]
    required = list(schema.get("required") or [])
    props = schema.get("properties") or {}
    if "id" in props and "id" in required:
        return ["id"]
    if required:
        return [required[0]]
    return []  # falls back to SQLite rowid


def _check_for(prop: Mapping) -> str | None:
    """Emit SQLite CHECK constraints for lossless JSON-Schema fidelity.

    Every returned fragment references `{col}` — the caller replaces
    it with the properly-escaped column identifier."""
    t = prop.get("type")
    if t == "boolean":
        return "{col} IN (0, 1)"
    if t == "integer":
        lo = prop.get("minimum")
        hi = prop.get("maximum")
        clauses = []
        if isinstance(lo, (int, float)) and not isinstance(lo, bool):
            clauses.append(f"{{col}} >= {int(lo)}")
        if isinstance(hi, (int, float)) and not isinstance(hi, bool):
            clauses.append(f"{{col}} <= {int(hi)}")
        return " AND ".join(clauses) if clauses else None
    if t == "number":
        lo = prop.get("minimum")
        hi = prop.get("maximum")
        clauses = []
        if isinstance(lo, (int, float)) and not isinstance(lo, bool):
            clauses.append(f"{{col}} >= {float(lo)}")
        if isinstance(hi, (int, float)) and not isinstance(hi, bool):
            clauses.append(f"{{col}} <= {float(hi)}")
        return " AND ".join(clauses) if clauses else None
    if t == "string":
        pat = prop.get("pattern")
        mn  = prop.get("minLength")
        mx  = prop.get("maxLength")
        clauses = []
        if isinstance(mn, int):
            clauses.append(f"length({{col}}) >= {mn}")
        if isinstance(mx, int):
            clauses.append(f"length({{col}}) <= {mx}")
        if isinstance(pat, str):
            # SQLite has no regex by default; keep the pattern as a
            # comment so the DDL still documents it.
            clauses.append(f"1 = 1 /* pattern: {pat.replace('*/', '*_/')} */")
        return " AND ".join(clauses) if clauses else None
    if t in ("array", "object"):
        return "json_valid({col})"
    return None


def columns_from_schema(schema: Mapping) -> list[dict]:
    """Return one dict per property, DDL-ready."""
    required = set(schema.get("required") or [])
    out: list[dict] = []
    for name, prop in (schema.get("properties") or {}).items():
        col = {
            "name":     name,
            "sql_type": sql_type_for(prop if isinstance(prop, Mapping) else {}),
            "not_null": name in required and (not isinstance(prop, Mapping)
                                              or "default" not in prop),
            "default":  (prop.get("default") if isinstance(prop, Mapping) else None),
            "check":    (_check_for(prop) if isinstance(prop, Mapping) else None),
            "json":     (isinstance(prop, Mapping) and
                         prop.get("type") in ("array", "object")),
        }
        out.append(col)
    return out


# --- create / drop / introspect -----------------------------------------
def create_table(conn: sqlite3.Connection, name: str, schema: Mapping) -> None:
    cols = columns_from_schema(schema)
    if not cols:
        # object with no properties — still reserve a rowid-only table.
        conn.execute(f"CREATE TABLE IF NOT EXISTS {_safe_ident(name)} "
                     "(rowid INTEGER PRIMARY KEY)")
        conn.commit()
        return
    pk = _primary_key(schema)
    parts: list[str] = []
    for c in cols:
        piece = f"{_safe_ident(c['name'])} {c['sql_type']}"
        if c["not_null"]:
            piece += " NOT NULL"
        if c["default"] is not None:
            piece += f" DEFAULT {_sql_literal(c['default'])}"
        if c["check"]:
            # Replace {col} placeholder with the escaped column name.
            piece += f" CHECK ({c['check'].replace('{col}', _safe_ident(c['name']))})"
        parts.append(piece)
    if pk:
        parts.append("PRIMARY KEY (" +
                     ", ".join(_safe_ident(p) for p in pk) + ")")
    ddl = f"CREATE TABLE IF NOT EXISTS {_safe_ident(name)} ({', '.join(parts)})"
    conn.execute(ddl)
    conn.commit()


def drop_table(conn: sqlite3.Connection, name: str) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {_safe_ident(name)}")
    conn.commit()


def schema_from_table(conn: sqlite3.Connection, name: str) -> dict:
    """PRAGMA introspection → JSON Schema. Inverse of create_table
    (lossy on checks / regex patterns — those survive as SQLite CHECK
    clauses, not in the emitted JSON Schema)."""
    rows = conn.execute(f"PRAGMA table_info({_safe_ident(name)})").fetchall()
    if not rows:
        return {"type": "object", "properties": {}}
    props: dict[str, dict] = {}
    required: list[str] = []
    pks: list[tuple[int, str]] = []
    for cid, col_name, col_type, notnull, default, pk in rows:
        t = col_type.upper()
        if t == "INTEGER":
            props[col_name] = {"type": "integer"}
        elif t == "REAL":
            props[col_name] = {"type": "number"}
        elif t == "BLOB":
            props[col_name] = {"type": "string", "format": "binary"}
        else:  # TEXT and anything exotic
            props[col_name] = {"type": "string"}
        if default is not None:
            props[col_name]["default"] = _coerce_literal(default, t)
        if notnull and default is None:
            required.append(col_name)
        if pk:
            pks.append((pk, col_name))
    schema: dict = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    pks.sort()
    if pks:
        schema["x-primary-key"] = [n for _, n in pks]
    return schema


# --- CRUD helpers -------------------------------------------------------
def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        # Preserve SQL function defaults like `CURRENT_TIMESTAMP` as-is.
        upper = value.upper()
        if upper in ("CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME") \
           or upper.endswith("()"):
            return value
        return "'" + value.replace("'", "''") + "'"
    return "'" + json.dumps(value).replace("'", "''") + "'"


def _coerce_literal(value: Any, sql_type: str) -> Any:
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if sql_type == "INTEGER":
        try:
            return int(value)
        except (TypeError, ValueError):
            return value
    if sql_type == "REAL":
        try:
            return float(value)
        except (TypeError, ValueError):
            return value
    return value


class ComponentDB:
    """High-level CRUD + projection + audit on per-component tables.

    Everything routes through `json_patch()` for mutations so the same
    semantics hold regardless of whether the table was created from an
    OpenAPI component, an AsyncAPI message, a JDBC table descriptor,
    or a merged cross-API union."""

    _AUDIT_DDL = (
        "CREATE TABLE IF NOT EXISTS component_audit ("
        "  audit_id   INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  component  TEXT NOT NULL,"
        "  pk         TEXT NOT NULL,"
        "  ts         TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),"
        "  op         TEXT NOT NULL,"
        "  path       TEXT NOT NULL,"
        "  old_value  TEXT,"
        "  new_value  TEXT,"
        "  api        TEXT"
        ")"
    )

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        conn.execute(self._AUDIT_DDL)
        conn.commit()
        self._schemas: dict[str, dict] = {}

    # --- registration ---------------------------------------------------
    def register(self, name: str, schema: Mapping) -> None:
        create_table(self._conn, name, schema)
        self._schemas[name] = dict(schema)

    def unregister(self, name: str) -> None:
        drop_table(self._conn, name)
        self._schemas.pop(name, None)

    def components(self) -> list[str]:
        return sorted(self._schemas)

    def schema(self, name: str) -> dict:
        """Live-reflect the schema (inverse of create_table)."""
        return schema_from_table(self._conn, name)

    # --- put / get / patch ---------------------------------------------
    def _pk_cols(self, name: str) -> list[str]:
        return _primary_key(self._schemas.get(name) or self.schema(name))

    def _row_dict(self, name: str, pk_value: Any) -> dict | None:
        pks = self._pk_cols(name)
        if not pks:
            return None
        pk_vals = pk_value if isinstance(pk_value, (list, tuple)) else [pk_value]
        where = " AND ".join(f"{_safe_ident(k)} = ?" for k in pks)
        row = self._conn.execute(
            f"SELECT * FROM {_safe_ident(name)} WHERE {where}", pk_vals
        ).fetchone()
        if row is None:
            return None
        cols = [c[0] for c in self._conn.execute(
            f"SELECT * FROM {_safe_ident(name)} LIMIT 0"
        ).description]
        return dict(zip(cols, row))

    def put(self, name: str, row: Mapping, *, api: str | None = None) -> None:
        cols = list(row.keys())
        placeholders = ", ".join("?" for _ in cols)
        sql = (f"INSERT OR REPLACE INTO {_safe_ident(name)} "
               f"({', '.join(_safe_ident(c) for c in cols)}) "
               f"VALUES ({placeholders})")
        vals = [_maybe_jsonify(row[c], self._schemas.get(name, {}), c) for c in cols]
        pks = self._pk_cols(name)
        pk_value = [row[c] for c in pks] if pks else None
        old = self._row_dict(name, pk_value) if pk_value else None
        self._conn.execute(sql, vals)
        self._log_event(name, pk_value, "put", "",
                        old, dict(row), api)
        self._conn.commit()

    def get(self, name: str, pk_value: Any) -> dict | None:
        row = self._row_dict(name, pk_value)
        if row is None:
            return None
        schema = self._schemas.get(name) or self.schema(name)
        # Re-inflate JSON columns.
        for pname, pschema in (schema.get("properties") or {}).items():
            if isinstance(pschema, Mapping) and pschema.get("type") in ("array", "object"):
                if isinstance(row.get(pname), str):
                    try:
                        row[pname] = json.loads(row[pname])
                    except Exception:
                        pass
        return row

    def patch(self, name: str, pk_value: Any, patch_doc: Mapping,
              *, api: str | None = None) -> list[dict]:
        pks = self._pk_cols(name)
        if not pks:
            raise RuntimeError(f"component {name!r} has no primary key")
        pk_vals = pk_value if isinstance(pk_value, (list, tuple)) else [pk_value]
        old = self.get(name, pk_value) or {}
        # Use SQLite's json_patch for RFC 7396 semantics.
        (merged_json,) = self._conn.execute(
            "SELECT json_patch(?, ?)",
            (json.dumps(old, ensure_ascii=False),
             json.dumps(dict(patch_doc), ensure_ascii=False)),
        ).fetchone()
        merged = json.loads(merged_json) if merged_json else {}
        # Writeback is scoped to columns that actually exist on the
        # table. Keys a patch tries to add that aren't declared in the
        # schema are silently dropped *from the DB writeback* but
        # still recorded in the audit trail below — governance wants
        # to see the attempt.
        known_cols = {c[1] for c in self._conn.execute(
            f"PRAGMA table_info({_safe_ident(name)})"
        ).fetchall()}
        persisted = {k: v for k, v in merged.items() if k in known_cols}
        if not persisted:
            where = " AND ".join(f"{_safe_ident(k)} = ?" for k in pks)
            self._conn.execute(
                f"DELETE FROM {_safe_ident(name)} WHERE {where}", pk_vals
            )
        else:
            cols = list(persisted.keys())
            placeholders = ", ".join("?" for _ in cols)
            sql = (f"INSERT OR REPLACE INTO {_safe_ident(name)} "
                   f"({', '.join(_safe_ident(c) for c in cols)}) "
                   f"VALUES ({placeholders})")
            vals = [_maybe_jsonify(persisted[c], self._schemas.get(name, {}), c)
                    for c in cols]
            self._conn.execute(sql, vals)

        # Per-property audit.
        events: list[dict] = []
        for op in diff(old, merged):
            ev = self._log_event(
                name, pk_vals, op["op"], op["path"],
                _try_get_ptr(old, op["path"]),
                op.get("value"),
                api,
            )
            events.append(ev)
        self._conn.commit()
        return events

    def project(self, name: str, pk_value: Any, schema: Mapping) -> dict | None:
        """Return only the properties that `schema` names — the API
        projection view of the row. SQL is `SELECT col1, col2, ...`
        so the DB does the filtering, not Python."""
        row = self.get(name, pk_value)
        if row is None:
            return None
        if (schema.get("type") or "object") != "object":
            return row
        props = schema.get("properties") or {}
        if not props:
            return row
        return {k: row[k] for k in props if k in row}

    # --- audit ----------------------------------------------------------
    def _log_event(self, component: str, pk_value: Any,
                   op: str, path: str, old: Any, new: Any,
                   api: str | None) -> dict:
        pk_key = json.dumps(pk_value)
        cur = self._conn.execute(
            "INSERT INTO component_audit "
            "(component, pk, op, path, old_value, new_value, api) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                component, pk_key, op, path,
                None if old is None else json.dumps(old, ensure_ascii=False),
                None if new is None else json.dumps(new, ensure_ascii=False),
                api,
            ),
        )
        return {
            "audit_id": cur.lastrowid,
            "component": component,
            "pk": pk_value,
            "op": op, "path": path,
            "old": old, "new": new, "api": api,
        }

    def audit(self, *, component: str | None = None, since: int = 0
              ) -> list[dict]:
        clauses = ["audit_id > ?"]
        params: list[Any] = [since]
        if component is not None:
            clauses.append("component = ?"); params.append(component)
        q = ("SELECT audit_id, component, pk, ts, op, path, old_value, new_value, api"
             " FROM component_audit WHERE " + " AND ".join(clauses)
             + " ORDER BY audit_id")
        out: list[dict] = []
        for row in self._conn.execute(q, params).fetchall():
            aid, comp, pk_key, ts, op, path, old_j, new_j, api = row
            out.append({
                "audit_id": aid, "component": comp,
                "pk": json.loads(pk_key), "ts": ts,
                "op": op, "path": path,
                "old": json.loads(old_j) if old_j is not None else None,
                "new": json.loads(new_j) if new_j is not None else None,
                "api": api,
            })
        return out


# --- helpers -------------------------------------------------------------
def _maybe_jsonify(value: Any, schema: Mapping, col: str) -> Any:
    """Serialise array/object column values to JSON strings at write."""
    pschema = (schema.get("properties") or {}).get(col) or {}
    if isinstance(pschema, Mapping) and pschema.get("type") in ("array", "object"):
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
    return value


def _try_get_ptr(doc: Any, pointer: str) -> Any:
    if not pointer:
        return doc
    try:
        from .schema_patch import _split_pointer, _get_by_pointer
        return _get_by_pointer(doc, _split_pointer(pointer))
    except Exception:
        return None
