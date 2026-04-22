"""Apply OpenAPI security schemes to an outgoing HTTP request.

Covers the three schemes users reach for first (apiKey, http bearer,
http basic). OAuth2 is stubbed with a clear error so nodes relying on
it fail loudly instead of silently sending unauthenticated requests.
"""
from __future__ import annotations

import base64
from typing import Any, Mapping


def apply(req_kwargs: dict, scheme: Mapping[str, Any], credentials: Mapping[str, Any]) -> dict:
    """Mutate and return `req_kwargs` (kwargs passed to requests.request).

    `scheme` is a single entry from the spec's `components.securitySchemes`;
    `credentials` is whatever the user supplied (token/apikey/user+pass).
    """
    t = scheme.get("type", "").lower()
    headers = req_kwargs.setdefault("headers", {})
    params  = req_kwargs.setdefault("params", {})

    if t == "apikey":
        name = scheme.get("name", "Authorization")
        where = scheme.get("in", "header").lower()
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
        scheme_name = scheme.get("scheme", "").lower()
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
        raise NotImplementedError(
            "OAuth2 flows are not yet implemented. "
            "Pass a pre-obtained access token via an apiKey or http-bearer scheme."
        )
    if t == "openidconnect":
        raise NotImplementedError("openIdConnect is not yet implemented.")

    return req_kwargs
