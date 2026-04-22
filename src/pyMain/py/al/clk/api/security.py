"""Apply OpenAPI / AsyncAPI security schemes to an outgoing request.

Covers the schemes users reach for first:
    apiKey (header / query / cookie)
    http bearer
    http basic
    oauth2 — client_credentials grant (token fetched on demand)
    openIdConnect — stub that points at OIDC discovery; wire to oauth2

Every scheme entry matches OpenAPI 3.x's `components.securitySchemes.*`
shape; AsyncAPI 2.x uses the same keys. Credentials come in a dict
that names the scheme variant — see each branch for expected keys.

Public helpers:
  apply(req_kwargs, scheme, credentials)     — mutate kwargs for requests
  enumerate_schemes(spec)                    — {name: scheme_def}
  schemes_for_operation(op, spec)            — [(name, scheme_def)]
"""
from __future__ import annotations

import base64
import time
from typing import Any, Iterable, Mapping

import requests

# Cache: (token_url, client_id, scope) -> (access_token, expiry_epoch)
_TOKEN_CACHE: dict[tuple[str, str, str], tuple[str, float]] = {}


def enumerate_schemes(spec: Mapping) -> dict[str, dict]:
    """Return {name: scheme_def} from the spec's components.securitySchemes."""
    comps = spec.get("components") or {}
    schemes = comps.get("securitySchemes") or {}
    out: dict[str, dict] = {}
    for name, entry in schemes.items():
        if isinstance(entry, Mapping):
            out[name] = dict(entry)
    return out


def schemes_for_operation(op: Mapping, spec: Mapping) -> list[tuple[str, dict]]:
    """Return the schemes that apply to this operation.

    Per OpenAPI 3.x: operation-level `security` overrides top-level
    `security`. Each list entry is a dict `{schemeName: [scopes]}`; we
    flatten to the set of scheme names mentioned and return
    `(name, scheme_def)` pairs.
    """
    requirements = op.get("security")
    if requirements is None:
        requirements = spec.get("security") or []
    names: list[str] = []
    for req in requirements or []:
        if isinstance(req, Mapping):
            for name in req.keys():
                if name not in names:
                    names.append(name)
    defs = enumerate_schemes(spec)
    return [(n, defs[n]) for n in names if n in defs]


def _fetch_oauth2_token(scheme: Mapping, credentials: Mapping) -> str:
    flows = scheme.get("flows") or {}
    # Client-credentials is the easiest to implement; OIDC / auth-code
    # / device require user interaction and belong in a separate flow.
    cc = flows.get("clientCredentials") or {}
    token_url = credentials.get("tokenUrl") or cc.get("tokenUrl")
    if not token_url:
        raise RuntimeError(
            "oauth2 clientCredentials needs a tokenUrl — provide one via "
            "credentials['tokenUrl'] or in the spec's flows.clientCredentials.tokenUrl"
        )
    client_id     = credentials.get("client_id", "")
    client_secret = credentials.get("client_secret", "")
    scope         = credentials.get("scope", "") or " ".join((cc.get("scopes") or {}).keys())
    key = (token_url, client_id, scope)
    cached = _TOKEN_CACHE.get(key)
    if cached and cached[1] > time.time() + 10:
        return cached[0]
    r = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
        timeout=15,
    )
    r.raise_for_status()
    body = r.json()
    token = body.get("access_token")
    if not token:
        raise RuntimeError(f"oauth2 token endpoint returned no access_token: {body}")
    expires_in = float(body.get("expires_in", 3600))
    _TOKEN_CACHE[key] = (token, time.time() + expires_in)
    return token


def apply(req_kwargs: dict, scheme: Mapping[str, Any],
          credentials: Mapping[str, Any]) -> dict:
    """Mutate and return `req_kwargs` (kwargs passed to requests.request)."""
    t = (scheme.get("type") or "").lower()
    headers = req_kwargs.setdefault("headers", {})
    params  = req_kwargs.setdefault("params", {})

    if t == "apikey":
        name  = scheme.get("name", "Authorization")
        where = (scheme.get("in") or "header").lower()
        value = credentials.get("apiKey") or credentials.get("value") or ""
        if not value:
            return req_kwargs
        if where == "header":
            headers[name] = value
        elif where == "query":
            params[name] = value
        elif where == "cookie":
            req_kwargs.setdefault("cookies", {})[name] = value
        return req_kwargs

    if t == "http":
        scheme_name = (scheme.get("scheme") or "").lower()
        if scheme_name == "bearer":
            token = credentials.get("token") or credentials.get("value") or ""
            if token:
                headers["Authorization"] = f"Bearer {token}"
        elif scheme_name == "basic":
            user = credentials.get("username", "")
            pw   = credentials.get("password", "")
            blob = base64.b64encode(f"{user}:{pw}".encode()).decode()
            headers["Authorization"] = f"Basic {blob}"
        return req_kwargs

    if t == "oauth2":
        # Short-circuit if the caller already resolved a token.
        token = credentials.get("token") or credentials.get("access_token")
        if not token:
            token = _fetch_oauth2_token(scheme, credentials)
        headers["Authorization"] = f"Bearer {token}"
        return req_kwargs

    if t == "openidconnect":
        # OIDC discovery → use a token passed in directly. Full
        # authorization-code flow is still out of scope.
        token = credentials.get("token") or credentials.get("id_token")
        if not token:
            raise NotImplementedError(
                "openIdConnect requires a pre-obtained token (credentials['token']). "
                "Full discovery + auth-code flow is not yet implemented."
            )
        headers["Authorization"] = f"Bearer {token}"
        return req_kwargs

    return req_kwargs


def clear_token_cache() -> None:
    """Forget cached OAuth2 tokens (mostly for tests)."""
    _TOKEN_CACHE.clear()
