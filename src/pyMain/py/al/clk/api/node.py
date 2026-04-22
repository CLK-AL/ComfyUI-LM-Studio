"""The single OpenAPINode class ComfyUI sees.

Inputs are intentionally few + flexible so one node covers every spec:
  - spec_source     (STRING)   : file path / URL / raw JSON/YAML / '<preset>'
  - operation_id    (STRING)   : operationId from the spec
  - protocol        (enum)     : http | sse | wss
  - method          (enum)     : GET/POST/... + PROPFIND/MKCOL/... (unused on wss/sse)
  - values_json     (STRING)   : JSON with the op's path/query/header/body values
  - content_type    (STRING)   : optional override for request content type
  - accept          (STRING)   : optional override for Accept header
  - auth_scheme     (STRING)   : name of a scheme in components.securitySchemes
  - credentials_json(STRING)   : JSON {token | apiKey | username+password}
  - file_path       (STRING)   : optional path for octet-stream uploads
  - server_url      (STRING)   : override spec.servers[0]

Outputs:
  - body     (STRING)  — decoded response body (JSON pretty-printed for dicts)
  - stats    (STRING)  — HTTP status + byte count
  - headers  (STRING)  — response headers as JSON

The auto-generated `OpenAPIOperationNode:<preset>:<opId>` variants (in
registry.py) pre-fill spec_source / operation_id / protocol / method so
the user just wires values_json.
"""
from __future__ import annotations

import json
from typing import Any, Dict, Tuple

from .loader import load_spec
from .protocols import get_executor
from .presets import PRESETS


class OpenAPINode:
    CATEGORY = "API"
    FUNCTION = "invoke"
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("body", "stats", "headers")

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        preset_names = list(PRESETS.keys())
        return {
            "required": {
                "spec_kind": (["openapi", "asyncapi", "graphql"],
                              {"default": "openapi"}),
                "spec_source": ("STRING", {
                    "default": f"preset:{preset_names[0]}" if preset_names else "",
                    "multiline": True,
                }),
                "operation_id": ("STRING", {"default": "", "multiline": False}),
                "protocol": (["http", "sse", "wss"],),
                "method": (
                    ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS",
                     "PROPFIND", "PROPPATCH", "MKCOL", "COPY", "MOVE",
                     "LOCK", "UNLOCK", "REPORT"],
                ),
                "values_json": ("STRING", {"default": "{}", "multiline": True}),
            },
            "optional": {
                "content_type": ("STRING", {"default": ""}),
                "accept":       ("STRING", {"default": ""}),
                "auth_scheme":  ("STRING", {"default": ""}),
                "credentials_json": ("STRING", {"default": "{}", "multiline": True}),
                "file_path":    ("STRING", {"default": ""}),
                "server_url":   ("STRING", {"default": ""}),
            },
        }

    # --- core ------------------------------------------------------------
    def invoke(
        self,
        spec_kind: str,
        spec_source: str,
        operation_id: str,
        protocol: str,
        method: str,
        values_json: str,
        content_type: str = "",
        accept: str = "",
        auth_scheme: str = "",
        credentials_json: str = "{}",
        file_path: str = "",
        server_url: str = "",
    ) -> Tuple[str, str, str]:
        try:
            spec = self._resolve_spec(spec_source)
            values = json.loads(values_json or "{}")
            creds  = json.loads(credentials_json or "{}")

            if spec_kind.lower() != "openapi":
                # Dispatch through the handler registry — AsyncAPI /
                # GraphQL raise NotImplementedError with a clear message
                # until their handlers land.
                from .spec_kinds import for_kind
                handler = for_kind(spec_kind)
                resp = handler.execute(
                    spec, operation_id, values,
                    protocol=protocol, server_url=server_url,
                    file_path=file_path or None,
                )
                return resp.as_tuple()

            op, path, method_from_spec = find_operation(spec, operation_id)
            if not method or method.upper() in ("", "AUTO"):
                method = method_from_spec
            chosen_server = server_url or (
                (spec.get("servers") or [{}])[0].get("url", "")
            ) or ""
            scheme = None
            if auth_scheme:
                scheme = (spec.get("components", {})
                              .get("securitySchemes", {})
                              .get(auth_scheme))

            executor = get_executor(protocol)
            resp = executor(
                operation=op, method=method, server_url=chosen_server,
                path=path, values=values,
                auth_scheme=scheme, credentials=creds,
                file_path=file_path or None,
            )

            if content_type:
                resp.headers.setdefault("x-request-content-type", content_type)
            if accept:
                resp.headers.setdefault("x-request-accept", accept)

            return resp.as_tuple()
        except Exception as e:  # noqa: BLE001
            return (f"Error: {e}", "HTTP 0\nBytes: 0", "{}")

    # --- helpers ---------------------------------------------------------
    @staticmethod
    def _resolve_spec(src: str) -> dict:
        s = src.strip()
        if s.startswith("preset:"):
            key = s[len("preset:"):].strip()
            if key not in PRESETS:
                raise ValueError(
                    f"Unknown preset {key!r}. Available: {sorted(PRESETS.keys())}"
                )
            return PRESETS[key].spec()
        return load_spec(s)


def find_operation(spec: dict, operation_id: str) -> tuple[dict, str, str]:
    """Return (operation_dict, path, http_method) for the given operationId."""
    for path, item in (spec.get("paths") or {}).items():
        for method, op in (item or {}).items():
            if not isinstance(op, dict):
                continue
            if op.get("operationId") == operation_id:
                return op, path, method.upper()
    raise KeyError(f"operationId {operation_id!r} not found in spec")
