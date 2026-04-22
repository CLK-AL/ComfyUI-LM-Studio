"""JSON Schema / OpenAPI → ComfyUI INPUT_TYPES mapping.

Covers every standard `type` + `format` combination, and passes every
constraint (min / max / exclusive bounds / multipleOf / length / pattern
/ uniqueItems / …) through as extra entries in the options dict so a
smart UI — or downstream validation — can see them. ComfyUI's built-in
widgets ignore unknown keys, which makes this safe as a lossless
projection.

Field names emitted (per-type):

  STRING options:
    default, multiline
    min_length, max_length, pattern, format
    placeholder, password, is_json, is_file_path, is_base64
  INT options:
    default, min, max, step, multiple_of, exclusive_minimum, exclusive_maximum
    format (int32 | int64)
  FLOAT options:
    default, min, max, step, multiple_of, exclusive_minimum, exclusive_maximum
    format (float | double)
  BOOLEAN options:
    default
  (enum)     → ( [v1, v2, ...], )    ComfyUI dropdown
"""
from __future__ import annotations

from typing import Any, Mapping

# ----- format → UI hint map ---------------------------------------------
# Hints are *advice* — purely annotations downstream consumers may read.
# None of them break standard ComfyUI widgets.
_STRING_FORMATS: dict[str, dict] = {
    "date":         {"placeholder": "YYYY-MM-DD"},
    "date-time":    {"placeholder": "YYYY-MM-DDTHH:MM:SSZ"},
    "time":         {"placeholder": "HH:MM:SS"},
    "duration":     {"placeholder": "P1DT2H"},
    "email":        {"placeholder": "user@example.com"},
    "idn-email":    {"placeholder": "user@example.com"},
    "hostname":     {"placeholder": "example.com"},
    "idn-hostname": {"placeholder": "example.com"},
    "ipv4":         {"placeholder": "0.0.0.0"},
    "ipv6":         {"placeholder": "::1"},
    "uri":          {"placeholder": "https://…"},
    "uri-reference":{"placeholder": "/path?q=1"},
    "uri-template": {"placeholder": "/things/{id}"},
    "iri":          {"placeholder": "https://…"},
    "uuid":         {"placeholder": "00000000-0000-0000-0000-000000000000"},
    "password":     {"password": True},
    "byte":         {"is_base64": True},
    "binary":       {"is_file_path": True, "multiline": False},
    "textarea":     {"multiline": True},
    "json":         {"multiline": True, "is_json": True},
    "yaml":         {"multiline": True},
    "markdown":     {"multiline": True},
    "regex":        {"placeholder": "^.*$"},
}

# Loose default regexes to fall back on when the spec doesn't supply
# one — purely advisory.
_DEFAULT_PATTERNS: dict[str, str] = {
    "email":  r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    "uuid":   r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
    "ipv4":   r"^(\d{1,3}\.){3}\d{1,3}$",
    "date":   r"^\d{4}-\d{2}-\d{2}$",
}

_INT_FORMAT_BOUNDS: dict[str, tuple[int, int]] = {
    "int32": (-(2 ** 31), 2 ** 31 - 1),
    "int64": (-(2 ** 63), 2 ** 63 - 1),
}


# ----- primitive builders -----------------------------------------------
def _drop_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def _str(default: str = "", multiline: bool = False, **extras) -> tuple:
    opts = {"default": default, "multiline": multiline}
    opts.update(_drop_none(extras))
    return ("STRING", opts)


def _int(default: int = 0, min_: int = -(2 ** 31), max_: int = 2 ** 31 - 1,
         step: int = 1, **extras) -> tuple:
    opts = {"default": default, "min": min_, "max": max_, "step": step}
    opts.update(_drop_none(extras))
    return ("INT", opts)


def _float(default: float = 0.0, min_: float = -1e9, max_: float = 1e9,
           step: float = 0.01, **extras) -> tuple:
    opts = {"default": default, "min": min_, "max": max_, "step": step}
    opts.update(_drop_none(extras))
    return ("FLOAT", opts)


def _bool(default: bool = False) -> tuple:
    return ("BOOLEAN", {"default": default})


def _enum(values: list[Any]) -> tuple:
    # Stringify — ComfyUI dropdowns are strings.
    return (list(map(str, values)),)


# ----- constraint helpers -----------------------------------------------
def _int_bounds(schema: Mapping) -> tuple[int, int]:
    # Start with format-defined defaults (int32 / int64 if specified).
    fmt = schema.get("format") or ""
    lo_default, hi_default = _INT_FORMAT_BOUNDS.get(fmt, (-(2 ** 31), 2 ** 31 - 1))
    lo = schema.get("minimum", lo_default)
    hi = schema.get("maximum", hi_default)
    # OpenAPI 3.1: exclusiveMinimum / exclusiveMaximum are numbers.
    # OpenAPI 3.0: they are booleans paired with minimum/maximum.
    xlo = schema.get("exclusiveMinimum")
    xhi = schema.get("exclusiveMaximum")
    if isinstance(xlo, bool) and xlo and isinstance(lo, (int, float)):
        lo = int(lo) + 1
    elif isinstance(xlo, (int, float)) and not isinstance(xlo, bool):
        lo = max(lo, int(xlo) + 1) if lo is not None else int(xlo) + 1
    if isinstance(xhi, bool) and xhi and isinstance(hi, (int, float)):
        hi = int(hi) - 1
    elif isinstance(xhi, (int, float)) and not isinstance(xhi, bool):
        hi = min(hi, int(xhi) - 1) if hi is not None else int(xhi) - 1
    return int(lo), int(hi)


def _float_bounds(schema: Mapping) -> tuple[float, float, float | None, float | None]:
    # Return (min, max, exclusiveMin, exclusiveMax) — for floats we
    # keep the exclusive values as annotations rather than collapsing
    # them with an epsilon.
    lo = schema.get("minimum", -1e9)
    hi = schema.get("maximum",  1e9)
    xlo = schema.get("exclusiveMinimum")
    xhi = schema.get("exclusiveMaximum")
    xlo_out = float(xlo) if isinstance(xlo, (int, float)) and not isinstance(xlo, bool) else None
    xhi_out = float(xhi) if isinstance(xhi, (int, float)) and not isinstance(xhi, bool) else None
    return float(lo), float(hi), xlo_out, xhi_out


# ----- main entry point -------------------------------------------------
def json_schema_to_comfy(schema: dict | None, name: str = "") -> tuple:
    """Return a ComfyUI INPUT_TYPES tuple for a JSON-Schema fragment."""
    if not schema:
        return _str()

    # Enums short-circuit regardless of type (OpenAPI allows `enum`
    # with an optional `type`).
    if "enum" in schema:
        return _enum(schema["enum"])

    t = schema.get("type")

    # --- integer ---
    if t == "integer":
        lo, hi = _int_bounds(schema)
        return _int(
            default=schema.get("default", 0),
            min_=lo, max_=hi,
            step=int(schema.get("multipleOf", 1) or 1),
            multiple_of=schema.get("multipleOf"),
            exclusive_minimum=schema.get("exclusiveMinimum"),
            exclusive_maximum=schema.get("exclusiveMaximum"),
            format=schema.get("format"),
        )

    # --- number ---
    if t == "number":
        lo, hi, xlo, xhi = _float_bounds(schema)
        step = float(schema.get("multipleOf", 0.01) or 0.01)
        return _float(
            default=float(schema.get("default", 0.0)),
            min_=lo, max_=hi, step=step,
            multiple_of=schema.get("multipleOf"),
            exclusive_minimum=xlo,
            exclusive_maximum=xhi,
            format=schema.get("format"),
        )

    # --- boolean ---
    if t == "boolean":
        return _bool(default=bool(schema.get("default", False)))

    # --- string ---
    if t == "string":
        fmt = (schema.get("format") or "").strip()
        hints = dict(_STRING_FORMATS.get(fmt, {}))
        multiline = bool(hints.pop("multiline", False) or schema.get("x-multiline"))
        default = str(schema.get("default", ""))
        pattern = schema.get("pattern") or _DEFAULT_PATTERNS.get(fmt)
        return _str(
            default=default,
            multiline=multiline,
            min_length=schema.get("minLength"),
            max_length=schema.get("maxLength"),
            pattern=pattern,
            format=fmt or None,
            **hints,
        )

    # --- array ---
    if t == "array":
        # ComfyUI has no array widget — surface as a multiline JSON blob
        # with the container constraints annotated.
        return _str(
            default="[]",
            multiline=True,
            is_json=True,
            format="array",
            min_items=schema.get("minItems"),
            max_items=schema.get("maxItems"),
            unique_items=schema.get("uniqueItems"),
            items_type=((schema.get("items") or {}).get("type") or None),
        )

    # --- object / oneOf / allOf / anyOf / null / $ref — free-form JSON ---
    hints: dict[str, Any] = {"is_json": True, "format": "object"}
    if schema.get("type") == "null":
        hints = {"format": "null"}
    return _str(default="{}" if schema.get("type") == "object" else "",
                multiline=True, **hints)
