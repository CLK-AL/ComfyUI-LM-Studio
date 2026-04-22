"""JDBC schema → Canonical → ComfyUI — full round trip.

Exercises the sample-tables preset end-to-end: every SQL type (standard
java.sql.Types + PostgreSQL 18 + PostGIS) must project into a ComfyUI
input slot with the right base type and format hint.
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml  # pyyaml available via run-tests.sh

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))


def _load_sample():
    path = REPO / "api" / "jdbc" / "spec" / "sample-tables.yaml"
    return yaml.safe_load(path.read_text())


# --- sql_types.column_to_json_schema ------------------------------------
def test_column_bigint_is_integer_int64():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="BIGINT", nullable=False)
    assert s["type"] == "integer"
    assert s["format"] == "int64"


def test_column_varchar_with_size_has_maxlength():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="VARCHAR", size=128, nullable=True)
    assert s["type"] == "string" and s["maxLength"] == 128


def test_column_timestamptz_maps_to_date_time():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="TIMESTAMP_WITH_TIMEZONE", nullable=False)
    assert s["type"] == "string" and s["format"] == "date-time"


def test_column_pg_jsonb_maps_to_json():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="OTHER", pg_type="jsonb")
    assert s["format"] == "json"


def test_column_pg_uuid_is_uuid_format():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="VARCHAR", pg_type="uuid")
    assert s["type"] == "string" and s["format"] == "uuid"


def test_column_postgis_geometry_is_geojson():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="OTHER", pg_type="geometry",
                              geotype="Point")
    assert s["type"] == "object"
    assert s["format"] == "geojson"
    assert s["x-geotype"] == "Point"


def test_column_inet_is_ipv4_format():
    from al.clk.api.sql_types import column_to_json_schema
    s = column_to_json_schema(sql_type="VARCHAR", pg_type="inet")
    assert s["format"] == "ipv4"


# --- Canonical emission -------------------------------------------------
def test_sample_tables_produce_crud_operations_per_table():
    from al.clk.api.to_jsonschema import jdbc
    canon = jdbc.convert(_load_sample())
    op_ids = {op["id"] for op in canon["operations"]}
    # users (pk=id): select, select_by_id, insert, update_by_id, delete_by_id
    for base in ("users", "places"):
        assert f"select_{base}"           in op_ids
        assert f"select_{base}_by_id"     in op_ids
        assert f"insert_{base}"           in op_ids
        assert f"update_{base}_by_id"     in op_ids
        assert f"delete_{base}_by_id"     in op_ids


def test_select_output_schema_is_grid_array_of_row_objects():
    from al.clk.api.to_jsonschema import jdbc
    canon = jdbc.convert(_load_sample())
    op = next(o for o in canon["operations"] if o["id"] == "select_places")
    out = op["output_schema"]
    assert out["type"] == "array"
    assert out.get("x-grid") is True
    row_props = out["items"]["properties"]
    # PostGIS columns surface as GeoJSON objects.
    assert row_props["point"]["format"] == "geojson"
    assert row_props["region"]["format"] == "geojson"
    assert row_props["props"]["format"] == "json"


# --- Registry integration -----------------------------------------------
def test_sample_tables_preset_registers_typed_nodes():
    from al.clk.api import NODE_CLASS_MAPPINGS
    keys = [k for k in NODE_CLASS_MAPPINGS if k.startswith("API_sample_tables_")]
    assert keys, "no sample-tables classes registered"
    # Pick insert_users — it should expose email / display / active / etc
    # as typed inputs.
    cls = NODE_CLASS_MAPPINGS["API_sample_tables_insert_users"]
    it = cls.INPUT_TYPES()
    # Required (non-null + no default)
    assert "email"     in it["required"]
    assert it["required"]["email"][0] == "STRING"
    assert it["required"]["email"][1].get("max_length") == 255
    # `active` has a default=true, so it's optional.
    assert "active" in it["optional"]
    assert it["optional"]["active"][0] == "BOOLEAN"


def test_places_insert_has_geojson_inputs():
    from al.clk.api import NODE_CLASS_MAPPINGS
    cls = NODE_CLASS_MAPPINGS["API_sample_tables_insert_places"]
    it = cls.INPUT_TYPES()
    req = it["required"]
    opt = it["optional"]
    # point is non-null → required; bounds/region nullable → optional.
    assert "point" in req and req["point"][1].get("format") == "geojson"
    assert "bounds" in opt and opt["bounds"][1].get("format") == "geojson"
    assert "region" in opt and opt["region"][1].get("format") == "geojson"
    assert opt["props"][1]["format"] == "json"
