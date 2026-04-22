"""WebSocket (ws/wss) executor.

Uses the `websockets` sync client if installed; falls back to a clear
NotImplementedError otherwise so the missing-dep path fails loudly.

Supports:
  * Sending an initial payload (the user's request body, serialized via
    ..codecs based on the operation's requestBody content type).
  * Collecting up to `max_messages` or until close / timeout.
  * Content negotiation on each message (JSON-first, else text/bytes).
"""
from __future__ import annotations

import json

from . import Response


def execute(
    operation: dict,
    method: str,   # unused for WSS, kept for protocol uniformity
    server_url: str,
    path: str,
    values: dict,
    *,
    auth_scheme: dict | None = None,
    credentials: dict | None = None,
    max_messages: int = 256,
    timeout_s: float = 30.0,
    **_ignored,
) -> Response:
    try:
        from websockets.sync.client import connect  # type: ignore
    except ImportError as e:
        raise NotImplementedError(
            "WebSocket support needs the `websockets` package. "
            "Install it with:  pip install websockets"
        ) from e

    ws_url = server_url.rstrip("/") + path
    if ws_url.startswith("http://"):
        ws_url = "ws://" + ws_url[len("http://"):]
    elif ws_url.startswith("https://"):
        ws_url = "wss://" + ws_url[len("https://"):]

    headers: dict[str, str] = {}
    if auth_scheme:
        # Reuse the HTTP security applier — it only touches headers/params
        # for apiKey/bearer/basic, which is what WS upgrades carry too.
        from .. import security
        req = {"headers": headers, "params": {}}
        security.apply(req, auth_scheme, credentials or {})

    resp = Response()
    messages: list = []
    try:
        with connect(ws_url, additional_headers=headers, open_timeout=timeout_s) as ws:
            initial = values.get("body") if values else None
            if initial is not None:
                ws.send(initial if isinstance(initial, (str, bytes)) else json.dumps(initial))
            for _ in range(max_messages):
                try:
                    msg = ws.recv(timeout=timeout_s)
                except TimeoutError:
                    break
                if isinstance(msg, bytes):
                    messages.append({"bytes": len(msg)})
                    continue
                if msg.startswith(("{", "[")):
                    try:
                        messages.append({"data": json.loads(msg)})
                        continue
                    except Exception:
                        pass
                messages.append({"data": msg})
        resp.events = messages
        resp.body = "\n".join(
            m["data"] if isinstance(m.get("data"), str) else json.dumps(m)
            for m in messages
        )
        resp.status = 101  # Switching Protocols — the handshake completed
    except Exception as e:  # noqa: BLE001
        resp.status = 0
        resp.body = f"Error: {e}"
    return resp
