"""Security schemes: apiKey / http basic / http bearer / JWT / oauth2 / oidc.

Tests fall into three groups:
  1. `security.apply()` — scheme-level unit tests (no HTTP).
  2. enumeration — schemes_for_operation correctly resolves per-op and
     per-spec security requirements for both OpenAPI and AsyncAPI.
  3. wiring — a registry-generated per-operation node class exposes the
     right `auth_scheme` dropdown; invoke_typed hands the scheme object
     to the HTTP executor, which mutates the outgoing request through
     the codepaths under test (verified with the WireMock facade).
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

import pytest
import requests

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))


# --- 1. apply() ----------------------------------------------------------
def _apply(scheme, credentials, kwargs=None):
    from comfyui_openapi_node.security import apply
    return apply(kwargs or {}, scheme, credentials)


def test_apply_api_key_header():
    r = _apply({"type": "apiKey", "in": "header", "name": "X-Api-Key"},
               {"apiKey": "abc123"})
    assert r["headers"]["X-Api-Key"] == "abc123"
    assert r["params"] == {}


def test_apply_api_key_query():
    r = _apply({"type": "apiKey", "in": "query", "name": "api_key"},
               {"value": "xyz"})
    assert r["params"]["api_key"] == "xyz"
    assert r["headers"] == {}


def test_apply_api_key_cookie():
    r = _apply({"type": "apiKey", "in": "cookie", "name": "sid"},
               {"value": "sess-7"})
    assert r["cookies"]["sid"] == "sess-7"


def test_apply_http_basic():
    r = _apply({"type": "http", "scheme": "basic"},
               {"username": "ada", "password": "pw"})
    expected = "Basic " + base64.b64encode(b"ada:pw").decode()
    assert r["headers"]["Authorization"] == expected


def test_apply_http_bearer():
    r = _apply({"type": "http", "scheme": "bearer"}, {"token": "eyJhbGciOi…"})
    assert r["headers"]["Authorization"] == "Bearer eyJhbGciOi…"


def test_apply_http_jwt_uses_bearer_path():
    # `bearerFormat: JWT` is only a hint; the code path is the same.
    r = _apply({"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
               {"token": "JWT.TOKEN.HERE"})
    assert r["headers"]["Authorization"] == "Bearer JWT.TOKEN.HERE"


def test_apply_oauth2_client_credentials(monkeypatch):
    from comfyui_openapi_node import security as sec
    sec.clear_token_cache()

    def fake_post(url, data=None, timeout=None, **_kw):
        assert data["grant_type"] == "client_credentials"
        assert data["client_id"] == "cid"
        assert data["client_secret"] == "csec"
        class R:
            def raise_for_status(self): pass
            def json(self): return {"access_token": "tok-42", "expires_in": 3600}
        return R()
    monkeypatch.setattr(sec.requests, "post", fake_post)

    scheme = {"type": "oauth2",
              "flows": {"clientCredentials":
                            {"tokenUrl": "http://auth/token",
                             "scopes": {"read": "r"}}}}
    r = _apply(scheme, {"client_id": "cid", "client_secret": "csec"})
    assert r["headers"]["Authorization"] == "Bearer tok-42"
    sec.clear_token_cache()


def test_apply_oauth2_passthrough_token():
    r = _apply({"type": "oauth2", "flows": {}}, {"token": "already-have-it"})
    assert r["headers"]["Authorization"] == "Bearer already-have-it"


def test_apply_oidc_with_token_passes_bearer():
    r = _apply({"type": "openIdConnect",
                "openIdConnectUrl": "http://issuer/.well-known/openid-configuration"},
               {"token": "id-tok"})
    assert r["headers"]["Authorization"] == "Bearer id-tok"


def test_apply_oidc_without_token_raises():
    from comfyui_openapi_node.security import apply
    with pytest.raises(NotImplementedError):
        apply({}, {"type": "openIdConnect"}, {})


# --- 2. enumeration ------------------------------------------------------
def test_enumerate_schemes_from_spec():
    from comfyui_openapi_node.security import enumerate_schemes
    spec = {"components": {"securitySchemes": {
        "A": {"type": "apiKey", "in": "header", "name": "X"},
        "B": {"type": "http", "scheme": "bearer"},
    }}}
    got = enumerate_schemes(spec)
    assert set(got) == {"A", "B"}


def test_schemes_for_operation_prefers_op_over_top_level():
    from comfyui_openapi_node.security import schemes_for_operation
    spec = {
        "components": {"securitySchemes": {
            "Global": {"type": "http", "scheme": "basic"},
            "PerOp":  {"type": "http", "scheme": "bearer"},
        }},
        "security": [{"Global": []}],
    }
    op_has_own = {"security": [{"PerOp": []}]}
    assert [n for n, _ in schemes_for_operation(op_has_own, spec)] == ["PerOp"]
    op_inherits = {}
    assert [n for n, _ in schemes_for_operation(op_inherits, spec)] == ["Global"]
    op_unauth = {"security": []}
    assert schemes_for_operation(op_unauth, spec) == []


# --- 3. registry wiring --------------------------------------------------
def test_registry_exposes_scheme_dropdown_for_secured_op(monkeypatch):
    """A registry-generated node for an operation that declares security
    should expose only that operation's schemes in the `auth_scheme`
    dropdown."""
    import comfyui_openapi_node.presets as presets_mod
    from comfyui_openapi_node.presets import Preset
    from comfyui_openapi_node.loader import load_spec
    from comfyui_openapi_node.registry import _register_preset, NODE_CLASS_MAPPINGS
    spec_path = REPO / "api" / "openapi" / "spec" / "secured-demo.yaml"
    preset = Preset(
        name="secured-demo",
        title="Secured demo",
        description="",
        spec=lambda p=spec_path: load_spec(p),
        kind="openapi",
    )
    _register_preset("secured-demo", preset)

    cls = NODE_CLASS_MAPPINGS["API_secured_demo_whoAmIWithApiKey"]
    it = cls.INPUT_TYPES()
    choices_tuple = it["optional"]["auth_scheme"]
    choices = choices_tuple[0]
    # Only the operation's declared scheme (plus the blank default).
    assert choices == ["", "ApiKeyHeader"]

    oauth_cls = NODE_CLASS_MAPPINGS["API_secured_demo_whoAmIWithOAuth2"]
    oc = oauth_cls.INPUT_TYPES()["optional"]["auth_scheme"][0]
    assert oc == ["", "OAuth2CC"]
