"""WireMock-backed tests for LMStudioNode._get_response_api.

Run:
    docker run --rm -d -p 8089:8080 --name wiremock wiremock/wiremock:3.9.1
    pytest tests/ -q

These tests force the API path by passing use_sdk=False.
"""
import json
import os
import sys

import pytest
import requests
from wiremock.client import Mapping, Mappings, MappingRequest, MappingResponse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CHAT_PATH = "/api/v0/chat/completions"


def _stub(response_body, status=200, fixed_delay_ms=None):
    resp = MappingResponse(
        status=status,
        headers={"Content-Type": "application/json"},
        body=json.dumps(response_body),
    )
    if fixed_delay_ms is not None:
        resp.fixed_delay_milliseconds = fixed_delay_ms
    mapping = Mapping(
        request=MappingRequest(method="POST", url=CHAT_PATH),
        response=resp,
        persistent=False,
    )
    Mappings.create_mapping(mapping=mapping)


def _get_recorded_requests(wiremock_base):
    r = requests.get(f"{wiremock_base}/__admin/requests", timeout=5)
    r.raise_for_status()
    return r.json().get("requests", [])


def _call_api(node, server_address, **overrides):
    kwargs = dict(
        system_prompt="sys",
        user_message="hi",
        model_id="test-model",
        server_address=server_address,
        temperature=0.5,
        max_tokens=128,
        thinking_tokens=True,
        use_sdk=False,
        image=None,
        debug=False,
    )
    kwargs.update(overrides)
    return node.get_response(**kwargs)


# --- Case 1 ---------------------------------------------------------------
def test_happy_path(node, server_address):
    _stub({
        "choices": [{"message": {"content": "hello there"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 2},
        "stats": {"tokens_per_second": 12.5},
    })
    out, stats = _call_api(node, server_address)
    assert out == "hello there"
    assert "Tokens per Second: 12.50" in stats
    assert "Input Tokens: 4" in stats
    assert "Output Tokens: 2" in stats


# --- Case 2 ---------------------------------------------------------------
def test_strips_thinking_tokens(node, server_address):
    _stub({
        "choices": [{"message": {"content": "<think>secret</think>visible"}}],
        "usage": {}, "stats": {},
    })
    out, _ = _call_api(node, server_address, thinking_tokens=False)
    assert out == "visible"


# --- Case 3 ---------------------------------------------------------------
def test_keeps_thinking_tokens(node, server_address):
    body = "<think>secret</think>visible"
    _stub({
        "choices": [{"message": {"content": body}}],
        "usage": {}, "stats": {},
    })
    out, _ = _call_api(node, server_address, thinking_tokens=True)
    assert out == body


# --- Case 4 ---------------------------------------------------------------
def test_missing_usage_and_stats(node, server_address):
    _stub({"choices": [{"message": {"content": "ok"}}]})
    out, stats = _call_api(node, server_address)
    assert out == "ok"
    assert "Tokens per Second: 0.00" in stats
    assert "Input Tokens: 0" in stats
    assert "Output Tokens: 0" in stats


# --- Case 5 ---------------------------------------------------------------
def test_malformed_choices(node, server_address):
    _stub({})
    out, stats = _call_api(node, server_address)
    assert out.startswith("Error:")
    assert stats == node.default_stats


# --- Case 6 ---------------------------------------------------------------
def test_http_500(node, server_address):
    _stub({"error": "boom"}, status=500)
    out, stats = _call_api(node, server_address)
    assert out.startswith("Error:")
    assert stats == node.default_stats


# --- Case 7 ---------------------------------------------------------------
def test_connection_refused(node):
    # A port nothing is listening on.
    bad = "http://127.0.0.1:1"
    out, stats = _call_api(node, bad)
    assert "Connection error" in out
    assert stats == node.default_stats


# --- Case 8 ---------------------------------------------------------------
@pytest.mark.slow
def test_timeout(node, server_address, monkeypatch):
    # Patch requests.post to raise Timeout so we don't wait 120s.
    import node as node_module
    real_post = node_module.requests.post

    def fake_post(*a, **kw):
        raise requests.Timeout("simulated")

    monkeypatch.setattr(node_module.requests, "post", fake_post)
    out, stats = _call_api(node, server_address)
    assert "timed out" in out.lower()
    assert stats == node.default_stats
    monkeypatch.setattr(node_module.requests, "post", real_post)


# --- Case 9 ---------------------------------------------------------------
def test_request_shape(node, server_address):
    _stub({"choices": [{"message": {"content": "x"}}], "usage": {}, "stats": {}})
    _call_api(
        node, server_address,
        system_prompt="SYS", user_message="USR",
        model_id="m1", temperature=0.33,
    )
    reqs = _get_recorded_requests(server_address)
    assert len(reqs) == 1
    body = json.loads(reqs[0]["request"]["body"])
    assert body["model"] == "m1"
    assert body["temperature"] == 0.33
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user",   "content": "USR"},
    ]


# --- Case 10 --------------------------------------------------------------
def test_content_type_header(node, server_address):
    _stub({"choices": [{"message": {"content": "x"}}], "usage": {}, "stats": {}})
    _call_api(node, server_address)
    reqs = _get_recorded_requests(server_address)
    headers = reqs[0]["request"]["headers"]
    assert headers.get("Content-Type", "").startswith("application/json")


# --- Case 12 (pinning known bug) -----------------------------------------
@pytest.mark.xfail(reason="max_tokens is not forwarded in API mode (known bug)")
def test_max_tokens_forwarded(node, server_address):
    _stub({"choices": [{"message": {"content": "x"}}], "usage": {}, "stats": {}})
    _call_api(node, server_address, max_tokens=77)
    reqs = _get_recorded_requests(server_address)
    body = json.loads(reqs[0]["request"]["body"])
    assert body.get("max_tokens") == 77
