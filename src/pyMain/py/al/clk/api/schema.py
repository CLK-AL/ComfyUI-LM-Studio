"""JSON Schema / OpenAPI → ComfyUI INPUT_TYPES mapping.

## Coverage — JSON Schema Draft 2020-12 standard formats

date-time · date · time · duration · email · idn-email · hostname ·
idn-hostname · ipv4 · ipv6 · uri · uri-reference · uri-template · iri
· iri-reference · uuid · regex · json-pointer · relative-json-pointer
· password (OpenAPI) · byte (OpenAPI) · binary (OpenAPI)

Plus the `x-*` and RJSF-style hints we recognise:
textarea · json · yaml · markdown · color · tel · geojson

## RJSF uiSchema → ComfyUI widget options

`merge_ui_schema(tuple_, ui_schema)` takes a ComfyUI INPUT_TYPES tuple
emitted by `json_schema_to_comfy` and overlays RJSF uiSchema hints.
Supported `ui:widget` values (covers the full RJSF default widget set):

  text        → STRING, multiline=False
  textarea    → STRING, multiline=True
  password    → STRING, password=True
  email       → STRING, format=email
  color       → STRING, format=color
  date        → STRING, format=date
  date-time   → STRING, format=date-time
  time        → STRING, format=time
  file        → STRING, is_file_path=True
  hidden      → tuple unchanged but x-hidden=True annotation set
  updown      → INT/FLOAT, display=number
  range       → INT/FLOAT, display=slider
  select      → combo (already so if schema had enum)
  radio       → combo + x-display=radio
  checkbox    → BOOLEAN
  checkboxes  → STRING multiline + is_json + x-display=checkboxes

Plus RJSF `ui:options`, `ui:help`, `ui:description`, `ui:placeholder`,
`ui:title`, `ui:disabled`, `ui:readonly`, `ui:autofocus`, `ui:emptyValue`
all survive as annotations on the ComfyUI options dict.

## Field names emitted on each ComfyUI type

  STRING options:
    default, multiline
    min_length, max_length, pattern, format
    placeholder, password, is_json, is_file_path, is_base64
    x-hidden, x-widget, x-display, x-help, x-title, x-readonly, x-disabled
  INT options:
    default, min, max, step, multiple_of, exclusive_minimum, exclusive_maximum
    format (int32 | int64), display (number | slider)
  FLOAT options:
    default, min, max, step, multiple_of, exclusive_minimum, exclusive_maximum
    format (float | double), display (number | slider)
  BOOLEAN options:
    default, label_on, label_off
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
    "iri-reference":        {"placeholder": "https://…"},
    "json-pointer":         {"placeholder": "/foo/bar"},
    "relative-json-pointer":{"placeholder": "1/foo"},
    "color":        {"placeholder": "#RRGGBB"},
    "tel":          {"placeholder": "+1 555 0100"},
    "geojson":      {"multiline": True, "is_json": True,
                     "placeholder": '{"type":"Point","coordinates":[0,0]}'},
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
    fmt = (schema.get("format") or "").strip()
    if schema.get("type") == "null":
        hints = {"format": "null"}
    elif fmt and fmt in _STRING_FORMATS:
        # Honor format when present even on object schemas (e.g. geojson).
        hints = dict(_STRING_FORMATS[fmt])
        hints.setdefault("is_json", True)
        hints["format"] = fmt
        if schema.get("x-geotype"):
            hints["x-geotype"] = schema["x-geotype"]
    else:
        hints = {"is_json": True, "format": fmt or "object"}
    # Let `hints` drive `multiline` when it carries one (geojson etc.).
    multiline = hints.pop("multiline", True)
    return _str(default="{}" if schema.get("type") == "object" else "",
                multiline=multiline, **hints)


# ----- RJSF uiSchema overlay --------------------------------------------
# Maps React JSON Schema Form `ui:widget` values to ComfyUI option
# mutations. Each entry is a callable that takes the current options
# dict and updates it in place. Keeps unknown widgets harmless
# (x-widget annotation).
_UI_WIDGET: dict[str, Any] = {
    "text":       lambda o: o.update({"multiline": False}),
    "textarea":   lambda o: o.update({"multiline": True}),
    "password":   lambda o: o.update({"password": True}),
    "email":      lambda o: o.update({"format": "email"}),
    "color":      lambda o: o.update({"format": "color",
                                      "placeholder": o.get("placeholder") or "#RRGGBB"}),
    "date":       lambda o: o.update({"format": "date"}),
    "date-time":  lambda o: o.update({"format": "date-time"}),
    "time":       lambda o: o.update({"format": "time"}),
    "file":       lambda o: o.update({"is_file_path": True, "multiline": False}),
    "hidden":     lambda o: o.update({"x-hidden": True}),
    "updown":     lambda o: o.update({"display": "number"}),
    "range":      lambda o: o.update({"display": "slider"}),
    "radio":      lambda o: o.update({"x-display": "radio"}),
    "checkbox":   lambda o: None,  # handled in merge_ui_schema (retype → BOOLEAN)
    "checkboxes": lambda o: o.update({"multiline": True, "is_json": True,
                                      "x-display": "checkboxes"}),
    "select":     lambda o: None,  # schema enum already drives this
}


def merge_ui_schema(comfy_tuple: tuple, ui_schema: Mapping | None) -> tuple:
    """Overlay an RJSF-style uiSchema onto a ComfyUI tuple.

    Safe on `None` / empty / unknown keys — returns the tuple unchanged
    when it can't apply anything.
    """
    if not ui_schema:
        return comfy_tuple
    # Extract current options
    if len(comfy_tuple) == 1:
        # (enum tuple,) — only widget:radio is meaningful here; rest pass.
        widget = (ui_schema.get("ui:widget") or "").lower()
        if widget == "radio":
            return (comfy_tuple[0], {"x-display": "radio"})
        return comfy_tuple
    ctype, opts = comfy_tuple[0], dict(comfy_tuple[1])

    widget = (ui_schema.get("ui:widget") or "").lower()

    # `checkbox` widget coerces the base type to BOOLEAN.
    if widget == "checkbox" and ctype != "BOOLEAN":
        return ("BOOLEAN", {"default": bool(opts.get("default") or False)})

    fn = _UI_WIDGET.get(widget)
    if fn is not None:
        fn(opts)
    elif widget:
        opts["x-widget"] = widget

    # Generic RJSF ui:* passthroughs (purely annotations).
    for src, dst in (
        ("ui:placeholder", "placeholder"),
        ("ui:help",        "x-help"),
        ("ui:title",       "x-title"),
        ("ui:description", "x-description"),
        ("ui:disabled",    "x-disabled"),
        ("ui:readonly",    "x-readonly"),
        ("ui:autofocus",   "x-autofocus"),
        ("ui:emptyValue",  "x-empty-value"),
    ):
        if src in ui_schema:
            opts[dst] = ui_schema[src]

    # ui:options is a dict of arbitrary widget options — pass it through
    # under `x-ui-options` so downstream widgets can read it.
    if "ui:options" in ui_schema:
        opts["x-ui-options"] = dict(ui_schema["ui:options"])

    return (ctype, opts)
