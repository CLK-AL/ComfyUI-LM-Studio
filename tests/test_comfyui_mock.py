#!/usr/bin/env python3
"""Unit tests for the LMStudioNode (a ComfyUI node is a unit).

The LM Studio server is replaced by the jbang WireMock facade seeded from
the LM Studio OpenAPI. Tests exercise LMStudioNode.get_response in API
mode (use_sdk=False) against the facade.

Run:
    ./run-tests.sh                               # bash launcher, auto venv
    .\run-tests.ps1                              # PowerShell launcher
    pytest tests/test_comfyui_mock.py -q         # direct pytest

The session-scoped `wiremock_base` fixture (conftest.py) auto-bootstraps
SDKMAN + jbang + OpenAPI spec if the server isn't already running; set
SKIP_BOOTSTRAP=1 to require a pre-started mock instead.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


# --- WireMock helpers ----------------------------------------------------
def wm_reset(base: str) -> None:
    # WireMock 3.x: /__admin/reset is the global reset (the 2.x
    # /__admin/requests/reset endpoint 404s here).
    requests.post(f"{base}/__admin/reset", timeout=5).raise_for_status()


def wm_stub(base: str, body, status: int = 200,
            method: str = "POST",
            url_path: str = "/api/v0/chat/completions") -> None:
    mapping = {
        "request": {"method": method, "urlPath": url_path},
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "body": body if isinstance(body, str) else json.dumps(body),
        },
    }
    requests.post(f"{base}/__admin/mappings", json=mapping, timeout=5).raise_for_status()


def wm_seed_default(base: str) -> None:
    wm_stub(base, {
        "choices": [{"message": {"role": "assistant",
                                 "content": "stubbed reply from wiremock-lms"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        "stats": {"tokens_per_second": 10.0},
    })


# --- Fixtures ------------------------------------------------------------
@pytest.fixture
def node():
    sys.path.insert(0, str(REPO))
    from node import LMStudioNode
    return LMStudioNode()


@pytest.fixture
def base(wiremock_base):  # wiremock_base comes from conftest.py
    wm_reset(wiremock_base)
    return wiremock_base


# --- Tests ---------------------------------------------------------------
def _call(node, base_url, **over):
    kw = dict(
        system_prompt="sys", user_message="hi",
        model_id="m1", server_address=base_url,
        temperature=0.7, max_tokens=64,
        thinking_tokens=True, use_sdk=False, image=None, debug=False,
    )
    kw.update(over)
    return node.get_response(**kw)


def test_happy_path(node, base):
    wm_seed_default(base)
    out, stats = _call(node, base)
    assert out == "stubbed reply from wiremock-lms"
    assert "Tokens per Second: 10.00" in stats
    assert "Input Tokens: 4" in stats
    assert "Output Tokens: 6" in stats


def test_thinking_stripped(node, base):
    wm_stub(base, {
        "choices": [{"message": {"content": "<think>secret</think>visible"}}],
        "usage": {}, "stats": {},
    })
    out, _ = _call(node, base, thinking_tokens=False)
    assert out == "visible"


def test_http_500(node, base):
    wm_stub(base, {"error": "boom"}, status=500)
    out, stats = _call(node, base)
    assert out.startswith("Error:")
    assert stats == node.default_stats


def test_connection_refused(node):
    # Port nothing is listening on.
    out, stats = _call(node, "http://127.0.0.1:1")
    assert "Connection error" in out
    assert stats == node.default_stats


def test_request_shape(node, base):
    wm_seed_default(base)
    _call(node, base, system_prompt="SYS", user_message="USR",
          model_id="mX", temperature=0.33)
    r = requests.get(f"{base}/__admin/requests", timeout=5).json()
    reqs = r.get("requests", [])
    assert reqs, "no requests recorded"
    body = json.loads(reqs[0]["request"]["body"])
    assert body["model"] == "mX"
    assert body["temperature"] == 0.33
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user",   "content": "USR"},
    ]


if __name__ == "__main__":
    # CLI entry: delegate to pytest so results match `pytest tests/...`.
    raise SystemExit(pytest.main([__file__, "-q"] + sys.argv[1:]))
