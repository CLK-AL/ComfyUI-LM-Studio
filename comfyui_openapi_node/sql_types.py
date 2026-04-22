"""JDBC SQL types (java.sql.Types) and PostgreSQL 18 extensions → JSON Schema.

The goal: any relational-DB table schema we pull through a
ResultSetMetaData (or Spring JdbcTemplate) projection becomes a JSON
Schema object that binding.py + registry.py can consume the same way
they consume OpenAPI operations. The path is:

   column metadata (name, sql_type, nullable, size, geotype, …)
          ↓
   sql_types.column_to_json_schema(...)
          ↓
   JSON Schema property
          ↓
   schema.json_schema_to_comfy → ComfyUI INPUT_TYPES slot

Covers:
  * every java.sql.Types code
  * PostgreSQL 18 type extensions (jsonb, uuid, inet/cidr/macaddr,
    tsvector, ltree, cube, money, bytea)
  * PostGIS geometry / geography (returned as GeoJSON — format='geojson')
"""
from __future__ import annotations

from enum import IntEnum
from typing import Any, Mapping


# --- java.sql.Types ------------------------------------------------------
# IntEnum whose values match JDBC 4.2 numerically — cross-compare with
# the Kotlin `SqlTypes` enum at `api/common/SqlTypes.kt` is literal.
class SqlTypes(IntEnum):
    BIT                      = -7
    TINYINT                  = -6
    SMALLINT                 = 5
    INTEGER                  = 4
    BIGINT                   = -5
    FLOAT                    = 6
    REAL                     = 7
    DOUBLE                   = 8
    NUMERIC                  = 2
    DECIMAL                  = 3
    CHAR                     = 1
    VARCHAR                  = 12
    LONGVARCHAR              = -1
    DATE                     = 91
    TIME                     = 92
    TIMESTAMP                = 93
    TIMESTAMP_WITH_TIMEZONE  = 2014
    TIME_WITH_TIMEZONE       = 2013
    BINARY                   = -2
    VARBINARY                = -3
    LONGVARBINARY            = -4
    NULL                     = 0
    OTHER                    = 1111
    JAVA_OBJECT              = 2000
    BLOB                     = 2004
    CLOB                     = 2005
    NCHAR                    = -15
    NVARCHAR                 = -9
    LONGNVARCHAR             = -16
    NCLOB                    = 2011
    BOOLEAN                  = 16
    ROWID                    = -8
    SQLXML                   = 2009
    REF_CURSOR               = 2012
    ARRAY                    = 2003
    STRUCT                   = 2002
    REF                      = 2006
    DATALINK                 = 70

    @classmethod
    def from_name(cls, name: str) -> "SqlTypes":
        return cls[name.upper()]

    @classmethod
    def from_code(cls, code: int) -> "SqlTypes":
        return cls(code)


# Backwards-compat name lookup: {"BIGINT": -5, …}
SQL_TYPES: dict[str, int] = {m.name: m.value for m in SqlTypes}

# --- JDBC SQL type name → JSON Schema fragment ---------------------------
# Kept minimal but lossless — json_schema_to_comfy expands these into
# ComfyUI options (format, min/max, multiline, placeholder, …).
_STD: dict[str, dict] = {
    # integers
    "BIT":         {"type": "boolean"},
    "BOOLEAN":     {"type": "boolean"},
    "TINYINT":     {"type": "integer", "minimum": -128,   "maximum": 127},
    "SMALLINT":    {"type": "integer", "minimum": -32768, "maximum": 32767},
    "INTEGER":     {"type": "integer", "format":  "int32"},
    "BIGINT":      {"type": "integer", "format":  "int64"},

    # floats / decimals
    "FLOAT":       {"type": "number",  "format":  "float"},
    "REAL":        {"type": "number",  "format":  "float"},
    "DOUBLE":      {"type": "number",  "format":  "double"},
    "NUMERIC":     {"type": "number"},
    "DECIMAL":     {"type": "number"},

    # text
    "CHAR":        {"type": "string"},
    "VARCHAR":     {"type": "string"},
    "LONGVARCHAR": {"type": "string", "x-multiline": True},
    "NCHAR":       {"type": "string"},
    "NVARCHAR":    {"type": "string"},
    "LONGNVARCHAR":{"type": "string", "x-multiline": True},
    "CLOB":        {"type": "string", "x-multiline": True},
    "NCLOB":       {"type": "string", "x-multiline": True},
    "SQLXML":      {"type": "string", "format": "xml"},

    # temporal
    "DATE":                    {"type": "string", "format": "date"},
    "TIME":                    {"type": "string", "format": "time"},
    "TIME_WITH_TIMEZONE":      {"type": "string", "format": "time"},
    "TIMESTAMP":               {"type": "string", "format": "date-time"},
    "TIMESTAMP_WITH_TIMEZONE": {"type": "string", "format": "date-time"},

    # binary
    "BINARY":       {"type": "string", "format": "byte"},
    "VARBINARY":    {"type": "string", "format": "byte"},
    "LONGVARBINARY":{"type": "string", "format": "byte"},
    "BLOB":         {"type": "string", "format": "binary"},

    # special
    "ROWID":        {"type": "string"},
    "ARRAY":        {"type": "array"},
    "STRUCT":       {"type": "object"},
    "REF":          {"type": "string"},
    "REF_CURSOR":   {"type": "array"},
    "DATALINK":     {"type": "string", "format": "uri"},
    "NULL":         {"type": "null"},
    "OTHER":        {"type": "string", "format": "json"},
    "JAVA_OBJECT":  {"type": "string", "format": "json"},
}

# --- PostgreSQL 18 extensions --------------------------------------------
# Everything Postgres exposes that JDBC doesn't model cleanly. Keyed by
# the Postgres `pg_type.typname` lowercase so the driver's reported
# type survives verbatim.
_PG: dict[str, dict] = {
    "bool":        {"type": "boolean"},
    "int2":        {"type": "integer", "minimum": -32768, "maximum": 32767},
    "int4":        {"type": "integer", "format": "int32"},
    "int8":        {"type": "integer", "format": "int64"},
    "float4":      {"type": "number",  "format": "float"},
    "float8":      {"type": "number",  "format": "double"},
    "numeric":     {"type": "number"},
    "money":       {"type": "string", "pattern": r"^[-+]?\d+(\.\d+)?$"},
    "text":        {"type": "string", "x-multiline": True},
    "name":        {"type": "string"},
    "bytea":       {"type": "string", "format": "byte"},
    "uuid":        {"type": "string", "format": "uuid"},

    # network
    "inet":        {"type": "string", "format": "ipv4"},
    "cidr":        {"type": "string", "format": "ipv4"},
    "macaddr":     {"type": "string",
                     "pattern": r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$"},
    "macaddr8":    {"type": "string"},

    # structured
    "json":        {"type": "string", "format": "json"},
    "jsonb":       {"type": "string", "format": "json"},
    "jsonpath":    {"type": "string"},
    "xml":         {"type": "string", "format": "xml"},
    "hstore":      {"type": "string", "format": "json"},

    # full-text
    "tsvector":    {"type": "string"},
    "tsquery":     {"type": "string"},

    # ranges & special
    "ltree":       {"type": "string"},
    "cube":        {"type": "string"},

    # PostGIS — carried as GeoJSON so a single format covers wire + UI.
    "geometry":    {"type": "object", "format": "geojson"},
    "geography":   {"type": "object", "format": "geojson"},
    "box2d":       {"type": "object", "format": "geojson"},
    "box3d":       {"type": "object", "format": "geojson"},
    "raster":      {"type": "string", "format": "byte"},
}


def column_to_json_schema(
    *,
    sql_type: str,
    nullable: bool = True,
    size: int | None = None,
    precision: int | None = None,
    scale: int | None = None,
    pg_type: str | None = None,
    geotype: str | None = None,
    default: Any = None,
) -> dict:
    """Return a JSON Schema fragment for a single column.

    Priority: pg_type (lowercase Postgres typname) → sql_type (JDBC
    standard). geotype, if given, refines geometry columns to a specific
    GeoJSON subtype hint (e.g. "Point", "Polygon").
    """
    base: dict = {}
    if pg_type:
        base = dict(_PG.get(pg_type.lower(), {}))
    if not base:
        base = dict(_STD.get(sql_type.upper(), {"type": "string"}))

    # Carry constraints through.
    if size is not None and base.get("type") == "string":
        base.setdefault("maxLength", size)
    if precision is not None and base.get("type") == "number":
        # Spring-flavoured hint — the UI can render a numeric widget
        # with matching precision even if it doesn't enforce it.
        base["x-precision"] = precision
    if scale is not None and base.get("type") == "number":
        base["x-scale"] = scale
    if geotype and base.get("format") == "geojson":
        base["x-geotype"] = geotype

    if default is not None:
        base["default"] = default
    if not nullable:
        base["x-nullable"] = False
    else:
        base["x-nullable"] = True

    return base
