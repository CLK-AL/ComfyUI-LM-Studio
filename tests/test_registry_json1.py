"""SQLite JSON1 inside the schema registry — search by property name,
search by type, and in-SQL json_patch merges.

Goal: the same Google Books / Amazon / Audible → 'Book with ISBN' story
but answered by the DB, not by Python.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node.schema_registry import SchemaRegistry


BOOK_GOOGLE = {
    "type": "object",
    "required": ["isbn", "title"],
    "properties": {
        "isbn":      {"type": "string"},
        "title":     {"type": "string"},
        "pageCount": {"type": "integer"},
    },
}
BOOK_AMAZON = {
    "type": "object",
    "required": ["isbn"],
    "properties": {
        "isbn":   {"type": "string"},
        "price":  {"type": "number"},
        "rating": {"type": "number"},
    },
}
BOOK_AUDIBLE = {
    "type": "object",
    "required": ["isbn", "narrator"],
    "properties": {
        "isbn":     {"type": "string"},
        "narrator": {"type": "string"},
        "runtime":  {"type": "integer"},
    },
}
USER = {
    "type": "object",
    "required": ["id", "email"],
    "properties": {"id": {"type": "integer"}, "email": {"type": "string"}},
}


@pytest.fixture
def reg(tmp_path):
    r = SchemaRegistry.open(tmp_path / "reg")
    r.put("openapi", "google-books",   "components", "Book", BOOK_GOOGLE)
    r.put("openapi", "amazon-product", "components", "Book", BOOK_AMAZON)
    r.put("openapi", "audible",        "components", "Book", BOOK_AUDIBLE)
    r.put("openapi", "identity",       "components", "User", USER)
    return r


# --- the summary JSON column is populated and valid ---------------------
def test_summary_column_is_valid_json(reg):
    rows = reg._conn.execute("SELECT summary FROM schemas").fetchall()
    # CHECK (json_valid(summary)) would have rejected bad entries.
    assert rows and all(r[0].startswith("{") for r in rows)


# --- find_by_property ---------------------------------------------------
def test_find_by_property_returns_cross_api_matches(reg):
    # Every book source has an isbn — the user entity does not.
    rows = list(reg.find_by_property("isbn"))
    apis = {r.api for r in rows}
    assert apis == {"google-books", "amazon-product", "audible"}


def test_find_by_property_narrow_by_type(reg):
    rows = list(reg.find_by_property("rating", expected_type="number"))
    assert [r.api for r in rows] == ["amazon-product"]
    # And the negative case:
    assert list(reg.find_by_property("rating", expected_type="string")) == []


def test_find_by_property_filtered_by_kind(reg):
    rows = list(reg.find_by_property("isbn", kind="openapi"))
    assert len(rows) == 3
    assert list(reg.find_by_property("isbn", kind="asyncapi")) == []


# --- find_by_type -------------------------------------------------------
def test_find_by_type_object(reg):
    objs = list(reg.find_by_type("object"))
    # Four object schemas: 3 Books + 1 User.
    assert {(r.api, r.name) for r in objs} == {
        ("google-books",   "Book"),
        ("amazon-product", "Book"),
        ("audible",        "Book"),
        ("identity",       "User"),
    }


def test_find_by_type_string_returns_nothing_here(reg):
    # All stored schemas are objects in this fixture.
    assert list(reg.find_by_type("string")) == []


# --- json_merge_patch (SQLite's json_patch under the hood) --------------
def test_json_merge_patch_adds_property_and_persists(reg):
    merged = reg.json_merge_patch(
        "openapi", "google-books", "components", "Book",
        {"properties": {"isbn13": {"type": "string"}}},
    )
    # Patch applied → new property present.
    assert "isbn13" in merged["properties"]
    # Persistence: a second get reads the same from disk.
    again = reg.get("openapi", "google-books", "components", "Book")
    assert "isbn13" in again["properties"]


def test_json_merge_patch_null_removes_property(reg):
    # RFC 7396 — a null value on a key means "remove it".
    merged = reg.json_merge_patch(
        "openapi", "amazon-product", "components", "Book",
        {"properties": {"rating": None}},
    )
    assert "rating" not in merged["properties"]


# --- integration: find_by_property + unified_component ------------------
def test_find_isbn_apis_then_unify(reg):
    apis = [r.api for r in reg.find_by_property("isbn", expected_type="string")]
    assert len(apis) == 3
    book = reg.unified_component("Book")
    assert book is not None
    assert set(book["properties"]) >= {"isbn", "title", "narrator",
                                        "price", "rating", "runtime",
                                        "pageCount"}
    assert book["required"] == ["isbn"]


# --- SQLite JSON1 availability sanity -----------------------------------
def test_sqlite_json1_functions_are_available():
    conn = sqlite3.connect(":memory:")
    # json_valid — single-arg, returns 1/0
    (v,) = conn.execute("SELECT json_valid('{\"a\":1}')").fetchone()
    assert v == 1
    # json_extract — pointer form
    (v,) = conn.execute("SELECT json_extract('{\"a\":1}', '$.a')").fetchone()
    assert v == 1
    # json_patch — two args, RFC 7396 merge
    (v,) = conn.execute(
        "SELECT json_patch('{\"a\":1,\"b\":2}', '{\"b\":null,\"c\":3}')"
    ).fetchone()
    import json as _json
    merged = _json.loads(v)
    assert merged == {"a": 1, "c": 3}
    conn.close()
