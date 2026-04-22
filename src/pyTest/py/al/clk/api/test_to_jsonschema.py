"""Protocol-neutral conversion: every spec kind → canonical JSON Schema →
ComfyUI via binding.py. Today we exercise the OpenAPI converter fully
and smoke-test the AsyncAPI / MCP scaffolds.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))


# --- OpenAPI ------------------------------------------------------------
def test_openapi_converter_emits_operations_with_schemas():
    from al.clk.api.to_jsonschema import openapi as oas
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "1"},
        "servers": [{"url": "http://h"}],
        "components": {"schemas": {"Foo": {"type": "object",
                                           "properties": {"x": {"type": "integer"}}}}},
        "paths": {
            "/things/{id}": {
                "get": {
                    "operationId": "getThing",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True,
                         "schema": {"type": "integer"}},
                    ],
                    "responses": {"200": {"content": {"application/json": {
                        "schema": {"$ref": "#/components/schemas/Foo"}
                    }}}},
                },
                "post": {
                    "operationId": "createThing",
                    "requestBody": {"content": {"application/json": {
                        "schema": {"type": "object",
                                   "required": ["name"],
                                   "properties": {"name": {"type": "string"}}}
                    }}},
                    "responses": {"201": {}},
                },
            },
        },
    }
    canon = oas.convert(spec)
    assert canon["title"] == "t"
    assert canon["server_url"] == "http://h"
    ops = {op["id"]: op for op in canon["operations"]}
    assert set(ops) == {"getThing", "createThing"}
    assert ops["getThing"]["verb"] == "GET"
    assert ops["getThing"]["path"] == "/things/{id}"
    assert ops["createThing"]["input_schema"]["properties"]["name"]["type"] == "string"
    # $ref survives into output_schema (binding.py resolves it later).
    assert "$ref" in ops["getThing"]["output_schema"] or \
           ops["getThing"]["output_schema"].get("type") == "object"


def test_openapi_converter_then_binding_produces_comfy_spec():
    from al.clk.api.to_jsonschema import openapi as oas
    from al.clk.api.binding import (
        operation_to_input_types,
        operation_to_return_types,
    )
    spec = {
        "openapi": "3.0.3",
        "info": {"title": "t", "version": "0"},
        "paths": {"/x": {"post": {
            "operationId": "x",
            "requestBody": {"content": {"application/json": {"schema": {
                "type": "object",
                "required": ["n"],
                "properties": {"n": {"type": "integer"}, "m": {"type": "string"}}
            }}}},
            "responses": {"200": {"content": {"application/json": {"schema": {
                "type": "object",
                "properties": {"ok": {"type": "boolean"}}
            }}}}}
        }}},
    }
    canon = oas.convert(spec)
    op = canon["operations"][0]["raw"]
    it = operation_to_input_types(op, canon.get("components") or {})
    rts, rns = operation_to_return_types(op, canon.get("components") or {})
    assert it["required"]["n"][0] == "INT"
    assert it["optional"]["m"][0] == "STRING"
    assert rts[0] == "BOOLEAN" and rns[0] == "ok"
    assert rns[-3:] == ("body", "stats", "headers")


# --- AsyncAPI -----------------------------------------------------------
def test_asyncapi_converter_smoke():
    from al.clk.api.to_jsonschema import asyncapi as aas
    spec = {
        "asyncapi": "2.6.0",
        "info": {"title": "chat", "version": "1"},
        "servers": {"prod": {"url": "ws://h"}},
        "channels": {
            "rooms.{id}.messages": {
                "publish": {"operationId": "sendMessage",
                            "message": {"payload": {"type": "object",
                                                    "properties": {"text": {"type": "string"}}}}},
                "subscribe": {"operationId": "onMessage",
                              "message": {"payload": {"type": "object",
                                                      "properties": {"text": {"type": "string"}}}}},
            }
        },
    }
    canon = aas.convert(spec)
    assert canon["server_url"] == "ws://h"
    ids = sorted(op["id"] for op in canon["operations"])
    assert ids == ["onMessage", "sendMessage"]
    send = next(o for o in canon["operations"] if o["id"] == "sendMessage")
    assert send["input_schema"]["properties"]["text"]["type"] == "string"
    assert send["output_schema"] == {}
    assert send["protocol"] == "ws"


# --- MCP ---------------------------------------------------------------
def test_mcp_converter_smoke():
    from al.clk.api.to_jsonschema import mcp
    tools = [
        {"name": "echo",
         "description": "",
         "inputSchema":  {"type": "object",
                          "required": ["text"],
                          "properties": {"text": {"type": "string"}}},
         "outputSchema": {"type": "object",
                          "properties": {"text": {"type": "string"}}}},
    ]
    canon = mcp.convert(tools)
    assert canon["operations"][0]["id"] == "echo"
    assert canon["operations"][0]["protocol"] == "mcp"
    assert canon["operations"][0]["input_schema"]["required"] == ["text"]
