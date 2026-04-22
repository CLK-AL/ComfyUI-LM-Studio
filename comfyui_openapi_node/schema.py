"""Map OpenAPI / JSON Schema types to ComfyUI INPUT_TYPES entries.

Intentionally conservative: unknown/complex shapes fall through to a
multiline STRING so nothing is silently dropped. A user can always
paste a JSON blob.
"""
from __future__ import annotations

from typing import Any


def _str(default: str = "", multiline: bool = False) -> tuple:
    return ("STRING", {"default": default, "multiline": multiline})


def _int(default: int = 0, minimum: int = -(2 ** 31), maximum: int = 2 ** 31 - 1) -> tuple:
    return ("INT", {"default": default, "min": minimum, "max": maximum, "step": 1})


def _float(default: float = 0.0, minimum: float = -1e9, maximum: float = 1e9) -> tuple:
    return ("FLOAT", {"default": default, "min": minimum, "max": maximum, "step": 0.01})


def _bool(default: bool = False) -> tuple:
    return ("BOOLEAN", {"default": default})


def _enum(values: list[Any]) -> tuple:
    return (list(map(str, values)),)


def json_schema_to_comfy(schema: dict | None, name: str = "") -> tuple:
    """Return a ComfyUI INPUT_TYPES tuple for a JSON-Schema fragment."""
    if not schema:
        return _str()

    if "enum" in schema:
        return _enum(schema["enum"])

    t = schema.get("type")
    if t == "integer":
        return _int(
            default=schema.get("default", 0),
            minimum=schema.get("minimum", -(2 ** 31)),
            maximum=schema.get("maximum", 2 ** 31 - 1),
        )
    if t == "number":
        return _float(
            default=schema.get("default", 0.0),
            minimum=schema.get("minimum", -1e9),
            maximum=schema.get("maximum", 1e9),
        )
    if t == "boolean":
        return _bool(schema.get("default", False))
    if t == "string":
        fmt = schema.get("format", "")
        if fmt in ("binary", "byte"):  # file upload
            return _str()  # filesystem path — executor handles it
        return _str(default=str(schema.get("default", "")),
                    multiline=bool(schema.get("x-multiline") or fmt == "textarea"))

    # object / array / anyOf / oneOf / $ref / null → let the user paste JSON
    return _str(multiline=True)
