"""Server-Sent Events executor.

Streams `data:` frames from a long-lived GET, accumulates them into
Response.events, and also concatenates their payloads into .body. The
consumer can either JSON-parse each event dict or read .body as one
flat string.

Content negotiation for event payloads uses the same codecs as HTTP:
if each `data:` line starts with '{' it's JSON-parsed, otherwise
kept as text.
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
    max_events: int = 1024,
    timeout_s: float = 600.0,
    **_ignored,
) -> Response:
    url = server_url.rstrip("/") + path
    headers = {"Accept": "text/event-stream", "Cache-Control": "no-cache"}
    qp = {p["name"]: values.get(p["name"]) for p in (operation.get("parameters") or [])
          if p.get("in") == "query" and p.get("name") in (values or {})}

    req_kwargs = {"url": url, "headers": headers, "params": qp, "stream": True, "timeout": timeout_s}
    if auth_scheme:
        from .. import security
        security.apply(req_kwargs, auth_scheme, credentials or {})

    resp = Response()
    try:
        with requests.get(**req_kwargs) as r:
            resp.status = r.status_code
            resp.headers = dict(r.headers)
            buf_data = []
            event = {"event": None, "id": None, "data": ""}
            count = 0
            for raw in r.iter_lines(decode_unicode=True):
                if raw is None:
                    continue
                line = raw.rstrip("\r")
                if line == "":
                    if event["data"]:
                        payload = event["data"].strip()
                        if payload.startswith(("{", "[")):
                            try:
                                payload = json.loads(payload)
                            except Exception:
                                pass
                        event_record = {**event, "data": payload}
                        resp.events.append(event_record)
                        buf_data.append(event_record["data"] if isinstance(event_record["data"], str)
                                        else json.dumps(event_record["data"]))
                        count += 1
                        if count >= max_events:
                            break
                    event = {"event": None, "id": None, "data": ""}
                    continue
                if line.startswith(":"):
                    continue  # comment
                if ":" in line:
                    field, _, val = line.partition(":")
                    val = val.lstrip(" ")
                    if field == "data":
                        event["data"] += (val + "\n")
                    elif field == "event":
                        event["event"] = val
                    elif field == "id":
                        event["id"] = val
            resp.body = "\n".join(buf_data)
    except requests.RequestException as e:
        resp.status = 0
        resp.body = f"Error: {e}"
    return resp
