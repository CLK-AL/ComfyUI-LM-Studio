"""Protocol executors. One module per transport; all implement `execute()`.

Each module exports:
    execute(operation, server_url, params, request_body, auth, **kw) -> Response
where `Response` is the small dataclass defined in this module.

Only `http` is fully implemented in the MVP. `wss` and `sse` raise
NotImplementedError with a clear message — the surface is in place so
upgrading later won't change any call sites.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Response:
    status: int = 0
    headers: dict = field(default_factory=dict)
    body: str = ""
    bytes_: bytes | None = None
    file_path: str | None = None
    events: list[dict] = field(default_factory=list)  # for SSE/WSS

    def as_tuple(self) -> tuple[str, str, str]:
        """Return (body, stats, headers_json) for ComfyUI output slots."""
        import json
        stats = f"HTTP {self.status}\nBytes: {len(self.body) if self.body else (len(self.bytes_) if self.bytes_ else 0)}"
        return (self.body or (self.file_path or ""), stats, json.dumps(self.headers))


def get_executor(protocol: str):
    protocol = protocol.lower()
    if protocol == "http":
        from . import http as mod
    elif protocol == "wss":
        from . import wss as mod
    elif protocol == "sse":
        from . import sse as mod
    else:
        raise ValueError(f"Unsupported protocol: {protocol!r}")
    return mod.execute
