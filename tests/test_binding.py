"""Unit tests for the OpenAPI-operation → ComfyUI-node-spec binding.

These don't need the WireMock facade — they inspect the class objects
produced by the registry (INPUT_TYPES, RETURN_TYPES, RETURN_NAMES).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


# --- pure binding helpers ------------------------------------------------
def test_expand_resolves_ref():
    from comfyui_openapi_node.binding import expand, resolve_ref
    components = {"schemas": {"Foo": {"type": "object",
                                      "properties": {"x": {"type": "integer"}}}}}
    assert resolve_ref("#/components/schemas/Foo", components)["type"] == "object"
    out = expand({"$ref": "#/components/schemas/Foo"}, components)
    assert out["type"] == "object"
    assert out["properties"]["x"]["type"] == "integer"


def test_operation_to_input_types_splits_required_and_optional():
    from comfyui_openapi_node.binding import operation_to_input_types
    op = {
        "parameters": [
            {"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}},
            {"name": "tag", "in": "query",                 "schema": {"type": "string"}},
        ],
        "requestBody": {"content": {"application/json": {"schema": {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name":   {"type": "string"},
                "active": {"type": "boolean"},
            },
        }}}},
    }
    it = operation_to_input_types(op, {})
    assert "id"   in it["required"] and it["required"]["id"][0]   == "INT"
    assert "name" in it["required"] and it["required"]["name"][0] == "STRING"
    assert "tag"    in it["optional"] and it["optional"]["tag"][0]    == "STRING"
    assert "active" in it["optional"] and it["optional"]["active"][0] == "BOOLEAN"


def test_operation_to_input_types_enum_becomes_tuple():
    from comfyui_openapi_node.binding import operation_to_input_types
    op = {"parameters": [{"name": "role", "in": "query", "required": True,
                          "schema": {"enum": ["user", "assistant"]}}]}
    slot = operation_to_input_types(op, {})["required"]["role"]
    assert isinstance(slot, tuple) and isinstance(slot[0], list)
    assert slot[0] == ["user", "assistant"]


def test_operation_to_return_types_prepends_typed_fields():
    from comfyui_openapi_node.binding import operation_to_return_types
    op = {"responses": {"200": {"content": {"application/json": {"schema": {
        "type": "object",
        "properties": {
            "count":  {"type": "integer"},
            "total":  {"type": "number"},
            "name":   {"type": "string"},
            "active": {"type": "boolean"},
        },
    }}}}}}
    rts, rns = operation_to_return_types(op, {})
    assert rts[:4] == ("INT", "FLOAT", "STRING", "BOOLEAN")
    assert rts[-3:] == ("STRING", "STRING", "STRING")
    assert rns[-3:] == ("body", "stats", "headers")
    assert rns[:4] == ("count", "total", "name", "active")


def test_missing_2xx_falls_back_to_canonical_tail():
    from comfyui_openapi_node.binding import operation_to_return_types
    op = {"responses": {"default": {"description": "n/a"}}}
    rts, rns = operation_to_return_types(op, {})
    assert rts == ("STRING", "STRING", "STRING")
    assert rns == ("body", "stats", "headers")


# --- registry / preset ---------------------------------------------------
def test_lm_studio_chat_completions_has_typed_inputs():
    """The auto-generated LM Studio chatCompletions node should expose
    the real parameter set as typed inputs, not a values_json blob."""
    from comfyui_openapi_node import NODE_CLASS_MAPPINGS
    # chatCompletions is one of two ops in api/openapi/spec/lm-studio.yaml
    cls_name = next(
        k for k in NODE_CLASS_MAPPINGS
        if k.startswith("OpenAPI_lm_studio_") and "chat" in k.lower()
    )
    it = NODE_CLASS_MAPPINGS[cls_name].INPUT_TYPES()
    # Body schema has `model` + `messages` as required, others optional.
    req = it.get("required", {})
    assert "model"    in req and req["model"][0]    == "STRING"
    assert "messages" in req  # array → falls through to multiline STRING
    # optional overrides
    opt = it.get("optional", {})
    assert "temperature" in opt and opt["temperature"][0] == "FLOAT"
    assert "max_tokens"  in opt and opt["max_tokens"][0]  == "INT"
    assert "stream"      in opt and opt["stream"][0]      == "BOOLEAN"
    # routing / infra inputs
    assert "server_url" in opt
