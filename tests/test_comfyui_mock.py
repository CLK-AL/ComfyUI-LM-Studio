#!/usr/bin/env python3
"""Unit tests for the LMStudioNode (a ComfyUI node is a unit).

The LM Studio server is replaced by the jbang WireMock facade seeded from
the LM Studio OpenAPI. Tests exercise LMStudioNode.get_response in API
mode (use_sdk=False) against the facade.

Run:
    ./run-tests.sh                               # bash launcher, auto venv
    .\\run-tests.ps1                             # PowerShell launcher
    pytest tests/test_comfyui_mock.py -q         # direct pytest

The session-scoped `wiremock_base` fixture (conftest.py) auto-bootstraps
SDKMAN + jbang + OpenAPI spec if the server isn't already running; set
SKIP_BOOTSTRAP=1 to require a pre-started mock instead.

Assertions are intentionally loose about:
  * return arity (2-tuple today, 3-tuple post-upstream-PR#1)
  * error prefix ("Error:" today, "API Error:" in the PR)
  * endpoint path (read from the OpenAPI spec, not hardcoded)
so that future upstream renames don't break the suite.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


# --- Small helpers -------------------------------------------------------
def _unpack(res):
    """Return (out, stats) regardless of get_response's tuple arity."""
    assert isinstance(res, tuple), f"expected tuple, got {type(res).__name__}"
    assert len(res) in (2, 3), f"expected 2 or 3 values, got {len(res)}"
    return res[0], res[1]


def _has_error(text: str) -> bool:
    return "error" in text.lower()


# --- WireMock helpers (endpoint path comes from the OpenAPI spec) --------
def wm_reset(base: str) -> None:
    requests.post(f"{base}/__admin/reset", timeout=5).raise_for_status()


def wm_stub(base: str, body, *, status: int = 200,
            method: str = "POST",
            url_path: str) -> None:
    mapping = {
        "request": {"method": method, "urlPath": url_path},
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "body": body if isinstance(body, str) else json.dumps(body),
        },
    }
    requests.post(f"{base}/__admin/mappings", json=mapping, timeout=5).raise_for_status()


def wm_seed_default(base: str, chat_path: str) -> None:
    wm_stub(base, {
        "choices": [{"message": {"role": "assistant",
                                 "content": "stubbed reply from wiremock-lms"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        "stats": {"tokens_per_second": 10.0},
    }, url_path=chat_path)


# --- Fixtures ------------------------------------------------------------
@pytest.fixture
def node():
    sys.path.insert(0, str(REPO))
    from node import LMStudioNode
    return LMStudioNode()


@pytest.fixture
def base(wiremock_base):
    wm_reset(wiremock_base)
    return wiremock_base


@pytest.fixture
def chat_path(spec_paths):
    return spec_paths["chat_completions"]


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


def test_happy_path(node, base, chat_path):
    wm_seed_default(base, chat_path)
    out, stats = _unpack(_call(node, base))
    assert out == "stubbed reply from wiremock-lms"
    assert "Tokens per Second" in stats
    assert "Input Tokens: 4" in stats
    assert "Output Tokens: 6" in stats


def test_thinking_stripped(node, base, chat_path):
    wm_stub(base, {
        "choices": [{"message": {"content": "<think>secret</think>visible"}}],
        "usage": {}, "stats": {},
    }, url_path=chat_path)
    out, _ = _unpack(_call(node, base, thinking_tokens=False))
    assert out == "visible"


def test_http_500(node, base, chat_path):
    wm_stub(base, {"error": "boom"}, status=500, url_path=chat_path)
    out, stats = _unpack(_call(node, base))
    assert _has_error(out), f"expected error marker, got {out!r}"
    assert stats == node.default_stats


def test_connection_refused(node):
    # Port nothing is listening on. Message wording differs between the
    # 'Connection error' path (current) and 'API Error: …' (upstream PR),
    # but both carry 'Error' somewhere.
    out, stats = _unpack(_call(node, "http://127.0.0.1:1"))
    assert _has_error(out), f"expected error marker, got {out!r}"
    assert stats == node.default_stats


def test_request_shape(node, base, chat_path):
    wm_seed_default(base, chat_path)
    _call(node, base, system_prompt="SYS", user_message="USR",
          model_id="mX", temperature=0.33)
    r = requests.get(f"{base}/__admin/requests", timeout=5).json()
    chat_reqs = [
        rq for rq in r.get("requests", [])
        if rq["request"]["url"].endswith(chat_path)
    ]
    assert chat_reqs, f"no request recorded for {chat_path}"
    body = json.loads(chat_reqs[0]["request"]["body"])
    assert body["model"] == "mX"
    assert body["temperature"] == 0.33
    assert body["stream"] is False
    # user_message may arrive as plain string (current) or as a content
    # array with a text part (upstream PR, to support image_url entries).
    msgs = body["messages"]
    assert msgs[0] == {"role": "system", "content": "SYS"}
    user = msgs[1]
    assert user["role"] == "user"
    if isinstance(user["content"], str):
        assert user["content"] == "USR"
    else:
        texts = [p["text"] for p in user["content"] if p.get("type") == "text"]
        assert "USR" in texts


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"] + sys.argv[1:]))
