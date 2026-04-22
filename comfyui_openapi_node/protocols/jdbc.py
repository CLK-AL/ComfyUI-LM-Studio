"""JDBC executor — delegates to the Kotlin Spring JdbcTemplate server.

The Python side doesn't open a JDBC connection directly; it calls
`jbang api/api.mock.jbang.kt jdbc serve` (Spring + HikariCP + PostGIS)
and sends REST calls to it. That's how we get a clean Python path + a
real JDBC connection without pinning a Python DB driver per backend.

Security options accepted through `credentials`:
  username          — JDBC user. Can be a URI-template token that
                      carries further auth (e.g. `apikey:<key>`).
  password          — any of:
                         • plain password
                         • bearer access-token (for DBs that accept it
                           as password, e.g. Cloud SQL IAM)
                         • JWT — full signed token, or
                         • JWT claim secret — value to sign a JWT with;
                           the Kotlin side mints the token from the
                           `username` claim and the `audience` option.
  auth_type         — basic | bearer | jwt | oauth2 | passthrough
  audience          — JWT / OAuth2 audience
  scope             — OAuth2 scope list (space-separated)
  token_url         — OAuth2 client_credentials token endpoint
  client_id, client_secret — OAuth2 client credentials

All of those are forwarded to the Kotlin side as-is; the Ktor endpoint
re-hydrates the proper driver-specific connection string from them.
"""
from __future__ import annotations

import json

import requests

from . import Response


def execute(
    operation: dict,
    method: str,
    server_url: str,
    path: str,
    values: dict,
    *,
    auth_scheme: dict | None = None,
    credentials: dict | None = None,
    file_path: str | None = None,
    timeout_s: float = 60.0,
    **_ignored,
) -> Response:
    """Invoke a JDBC operation over the Spring-facade REST bridge.

    `operation.raw` carries the table descriptor; the jbang server
    picks the right SQL statement by inspecting the URL path
    (/jdbc/<table>[/<id>]) and the method.
    """
    creds = dict(credentials or {})
    url = server_url.rstrip("/") + path.format(
        **{k: requests.utils.quote(str(v), safe="") for k, v in (values or {}).items()}
    )
    headers: dict[str, str] = {"Content-Type": "application/json"}

    # Embed JDBC-specific auth into the request headers the Kotlin side
    # understands (X-JDBC-*). Keeps the HTTP layer dumb.
    for src, dst in (
        ("username",     "X-JDBC-User"),
        ("password",     "X-JDBC-Password"),
        ("auth_type",    "X-JDBC-Auth"),
        ("audience",     "X-JDBC-Audience"),
        ("scope",        "X-JDBC-Scope"),
        ("token_url",    "X-JDBC-TokenURL"),
        ("client_id",    "X-JDBC-ClientId"),
        ("client_secret","X-JDBC-ClientSecret"),
    ):
        if creds.get(src):
            headers[dst] = str(creds[src])

    payload = values.get("body") if values else None
    data = None if payload is None else json.dumps(payload)

    try:
        r = requests.request(method.upper(), url,
                             headers=headers, data=data, timeout=timeout_s)
    except requests.RequestException as e:
        return Response(status=0, body=f"Error: {e}", headers={})

    resp = Response(status=r.status_code, headers=dict(r.headers))
    resp.body = r.text or ""
    return resp
