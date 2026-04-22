"""JSON Pointer / Patch / schema-merge + cross-API $ref resolution.

Motivating example: Google Books, Amazon, Audible — three APIs that
describe a "Book" keyed by ISBN with overlapping but not identical
field sets. `registry.unified_component("Book")` folds them into a
single JSON Schema that any of the three can satisfy.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.schema_patch import apply_patch, diff, merge_schemas
from al.clk.api.schema_registry import SchemaRegistry


# --- JSON Pointer / Patch (RFC 6902 subset) -----------------------------
def test_diff_flat_scalars():
    p = diff({"a": 1, "b": 2}, {"a": 1, "b": 3})
    assert p == [{"op": "replace", "path": "/b", "value": 3}]


def test_diff_add_and_remove():
    p = diff({"a": 1, "b": 2}, {"a": 1, "c": 9})
    # order can vary — normalise
    ops = {(o["op"], o["path"]) for o in p}
    assert ("remove", "/b") in ops
    assert ("add", "/c") in ops


def test_diff_recurses_into_nested_objects():
    p = diff({"a": {"x": 1}}, {"a": {"x": 2, "y": 3}})
    ops = {(o["op"], o["path"]) for o in p}
    assert ("replace", "/a/x") in ops
    assert ("add", "/a/y") in ops


def test_diff_lists_are_atomic():
    p = diff({"xs": [1, 2]}, {"xs": [1, 2, 3]})
    assert p == [{"op": "replace", "path": "/xs", "value": [1, 2, 3]}]


def test_apply_patch_roundtrip():
    a = {"a": 1, "b": {"c": 2}}
    b = {"a": 10, "b": {"c": 2, "d": 3}}
    p = diff(a, b)
    assert apply_patch(a, p) == b


def test_apply_patch_supports_list_append_dash():
    doc = {"xs": [1, 2]}
    apply_patch(doc, [{"op": "add", "path": "/xs/-", "value": 3}])
    assert doc["xs"] == [1, 2, 3]


def test_json_pointer_escaping():
    a = {"a/b": {"~x": 1}}
    b = {"a/b": {"~x": 2}}
    p = diff(a, b)
    # '/' → '~1' and '~' → '~0' in pointer tokens.
    assert p == [{"op": "replace", "path": "/a~1b/~0x", "value": 2}]


# --- merge_schemas ------------------------------------------------------
def _google_book():
    return {
        "$id": "google:Book",
        "type": "object",
        "required": ["isbn", "title"],
        "properties": {
            "isbn":        {"type": "string"},
            "title":       {"type": "string"},
            "authors":     {"type": "array", "items": {"type": "string"}},
            "pageCount":   {"type": "integer"},
            "publishedDate": {"type": "string", "format": "date"},
        },
    }


def _amazon_book():
    return {
        "$id": "amazon:Book",
        "type": "object",
        "required": ["isbn"],
        "properties": {
            "isbn":        {"type": "string"},
            "title":       {"type": "string"},
            "authors":     {"type": "array", "items": {"type": "string"}},
            "price":       {"type": "number"},
            "rating":      {"type": "number", "minimum": 0, "maximum": 5},
        },
    }


def _audible_book():
    return {
        "$id": "audible:Book",
        "type": "object",
        "required": ["isbn", "title", "narrator"],
        "properties": {
            "isbn":       {"type": "string"},
            "title":      {"type": "string"},
            "narrator":   {"type": "string"},
            "runtimeMin": {"type": "integer"},
        },
    }


def test_merge_keeps_intersecting_required():
    merged = merge_schemas([_google_book(), _amazon_book(), _audible_book()])
    # `isbn` is required by all three; `title` is not required by amazon.
    assert set(merged["required"]) == {"isbn"}


def test_merge_unions_properties():
    merged = merge_schemas([_google_book(), _amazon_book(), _audible_book()])
    # Every property across the three surfaces is available.
    expected = {"isbn", "title", "authors", "pageCount", "publishedDate",
                "price", "rating", "narrator", "runtimeMin"}
    assert expected <= set(merged["properties"].keys())


def test_merge_widens_numeric_bounds():
    a = {"type": "number", "minimum": 0, "maximum": 10}
    b = {"type": "number", "minimum": -5, "maximum": 20}
    m = merge_schemas([a, b])
    assert m["minimum"] == -5 and m["maximum"] == 20


def test_merge_unions_enum():
    merged = merge_schemas([
        {"enum": ["user", "assistant"]},
        {"enum": ["user", "system"]},
    ])
    assert merged["enum"] == ["user", "assistant", "system"]


def test_merge_records_provenance():
    merged = merge_schemas([_google_book(), _amazon_book(), _audible_book()])
    assert merged["x-sources"] == ["google:Book", "amazon:Book", "audible:Book"]


# --- registry.unified_component + resolve_ref ---------------------------
@pytest.fixture
def book_registry(tmp_path):
    reg = SchemaRegistry.open(tmp_path / "reg")
    reg.put("openapi", "google-books",   "components", "Book", _google_book())
    reg.put("openapi", "amazon-product", "components", "Book", _amazon_book())
    reg.put("openapi", "audible",        "components", "Book", _audible_book())
    return reg


def test_unified_component_across_apis(book_registry):
    book = book_registry.unified_component("Book")
    assert book is not None
    assert set(book["properties"]) >= {"isbn", "title", "narrator", "rating"}
    assert book["required"] == ["isbn"]


def test_resolve_registry_ref(book_registry):
    schema = book_registry.resolve_ref(
        "registry://openapi/google-books/components/Book"
    )
    assert schema is not None
    assert schema["properties"]["pageCount"]["type"] == "integer"


def test_resolve_local_pointer_in_container(book_registry):
    container = {"components": {"schemas": {"Book": _google_book()}}}
    schema = book_registry.resolve_ref(
        "#/components/schemas/Book", container=container
    )
    assert schema["$id"] == "google:Book"


def test_resolve_ref_missing_returns_none(book_registry):
    assert book_registry.resolve_ref("registry://openapi/nowhere/components/X") is None
    assert book_registry.resolve_ref("#/no/such/pointer",
                                     container={"a": 1}) is None
