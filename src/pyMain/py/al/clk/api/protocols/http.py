"""HTTP / HTTPS / WebDAV executor.

Supports every HTTP method spelled in the spec — standard (GET/POST/
PUT/DELETE/PATCH/HEAD/OPTIONS) plus WebDAV verbs (PROPFIND, PROPPATCH,
MKCOL, COPY, MOVE, LOCK, UNLOCK, REPORT). Content negotiation goes
through ..codecs.

Parameters:
  operation       — a single OpenAPI operation dict (ops['post'], etc.)
  method          — the verb string (already uppercased)
  server_url      — base URL from spec.servers[0] or user override
  path            — operation path, possibly containing {placeholders}
  values          — a dict of named values the user supplied; we split
                    them into query/path/header/body per the spec.
  auth_scheme     — spec entry from components.securitySchemes
  credentials     — user-supplied creds dict (see security.apply)
  file_path       — optional local path for binary upload bodies
"""
from __future__ import annotations

from typing import Any

import requests

from .. import codecs as _codecs, security
from . import Response


_WEBDAV = {"PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE", "LOCK", "UNLOCK", "REPORT"}
_STANDARD = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
ALLOWED_METHODS = _STANDARD | _WEBDAV


def _split_params(operation: dict, values: dict) -> tuple[dict, dict, dict]:
    """Partition user values into (path_params, query_params, headers)."""
    pp, qp, hd = {}, {}, {}
    for p in operation.get("parameters", []) or []:
        name = p.get("name")
        if name is None or name not in values:
            continue
        where = p.get("in", "query").lower()
        v = values[name]
        if where == "path":
            pp[name] = v
        elif where == "query":
            qp[name] = v
        elif where == "header":
            hd[name] = v
    return pp, qp, hd


def _request_body(operation: dict, values: dict, file_path: str | None) -> tuple[bytes | None, dict]:
    rb = operation.get("requestBody") or {}
    content = rb.get("content") or {}
    if not content:
        return None, {}

    # Prefer the user's "Content-Type" header if they set one; else
    # the first content type the operation declares.
    chosen = None
    for ct, spec in content.items():
        chosen = (ct, spec)
        break
    if chosen is None:
        return None, {}
    ct, ct_spec = chosen
    ct_lower = ct.lower()

    if ct_lower == "multipart/form-data":
        # Build `files=` for requests — one part per property in the schema.
        schema = ct_spec.get("schema") or {}
        props  = schema.get("properties") or {}
        files: list[tuple[str, tuple[str, Any, str]]] = []
        for name, subschema in props.items():
            if name not in values:
                continue
            fmt = (subschema or {}).get("format")
            if fmt in ("binary", "byte"):
                path = values[name]
                files.append((name, (path.split("/")[-1], open(path, "rb"), "application/octet-stream")))
            else:
                files.append((name, (None, str(values[name]), "text/plain")))
        # Let requests set the multipart boundary automatically.
        return None, {"files": files, "_multipart": True}

    if ct_lower == "application/octet-stream" and file_path:
        with open(file_path, "rb") as f:
            return f.read(), {"Content-Type": ct}

    codec = _codecs.pick(ct)
    body_val = values.get("body", values)  # whole body under "body", else the whole dict
    if isinstance(body_val, str):
        # If the user pasted a string that already parses as the right
        # media, ship it verbatim.
        data = body_val.encode()
    else:
        data = codec.encode(body_val)
    return data, {"Content-Type": ct}


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
    timeout_s: float = 120.0,
) -> Response:
    method = method.upper()
    if method not in ALLOWED_METHODS:
        raise ValueError(f"method {method!r} not supported; allowed: {sorted(ALLOWED_METHODS)}")

    pp, qp, hd = _split_params(operation, values or {})
    url = server_url.rstrip("/") + path.format(**{k: requests.utils.quote(str(v), safe="") for k, v in pp.items()})

    body, body_headers = _request_body(operation, values or {}, file_path)
    headers = {**hd, **{k: v for k, v in body_headers.items() if not k.startswith("_")}}

    req_kwargs: dict = {
        "method": method,
        "url": url,
        "params": qp,
        "headers": headers,
        "timeout": timeout_s,
    }
    if body_headers.get("_multipart"):
        req_kwargs["files"] = body_headers["files"]
    elif body is not None:
        req_kwargs["data"] = body

    if auth_scheme:
        security.apply(req_kwargs, auth_scheme, credentials or {})

    try:
        r = requests.request(**req_kwargs)
    except requests.RequestException as e:
        return Response(status=0, headers={"error": str(e)}, body=f"Error: {e}")

    resp = Response(status=r.status_code, headers=dict(r.headers))
    ct = r.headers.get("Content-Type", "")
    codec = _codecs.pick(ct)
    try:
        decoded = codec.decode(r.content)
    except Exception as e:  # noqa: BLE001
        resp.body = f"Error decoding {ct}: {e}"
        resp.bytes_ = r.content
        return resp

    if isinstance(decoded, (dict, list)):
        import json
        resp.body = json.dumps(decoded, ensure_ascii=False)
    elif isinstance(decoded, bytes):
        resp.bytes_ = decoded
        resp.body = ""
    else:
        resp.body = "" if decoded is None else str(decoded)
    return resp
