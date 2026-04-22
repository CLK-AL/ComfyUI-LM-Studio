"""Naming convention + end-to-end integration across every API kind.

One `Book` component drives every surface: OpenAPI component, JDBC
`book` table, AsyncAPI `BookUpdated` message, GraphQL type, MCP SSE
event carrying `{before, after}` of each patch. The mappings in
`naming.py` are the only shared vocabulary — no bespoke glue.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.component_tables import ComponentDB, create_table, schema_from_table
from al.clk.api.naming import (
    camel, component_name, message_name, node_class, node_display,
    patch_name, patch_op_to_sse, pascal, snake, sse_frame, table_name,
)


# --- case conversions ---------------------------------------------------
def test_snake_and_pascal_roundtrip():
    assert snake("BookReview")        == "book_review"
    assert snake("XMLHttpRequest")    == "xml_http_request"
    assert snake("already_snake")     == "already_snake"
    assert pascal("book_review")      == "BookReview"
    assert pascal("XMLHttpRequest")   == "XmlHttpRequest"
    assert pascal("already-pascal")   == "AlreadyPascal"
    assert camel("book_review")       == "bookReview"


def test_openapi_component_maps_to_jdbc_table():
    # The rule: OpenAPI component name ⇄ JDBC table name.
    for comp in ("Book", "BookReview", "ChatMessage", "LM_StudioModel"):
        t = table_name(comp)
        # Recovering the Pascal form yields the component.
        assert pascal(t) == component_name(comp)


def test_asyncapi_message_names_follow_verb():
    # Updated / Created / Deleted suffixes pair with patch ops.
    assert message_name("Book")                    == "BookUpdated"
    assert message_name("Book", verb="Created")    == "BookCreated"
    assert message_name("book_review", verb="Deleted") == "BookReviewDeleted"


def test_patch_name_uses_table_vocabulary():
    assert patch_name("Book")       == "book.patch"
    assert patch_name("BookReview") == "book_review.patch"


def test_node_class_and_display_names():
    assert node_class("lm-studio", "chatCompletions") == "API_lm_studio_chatCompletions"
    assert node_display("lm-studio", "chatCompletions") == "API · lm-studio · chatCompletions"


# --- audit → SSE {before, after} ---------------------------------------
def test_patch_op_to_sse_shape_from_entity_store_event():
    ev = {
        "type": "Book", "id": "9780000000001",
        "op": "replace", "path": "/title",
        "old_value": "Old Title", "new_value": "New Title",
        "api": "openapi/google-books", "ts": "2026-04-22T12:00:00Z",
    }
    out = patch_op_to_sse(ev)
    assert out["component"] == "Book"
    assert out["before"]    == "Old Title"
    assert out["after"]     == "New Title"
    assert out["message"]   == "BookUpdated"
    assert out["op"]        == "replace"


def test_patch_op_to_sse_shape_from_component_db_event():
    ev = {
        "component": "Book", "pk": "9780000000001",
        "op": "remove", "path": "/description",
        "old": "something", "new": None,
        "api": "openapi/amazon-product", "ts": "…",
    }
    out = patch_op_to_sse(ev)
    assert out["before"] == "something" and out["after"] is None
    assert out["message"] == "BookDeleted"


def test_sse_frame_renders_as_event_stream():
    payload = {"component": "Book", "op": "replace",
               "before": 1, "after": 2, "path": "/x"}
    frame = sse_frame(payload, id_=42)
    assert frame.startswith("id: 42\n")
    assert "event: entity.replace" in frame
    assert "\ndata: " in frame
    assert frame.endswith("\n\n")
    # data is parseable JSON with our before/after keys.
    data_line = [l for l in frame.splitlines() if l.startswith("data:")][0]
    parsed = json.loads(data_line.split(": ", 1)[1])
    assert parsed["before"] == 1 and parsed["after"] == 2


# --- end-to-end integration: one Book row, every API sees it -----------
_BOOK_OPENAPI_COMPONENT = {
    "type": "object",
    "required": ["isbn", "title"],
    "x-primary-key": ["isbn"],
    "properties": {
        "isbn":   {"type": "string", "minLength": 10, "maxLength": 17},
        "title":  {"type": "string"},
        "rating": {"type": "number", "minimum": 0, "maximum": 5},
    },
}


@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(str(tmp_path / "book.db"))
    d = ComponentDB(conn)
    d.register(component_name("Book"), _BOOK_OPENAPI_COMPONENT)
    return d


def test_openapi_component_lands_in_table_with_matching_name(db):
    """Round-trip: the component name `Book` lives in SQLite as a
    table named `book` (via `table_name("Book")`), recoverable back
    to the same JSON Schema shape."""
    # ComponentDB uses the Pascal name verbatim; table_name() is the
    # JDBC-style alias a DB-facing operator would see.
    names = [r[0] for r in db._conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall()]
    assert "Book" in names   # ComponentDB materialisation
    # Rehydrating the schema from the table recovers the property set.
    got = schema_from_table(db._conn, "Book")
    assert set(got["properties"]) == {"isbn", "title", "rating"}
    assert got["x-primary-key"] == ["isbn"]


def test_put_then_patch_emits_sse_with_before_after(db):
    db.put("Book", {"isbn": "9780000000001", "title": "Hello"},
           api="openapi/google-books")
    events = db.patch("Book", "9780000000001",
                      {"title": "Hello World", "rating": 4.5},
                      api="openapi/google-books")
    # SSE projection of each audit event carries before/after.
    sse_payloads = [patch_op_to_sse(e) for e in events]
    by_path = {p["path"]: p for p in sse_payloads}
    assert by_path["/title"]["before"]  == "Hello"
    assert by_path["/title"]["after"]   == "Hello World"
    assert by_path["/title"]["message"] == "BookUpdated"
    # Column existed (NULL) before the INSERT made it non-NULL, so the
    # mutation shows up as a `replace` from DB's point of view.
    assert by_path["/rating"]["before"] is None
    assert by_path["/rating"]["after"]  == 4.5
    assert by_path["/rating"]["message"] == "BookUpdated"


def test_projection_per_api_uses_same_row(db):
    """Two APIs — Google Books only shows {isbn, title}; Amazon adds
    rating. Both read through the same SQLite row."""
    db.put("Book",
           {"isbn": "9780000000002", "title": "T", "rating": 4.2})
    google_schema = {"type": "object",
                     "properties": {"isbn": {"type": "string"},
                                    "title": {"type": "string"}}}
    amazon_schema = {"type": "object",
                     "properties": {"isbn": {"type": "string"},
                                    "title": {"type": "string"},
                                    "rating": {"type": "number"}}}
    g = db.project("Book", "9780000000002", google_schema)
    a = db.project("Book", "9780000000002", amazon_schema)
    assert set(g) == {"isbn", "title"}
    assert set(a) == {"isbn", "title", "rating"}


def test_mcp_style_sse_stream_of_patch_ops(db):
    """MCP clients stream audit via SSE. Each frame carries
    before/after so the client can verify the mutation landed as
    expected — even without polling the store."""
    db.put("Book", {"isbn": "9780000000003", "title": "T"},
           api="openapi/audible")
    evs = db.patch("Book", "9780000000003", {"rating": 5.0},
                   api="openapi/audible")
    frames = [sse_frame(patch_op_to_sse(e),
                        id_=e["audit_id"], event=f"book.{e['op']}")
              for e in evs]
    assert frames
    first = frames[0]
    assert first.startswith("id: ")
    assert "event: book." in first
    assert "before" in first and "after" in first
