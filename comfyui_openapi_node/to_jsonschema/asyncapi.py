"""AsyncAPI → JSON Schema canonical form.

AsyncAPI 2.x/3.x uses JSON Schema for `components.schemas` (and
`message.payload`). The mapping:

  spec.channels.<name>.{subscribe|publish}.message.payload  → input_schema
  spec.channels.<name>.subscribe.message.payload            → output_schema
  spec.servers[0].url + channel name                        → server_url + path
  spec.components.schemas                                   → components.schemas

Status: scaffold. The field names differ a touch between 2.x and 3.x
(3.x moves operations out of channels), so `convert()` keeps it loose
and returns an empty ops list when it can't parse the shape yet.
"""
from __future__ import annotations

from typing import Mapping

from . import Canonical, OperationSchema


def _payload(message: Mapping | None) -> dict:
    if not isinstance(message, Mapping):
        return {}
    return (message.get("payload") or {})


def convert(spec: Mapping) -> Canonical:
    ops: list[OperationSchema] = []
    # AsyncAPI 2.x shape: channels[name] = { subscribe | publish | parameters | … }
    for ch_name, channel in (spec.get("channels") or {}).items():
        if not isinstance(channel, Mapping):
            continue
        for action in ("subscribe", "publish"):
            entry = channel.get(action)
            if not isinstance(entry, Mapping):
                continue
            op_id = entry.get("operationId") or f"{action}:{ch_name}"
            payload = _payload(entry.get("message"))
            # Input vs. output: publish = we send; subscribe = we receive.
            if action == "publish":
                input_schema, output_schema = payload, {}
            else:
                input_schema, output_schema = {}, payload
            ops.append(OperationSchema(
                id=op_id,
                protocol="ws",       # AsyncAPI bindings vary; ws/sse/mqtt/amqp — default to ws
                verb=action,
                path=ch_name,
                input_schema=input_schema,
                output_schema=output_schema,
                parameters=[],
                security=list(entry.get("security") or []),
                raw=dict(entry),
            ))

    servers = spec.get("servers") or {}
    first_server_url = ""
    if isinstance(servers, Mapping) and servers:
        first = next(iter(servers.values()))
        if isinstance(first, Mapping):
            first_server_url = first.get("url", "")

    return Canonical(
        title=((spec.get("info") or {}).get("title") or ""),
        version=((spec.get("info") or {}).get("version") or ""),
        server_url=first_server_url,
        components=dict(spec.get("components") or {}),
        operations=ops,
    )
