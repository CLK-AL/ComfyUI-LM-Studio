"""Load an OpenAPI spec from any source a ComfyUI workflow can produce.

Accepts:
  * `file:///path/to/spec.yaml` or plain filesystem paths
  * `http(s)://.../openapi.yaml` URLs
  * raw JSON/YAML string
  * bytes (e.g. from a multipart file upload handled by a ComfyUI widget)

Format is autodetected (YAML-by-default, JSON if the payload starts with
'{' / '[').
"""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Mapping, Union

SpecSource = Union[str, bytes, Path, Mapping[str, Any]]


def _parse(text: str) -> dict:
    s = text.lstrip()
    if s.startswith(("{", "[")):
        return json.loads(text)
    # YAML via PyYAML if available; otherwise a narrow fallback that
    # only tolerates JSON-compatible YAML (enough for most spec stubs).
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text) or {}
    except ImportError:
        try:
            return json.loads(text)
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(
                "PyYAML is not installed and the spec is not valid JSON. "
                "Install pyyaml to load YAML OpenAPI documents."
            ) from e


def load_spec(source: SpecSource, *, timeout_s: float = 20.0) -> dict:
    """Return a parsed OpenAPI document as a dict."""
    if isinstance(source, Mapping):
        return dict(source)

    if isinstance(source, bytes):
        return _parse(source.decode("utf-8"))

    if isinstance(source, Path):
        return _parse(source.read_text())

    assert isinstance(source, str)
    s = source.strip()

    # URL
    if s.startswith(("http://", "https://", "file://")):
        req = urllib.request.Request(s, headers={"User-Agent": "comfyui-openapi-node"})
        with urllib.request.urlopen(req, timeout=timeout_s) as r:
            return _parse(r.read().decode("utf-8"))

    # Filesystem path (relative or absolute). Treat it as a path only if
    # it looks like one and the file actually exists — otherwise the
    # string is treated as inline spec text.
    maybe_path = os.path.expanduser(s)
    if os.path.isfile(maybe_path):
        return _parse(Path(maybe_path).read_text())

    return _parse(s)
