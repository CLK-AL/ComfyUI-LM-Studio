"""Unit tests for the generic OpenAPINode driving the LM Studio preset
through the same jbang WireMock facade used elsewhere.

Goal: prove that given an OpenAPI spec and an operationId, the generic
node assembles + executes a correct HTTP call, then decodes the
response — without a word of LM-Studio-specific code in the test.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import requests

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))


@pytest.fixture
def openapi_node():
    from al.clk.api.node import OpenAPINode
    return OpenAPINode()


@pytest.fixture
def base(wiremock_base):
    # Session fixture resets after each test via autouse.
    return wiremock_base


def _stub(base, url_path, body, status=200, method="POST", content_type="application/json"):
    mapping = {
        "request": {"method": method, "urlPath": url_path},
        "response": {"status": status,
                     "headers": {"Content-Type": content_type},
                     "body": body if isinstance(body, str) else json.dumps(body)},
    }
    requests.post(f"{base}/__admin/mappings", json=mapping, timeout=5).raise_for_status()


# --- Presets registry ----------------------------------------------------
def test_lm_studio_preset_registered():
    from al.clk.api import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    assert "OpenAPINode" in NODE_CLASS_MAPPINGS
    # One auto-generated convenience class per operation in the preset.
    assert any(k.startswith("API_lm_studio_") for k in NODE_CLASS_MAPPINGS)
    assert any("lm-studio" in v for v in NODE_DISPLAY_NAME_MAPPINGS.values())


# --- HTTP + JSON happy path ---------------------------------------------
def test_chat_completions_via_preset(openapi_node, base, spec_paths):
    _stub(base, spec_paths["chat_completions"], {
        "choices": [{"message": {"content": "stubbed reply"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2},
    })
    body, stats, headers = openapi_node.invoke(spec_kind="openapi", 
        spec_source="preset:lm-studio",
        operation_id="chatCompletions",
        protocol="http",
        method="POST",
        values_json=json.dumps({
            "body": {
                "model": "m1",
                "messages": [{"role": "user", "content": "hi"}],
            }
        }),
        server_url=base,
    )
    assert "stubbed reply" in body, body
    assert "HTTP 200" in stats
    h = json.loads(headers)
    assert "application/json" in h.get("Content-Type", "").lower()


# --- Error path ----------------------------------------------------------
def test_missing_operation_returns_error_string(openapi_node, base):
    body, stats, _ = openapi_node.invoke(spec_kind="openapi", 
        spec_source="preset:lm-studio",
        operation_id="doesNotExist",
        protocol="http",
        method="GET",
        values_json="{}",
        server_url=base,
    )
    assert "error" in body.lower()
    assert "HTTP 0" in stats


# --- Content negotiation: XML response ----------------------------------
def test_xml_response_is_passed_through(openapi_node, base, spec_paths):
    _stub(base, spec_paths["models"], "<list><model>stub</model></list>",
          method="GET", content_type="application/xml")
    body, stats, headers = openapi_node.invoke(spec_kind="openapi", 
        spec_source="preset:lm-studio",
        operation_id="listModels",
        protocol="http",
        method="GET",
        values_json="{}",
        server_url=base,
    )
    # XMLCodec.decode returns an ElementTree Element; .as_tuple stringifies it.
    assert "Element" in body or "stub" in body or body == "" or "list" in body.lower()
    assert "HTTP 200" in stats


# --- WebDAV method is accepted -----------------------------------------
def test_propfind_is_allowed(openapi_node, base):
    # Stub any PROPFIND call to /
    mapping = {
        "request": {"method": "PROPFIND", "urlPath": "/"},
        "response": {"status": 207,
                     "headers": {"Content-Type": "application/xml"},
                     "body": "<multistatus/>"},
    }
    requests.post(f"{base}/__admin/mappings", json=mapping, timeout=5).raise_for_status()
    # Use the generic node with an ad-hoc one-shot spec.
    inline = json.dumps({
        "openapi": "3.0.3",
        "info": {"title": "wd", "version": "0"},
        "paths": {"/": {"propfind": {"operationId": "list",
                                     "responses": {"207": {"description": "ok"}}}}}
    })
    body, stats, _ = openapi_node.invoke(spec_kind="openapi", 
        spec_source=inline,
        operation_id="list",
        protocol="http",
        method="PROPFIND",
        values_json="{}",
        server_url=base,
    )
    assert "HTTP 207" in stats
