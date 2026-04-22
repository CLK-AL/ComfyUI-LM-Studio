"""Schema registry — SQLite-backed cache of discovered JDBC schemas,
keyed by URI template. Holds NO row data, just table/column metadata.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node.schema_registry import SchemaRegistry


_DEMO = {
    "tables": [
        {
            "name": "users",
            "primary_key": ["id"],
            "columns": [
                {"name": "id",    "sql_type": "BIGINT",  "pg_type": "int8",
                 "nullable": False},
                {"name": "email", "sql_type": "VARCHAR", "size": 255,
                 "nullable": False},
                {"name": "tags",  "sql_type": "ARRAY",   "nullable": True,
                 "default": None},
            ],
        }
    ]
}


@pytest.fixture
def reg(tmp_path):
    return SchemaRegistry.open(tmp_path / "reg.db")


# --- put / get roundtrip -------------------------------------------------
def test_put_then_get_roundtrip(reg):
    uri = "jdbc:postgresql://db.example.com:5432/app"
    assert reg.get(uri) is None
    reg.put(uri, _DEMO, driver="postgresql")
    got = reg.get(uri)
    assert got is not None
    # Table name + PK preserved.
    assert got["tables"][0]["name"] == "users"
    assert got["tables"][0]["primary_key"] == ["id"]
    # Columns preserved in order and with type metadata.
    cols = got["tables"][0]["columns"]
    assert [c["name"] for c in cols] == ["id", "email", "tags"]
    assert cols[0]["sql_type"] == "BIGINT" and cols[0]["pg_type"] == "int8"
    assert cols[1]["size"] == 255
    assert cols[2]["nullable"] is True


def test_put_is_idempotent_and_replaces(reg):
    uri = "jdbc:sqlite:/tmp/one.db"
    reg.put(uri, _DEMO)
    reg.put(uri, {"tables": [
        {"name": "users", "primary_key": ["id"],
         "columns": [{"name": "id", "sql_type": "INTEGER", "nullable": False}]},
    ]})
    got = reg.get(uri)
    assert len(got["tables"][0]["columns"]) == 1


# --- URI template matching ----------------------------------------------
def test_template_collapses_per_host_port_db(reg):
    reg.register_template("jdbc:postgresql://{host}:{port}/{db}")
    reg.put("jdbc:postgresql://db1.example.com:5432/app", _DEMO,
            driver="postgresql")
    # Different host + port + db — same template, same cached schema.
    assert reg.get("jdbc:postgresql://db2.example.com:6543/other") is not None
    # Confirm only ONE template stored.
    assert reg.templates() == ["jdbc:postgresql://{host}:{port}/{db}"]


def test_sqlite_memory_and_file_share_a_template_when_registered(reg):
    reg.register_template("jdbc:sqlite:{path}")
    reg.put("jdbc:sqlite::memory:", _DEMO)
    assert reg.get("jdbc:sqlite:/tmp/x.db") is not None


def test_unregistered_uri_uses_literal_as_template(reg):
    # No register_template() call → URI is its own template.
    reg.put("jdbc:mariadb://x/y", _DEMO)
    assert reg.get("jdbc:mariadb://x/y") is not None
    assert reg.get("jdbc:mariadb://other/z") is None


# --- clear ---------------------------------------------------------------
def test_clear_one_template(reg):
    reg.put("jdbc:sqlite:/tmp/a.db", _DEMO)
    reg.put("jdbc:sqlite:/tmp/b.db", _DEMO)
    reg.clear("jdbc:sqlite:/tmp/a.db")
    assert reg.get("jdbc:sqlite:/tmp/a.db") is None
    assert reg.get("jdbc:sqlite:/tmp/b.db") is not None


def test_clear_all(reg):
    reg.put("jdbc:sqlite:/tmp/a.db", _DEMO)
    reg.put("jdbc:sqlite:/tmp/b.db", _DEMO)
    reg.clear()
    assert reg.templates() == []


# --- registry holds NO row data -----------------------------------------
def test_registry_schema_has_no_row_table(reg):
    # Canary: the DB should only have the four bookkeeping tables.
    conn = reg._conn
    names = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_schema WHERE type='table'"
    ).fetchall()}
    assert names == {"connections", "tables_cache", "columns_cache", "uri_templates"}
