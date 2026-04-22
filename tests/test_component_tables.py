"""Component name → SQLite table. Same mapping run both directions.

Covers:
  * JSON Schema → CREATE TABLE (types, NOT NULL, DEFAULT, CHECK)
  * PRAGMA → JSON Schema (the inverse, lossy on CHECK clauses)
  * ComponentDB: put / get / patch (json_patch) / project
  * Per-property audit rows tagged with calling api
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node.component_tables import (
    ComponentDB,
    columns_from_schema,
    create_table,
    drop_table,
    schema_from_table,
    sql_type_for,
)


_BOOK = {
    "type": "object",
    "required": ["isbn", "title"],
    "x-primary-key": ["isbn"],
    "properties": {
        "isbn":     {"type": "string", "minLength": 10, "maxLength": 17},
        "title":    {"type": "string"},
        "authors":  {"type": "array",  "items": {"type": "string"}},
        "price":    {"type": "number", "minimum": 0},
        "active":   {"type": "boolean", "default": True},
        "meta":     {"type": "object"},
    },
}


# --- sql_type_for -------------------------------------------------------
def test_sql_type_for_primitives():
    assert sql_type_for({"type": "integer"})          == "INTEGER"
    assert sql_type_for({"type": "number"})           == "REAL"
    assert sql_type_for({"type": "boolean"})          == "INTEGER"
    assert sql_type_for({"type": "string"})           == "TEXT"
    assert sql_type_for({"type": "string",
                         "format": "binary"})          == "BLOB"
    assert sql_type_for({"type": "array"})            == "TEXT"
    assert sql_type_for({"type": "object"})           == "TEXT"


def test_columns_from_schema_covers_flags():
    cols = {c["name"]: c for c in columns_from_schema(_BOOK)}
    assert cols["isbn"]["sql_type"] == "TEXT" and cols["isbn"]["not_null"] is True
    # 'title' is required and has no default → NOT NULL
    assert cols["title"]["not_null"] is True
    # 'active' has a default → NOT NULL false (optional on insert)
    assert cols["active"]["not_null"] is False and cols["active"]["default"] is True
    # JSON-shaped columns advertise CHECK(json_valid(col))
    assert "json_valid" in (cols["meta"]["check"] or "")
    assert "json_valid" in (cols["authors"]["check"] or "")


# --- create_table + schema_from_table roundtrip ------------------------
def test_create_table_produces_pragma_rows():
    conn = sqlite3.connect(":memory:")
    create_table(conn, "Book", _BOOK)
    rows = conn.execute("PRAGMA table_info(Book)").fetchall()
    names = [r[1] for r in rows]
    assert set(names) == {"isbn", "title", "authors", "price", "active", "meta"}
    # PK is isbn
    pk = [r[1] for r in rows if r[5]]
    assert pk == ["isbn"]


def test_schema_from_table_recovers_core_shape():
    conn = sqlite3.connect(":memory:")
    create_table(conn, "Book", _BOOK)
    recovered = schema_from_table(conn, "Book")
    assert recovered["type"] == "object"
    assert set(recovered["properties"]) == {"isbn", "title", "authors",
                                             "price", "active", "meta"}
    # SQLite doesn't preserve regex / min/max length → those are lossy;
    # base types are intact.
    assert recovered["properties"]["price"]["type"] == "number"
    assert recovered["properties"]["active"]["type"] == "integer"  # boolean → INTEGER
    assert recovered["properties"]["meta"]["type"] == "string"
    assert recovered["x-primary-key"] == ["isbn"]


def test_drop_table_removes_it():
    conn = sqlite3.connect(":memory:")
    create_table(conn, "Book", _BOOK)
    drop_table(conn, "Book")
    assert conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' AND name='Book'"
    ).fetchone() is None


# --- ComponentDB CRUD + projection -------------------------------------
@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "c.db"))
    d = ComponentDB(conn)
    d.register("Book", _BOOK)
    return d


def test_put_then_get_roundtrips_json_columns(db):
    db.put("Book", {
        "isbn": "9780000000001", "title": "Hi",
        "authors": ["Ada", "Grace"], "price": 9.99,
        "active": True, "meta": {"edition": "1st"},
    })
    got = db.get("Book", "9780000000001")
    # JSON columns are rehydrated to dict/list on read.
    assert got["authors"] == ["Ada", "Grace"]
    assert got["meta"]    == {"edition": "1st"}


def test_patch_via_sqlite_json_patch(db):
    db.put("Book", {"isbn": "9780000000011", "title": "T", "price": 1.0})
    events = db.patch("Book", "9780000000011", {"price": 2.0, "subtitle": "added"},
                       api="openapi/books")
    got = db.get("Book", "9780000000011")
    assert got["price"] == 2.0
    # Audit captured both changes with api tag.
    paths = {(e["op"], e["path"]) for e in events}
    assert ("replace", "/price") in paths
    # `subtitle` isn't a declared column, so it's dropped by the
    # per-column writeback — but still appears in the audit trail as an
    # 'add' op so governance sees the attempt.
    assert any(e["path"] == "/subtitle" for e in events)
    assert all(e["api"] == "openapi/books" for e in events)


def test_patch_null_removes(db):
    db.put("Book", {"isbn": "9780000000022", "title": "T", "meta": {"e": "1"}})
    db.patch("Book", "9780000000022", {"meta": None})
    got = db.get("Book", "9780000000022")
    # RFC 7396: null removes; absent column reads as None.
    assert got.get("meta") is None


def test_project_returns_subset(db):
    db.put("Book", {"isbn": "9780000000033", "title": "T", "price": 1.0,
                    "meta": {"e": "1"}, "authors": ["A"]})
    api_view = db.project("Book", "9780000000033", {
        "type": "object",
        "properties": {"isbn": {"type": "string"},
                       "title": {"type": "string"}},
    })
    assert set(api_view) == {"isbn", "title"}


# --- audit stream -------------------------------------------------------
def test_audit_scoped_per_component(db):
    db.register("Ping", {"type": "object",
                         "required": ["k"],
                         "x-primary-key": ["k"],
                         "properties": {"k": {"type": "string"}}})
    db.put("Book", {"isbn": "9780000000044", "title": "A"}, api="api1")
    db.put("Ping", {"k": "p1"}, api="api2")
    only_book = db.audit(component="Book")
    assert {e["component"] for e in only_book} == {"Book"}
    # Full log sees both.
    total = db.audit()
    assert {e["component"] for e in total} == {"Book", "Ping"}


def test_register_twice_is_idempotent(db):
    # Second register() call on the same schema shouldn't raise.
    db.register("Book", _BOOK)
    assert "Book" in db.components()
