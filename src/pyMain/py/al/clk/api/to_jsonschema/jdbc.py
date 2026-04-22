"""JDBC / Spring JdbcTemplate → JSON Schema canonical form.

A relational-DB table is an API surface just like an OpenAPI path —
each column declares its type via JDBC (+ Postgres extensions), each
table exposes a handful of predictable operations:

    select_<table>           → SELECT *
    select_<table>_by_id     → SELECT WHERE pk = ?
    insert_<table>           → INSERT INTO … VALUES …
    update_<table>_by_id     → UPDATE … SET …
    delete_<table>_by_id     → DELETE WHERE pk = ?

Each of those becomes an `OperationSchema` with:

    input_schema  — columns required for the operation
    output_schema — the row object (array of rows for SELECT)

Binding.py fans properties out into ComfyUI slots; the Kotlin JDBC
server (Spring JdbcTemplate) exposes /jdbc/<table>/<op> under Ktor so
the Python executor can reuse the HTTP protocol path.

Table-schema dict shape accepted by this module:

    {
      "name": "users",
      "primary_key": ["id"],
      "columns": [
        {"name": "id",    "sql_type": "BIGINT",  "pg_type": "int8",
         "nullable": False},
        {"name": "email", "sql_type": "VARCHAR", "size": 255,
         "nullable": False},
        {"name": "geom",  "sql_type": "OTHER",   "pg_type": "geometry",
         "geotype": "Point"},
        …
      ]
    }

A GeoJSON-friendly row of the sample above is the Canonical output_schema.
"""
from __future__ import annotations

from typing import Iterable, Mapping

from ..sql_types import column_to_json_schema
from . import Canonical, OperationSchema


def _col_schema(col: Mapping) -> tuple[str, dict]:
    name = col.get("name") or ""
    schema = column_to_json_schema(
        sql_type=str(col.get("sql_type") or "VARCHAR"),
        pg_type=col.get("pg_type"),
        nullable=bool(col.get("nullable", True)),
        size=col.get("size"),
        precision=col.get("precision"),
        scale=col.get("scale"),
        geotype=col.get("geotype"),
        default=col.get("default"),
    )
    return name, schema


def _table_row_schema(table: Mapping) -> dict:
    props = {}
    required = []
    for col in table.get("columns") or []:
        name, schema = _col_schema(col)
        if not name:
            continue
        props[name] = schema
        if not col.get("nullable", True) and col.get("default") is None:
            required.append(name)
    return {"type": "object", "properties": props, "required": required}


def _pk_schema(table: Mapping) -> dict:
    pk = list(table.get("primary_key") or [])
    props = {}
    for col in table.get("columns") or []:
        if col.get("name") in pk:
            _, schema = _col_schema(col)
            props[col["name"]] = schema
    return {"type": "object", "properties": props, "required": pk}


def _list_schema(row_schema: dict) -> dict:
    # grid-friendly output: array of typed rows. The `x-grid` hint
    # nudges ComfyUI UIs that support a tabular widget to render it as
    # a grid of JSON-Schema-driven cells.
    return {
        "type": "array",
        "items": row_schema,
        "x-grid": True,
        "x-items-schema": row_schema,
    }


def convert(tables: Iterable[Mapping] | Mapping) -> Canonical:
    """Build Canonical from one or many table descriptors.

    Accepts either:
      {"tables": [{...}, {...}]}
      [{...}, {...}]
      a single table dict
    """
    if isinstance(tables, Mapping) and "tables" in tables:
        tables = tables["tables"] or []
    elif isinstance(tables, Mapping):
        tables = [tables]

    ops: list[OperationSchema] = []
    for table in tables or []:
        if not isinstance(table, Mapping):
            continue
        t_name = table.get("name") or ""
        if not t_name:
            continue
        row_schema = _table_row_schema(table)
        pk_schema  = _pk_schema(table)
        list_schema = _list_schema(row_schema)

        # SELECT (list) — no required inputs
        ops.append(OperationSchema(
            id=f"select_{t_name}",
            protocol="http",
            verb="GET",
            path=f"/jdbc/{t_name}",
            input_schema={},
            output_schema=list_schema,
            parameters=[],
            security=[],
            raw=dict(table),
        ))
        # SELECT by PK
        if pk_schema.get("required"):
            ops.append(OperationSchema(
                id=f"select_{t_name}_by_id",
                protocol="http",
                verb="GET",
                path=f"/jdbc/{t_name}/{{id}}",
                input_schema=pk_schema,
                output_schema=row_schema,
                parameters=[
                    {"name": k, "in": "path", "required": True,
                     "schema": pk_schema["properties"][k]}
                    for k in pk_schema["required"]
                ],
                security=[],
                raw=dict(table),
            ))
        # INSERT
        ops.append(OperationSchema(
            id=f"insert_{t_name}",
            protocol="http",
            verb="POST",
            path=f"/jdbc/{t_name}",
            input_schema=row_schema,
            output_schema=row_schema,
            parameters=[],
            security=[],
            raw=dict(table),
        ))
        # UPDATE by PK
        if pk_schema.get("required"):
            ops.append(OperationSchema(
                id=f"update_{t_name}_by_id",
                protocol="http",
                verb="PUT",
                path=f"/jdbc/{t_name}/{{id}}",
                input_schema=row_schema,
                output_schema=row_schema,
                parameters=[
                    {"name": k, "in": "path", "required": True,
                     "schema": pk_schema["properties"][k]}
                    for k in pk_schema["required"]
                ],
                security=[],
                raw=dict(table),
            ))
            ops.append(OperationSchema(
                id=f"delete_{t_name}_by_id",
                protocol="http",
                verb="DELETE",
                path=f"/jdbc/{t_name}/{{id}}",
                input_schema=pk_schema,
                output_schema={},
                parameters=[
                    {"name": k, "in": "path", "required": True,
                     "schema": pk_schema["properties"][k]}
                    for k in pk_schema["required"]
                ],
                security=[],
                raw=dict(table),
            ))

    return Canonical(
        title="JDBC",
        version="",
        server_url="",
        components={},
        security_schemes={},
        default_security=[],
        operations=ops,
    )
