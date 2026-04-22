"""Cross-kind JSON Schema registry.

On-disk .schema.json files are the source of truth. SQLite is a thin
index (kind / api / category / name → path + sha256 + captured_at).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.schema_registry import SchemaRegistry


_USER = {
    "type": "object",
    "required": ["id", "email"],
    "properties": {
        "id":    {"type": "integer", "format": "int64"},
        "email": {"type": "string",  "format": "email"},
    },
}

_CHAT_COMPLETIONS = {
    "operationId": "chatCompletions",
    "protocol":    "http",
    "verb":        "POST",
    "path":        "/api/v0/chat/completions",
    "input_schema":  {"type": "object", "properties": {"model": {"type": "string"}}},
    "output_schema": {"type": "object", "properties": {"choices": {"type": "array"}}},
}


@pytest.fixture
def reg(tmp_path):
    return SchemaRegistry.open(tmp_path / "registry")


# --- sanity: the index has exactly the two bookkeeping tables -----------
def test_index_only_has_thin_tables(reg):
    names = {r[0] for r in reg._conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table'"
    ).fetchall()}
    assert names == {"schemas", "uri_templates"}


# --- put / get round-trip via on-disk files -----------------------------
def test_put_writes_file_and_indexes_it(reg, tmp_path):
    row = reg.put("openapi", "lm-studio", "components", "User", _USER)
    # File exists at the advertised path.
    abs_ = reg.root / row.path
    assert abs_.is_file()
    # Contents round-trip exactly.
    assert json.loads(abs_.read_text()) == _USER
    # Retrieval goes through the index + file read.
    assert reg.get("openapi", "lm-studio", "components", "User") == _USER


def test_put_replaces_existing(reg):
    reg.put("openapi", "lm-studio", "components", "User", _USER)
    reg.put("openapi", "lm-studio", "components", "User",
            {"type": "object", "properties": {"x": {"type": "string"}}})
    got = reg.get("openapi", "lm-studio", "components", "User")
    assert list(got["properties"]) == ["x"]


def test_get_missing_returns_none(reg):
    assert reg.get("openapi", "nope", "components", "x") is None


# --- find / list --------------------------------------------------------
def test_find_by_kind_and_api(reg):
    reg.put("openapi", "lm-studio", "components", "User", _USER)
    reg.put("openapi", "lm-studio", "operations", "chatCompletions", _CHAT_COMPLETIONS)
    reg.put("asyncapi", "chat", "operations", "sendMessage", _CHAT_COMPLETIONS)
    rows = list(reg.find(kind="openapi"))
    assert {(r.category, r.name) for r in rows} == {
        ("components", "User"),
        ("operations", "chatCompletions"),
    }


def test_find_across_apis_by_component_name(reg):
    reg.put("openapi", "app-a", "components", "User", _USER)
    reg.put("openapi", "app-b", "components", "User", _USER)
    hits = list(reg.find(name="User"))
    assert {r.api for r in hits} == {"app-a", "app-b"}


# --- JDBC URI-template matching -----------------------------------------
def test_jdbc_uri_template_collapses_hosts(reg):
    reg.register_template("jdbc", "jdbc:postgresql://{host}:{port}/{db}")
    reg.put(
        "jdbc",
        "jdbc:postgresql://db1.example.com:5432/app",
        "tables", "users",
        {"type": "object", "properties": {"id": {"type": "integer"}}},
    )
    # Different concrete URI → same template → cached hit.
    got = reg.get("jdbc", "jdbc:postgresql://db2.example.com:6543/other",
                  "tables", "users")
    assert got is not None
    # find() under the template picks up the entry too.
    rows = list(reg.find(kind="jdbc",
                         api="jdbc:postgresql://another:5432/x"))
    assert len(rows) == 1 and rows[0].name == "users"


def test_sqlite_file_and_memory_share_template(reg):
    reg.register_template("jdbc", "jdbc:sqlite:{path}")
    reg.put("jdbc", "jdbc:sqlite::memory:", "tables", "t",
            {"type": "object"})
    assert reg.get("jdbc", "jdbc:sqlite:/tmp/x.db", "tables", "t") is not None


def test_unregistered_uri_uses_itself_as_template(reg):
    reg.put("jdbc", "jdbc:mariadb://x/y", "tables", "t",
            {"type": "object"})
    assert reg.get("jdbc", "jdbc:mariadb://x/y", "tables", "t") is not None
    assert reg.get("jdbc", "jdbc:mariadb://other/z", "tables", "t") is None


# --- delete / clear -----------------------------------------------------
def test_delete_removes_file_and_index_row(reg):
    row = reg.put("openapi", "a", "components", "User", _USER)
    abs_ = reg.root / row.path
    assert abs_.is_file()
    assert reg.delete("openapi", "a", "components", "User") is True
    assert not abs_.is_file()
    assert reg.get("openapi", "a", "components", "User") is None
    # Second delete is a no-op.
    assert reg.delete("openapi", "a", "components", "User") is False


def test_clear_scoped_to_api_deletes_files(reg):
    reg.put("openapi", "a", "components", "X", _USER)
    reg.put("openapi", "b", "components", "X", _USER)
    reg.clear(kind="openapi", api="a")
    assert reg.get("openapi", "a", "components", "X") is None
    assert reg.get("openapi", "b", "components", "X") is not None


def test_clear_all_empties_everything(reg):
    reg.put("openapi", "a", "components", "X", _USER)
    reg.put("asyncapi", "b", "operations", "Y", _CHAT_COMPLETIONS)
    reg.clear()
    assert list(reg.find()) == []
    # Files also gone.
    schemas_dir = reg.root / "schemas"
    leaves = [p for p in schemas_dir.rglob("*.schema.json")]
    assert leaves == []
