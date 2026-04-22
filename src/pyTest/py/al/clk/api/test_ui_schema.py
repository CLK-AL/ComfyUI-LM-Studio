"""Verify full JSON Schema format coverage + RJSF uiSchema overlay."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.schema import (
    json_schema_to_comfy as to_comfy,
    merge_ui_schema,
)


# --- JSON Schema Draft 2020-12 format coverage ---------------------------
_FORMATS = [
    "date-time", "date", "time", "duration",
    "email", "idn-email", "hostname", "idn-hostname",
    "ipv4", "ipv6",
    "uri", "uri-reference", "uri-template", "iri", "iri-reference",
    "uuid", "regex",
    "json-pointer", "relative-json-pointer",
    # OpenAPI-extension formats
    "password", "byte", "binary",
]


def test_every_standard_format_is_recognised():
    for fmt in _FORMATS:
        t, o = to_comfy({"type": "string", "format": fmt})
        assert t == "STRING", fmt
        # Either a placeholder or a format-specific flag must be set —
        # otherwise the format was silently dropped.
        evidence = (
            o.get("format") == fmt
            or o.get("placeholder")
            or o.get("password")
            or o.get("is_base64")
            or o.get("is_file_path")
            or o.get("multiline")
        )
        assert evidence, f"format {fmt!r} produced no annotation: {o}"


# --- uiSchema → widget ---------------------------------------------------
def _base():
    return to_comfy({"type": "string"})


def test_uiwidget_textarea_enables_multiline():
    _, o = merge_ui_schema(_base(), {"ui:widget": "textarea"})
    assert o["multiline"] is True


def test_uiwidget_password_sets_password_flag():
    _, o = merge_ui_schema(_base(), {"ui:widget": "password"})
    assert o["password"] is True


def test_uiwidget_color_sets_format_and_placeholder():
    _, o = merge_ui_schema(_base(), {"ui:widget": "color"})
    assert o["format"] == "color"
    assert "#" in o["placeholder"]


def test_uiwidget_date_sets_format():
    _, o = merge_ui_schema(_base(), {"ui:widget": "date"})
    assert o["format"] == "date"


def test_uiwidget_file_marks_file_path():
    _, o = merge_ui_schema(_base(), {"ui:widget": "file"})
    assert o["is_file_path"] is True


def test_uiwidget_hidden_annotates_hidden():
    _, o = merge_ui_schema(_base(), {"ui:widget": "hidden"})
    assert o["x-hidden"] is True


def test_uiwidget_updown_on_integer_sets_display_number():
    base = to_comfy({"type": "integer"})
    _, o = merge_ui_schema(base, {"ui:widget": "updown"})
    assert o["display"] == "number"


def test_uiwidget_range_on_number_sets_display_slider():
    base = to_comfy({"type": "number"})
    _, o = merge_ui_schema(base, {"ui:widget": "range"})
    assert o["display"] == "slider"


def test_uiwidget_checkbox_forces_boolean():
    base = to_comfy({"type": "string"})
    t, o = merge_ui_schema(base, {"ui:widget": "checkbox"})
    assert t == "BOOLEAN"
    assert "default" in o


def test_uiwidget_checkboxes_multiline_json():
    _, o = merge_ui_schema(_base(), {"ui:widget": "checkboxes"})
    assert o["multiline"] is True and o["is_json"] is True
    assert o["x-display"] == "checkboxes"


def test_uiwidget_radio_on_enum_annotates_radio():
    base = to_comfy({"enum": ["a", "b"]})
    out = merge_ui_schema(base, {"ui:widget": "radio"})
    assert out[0] == ["a", "b"]
    assert out[1]["x-display"] == "radio"


def test_uiwidget_unknown_survives_as_x_widget():
    _, o = merge_ui_schema(_base(), {"ui:widget": "my-custom-widget"})
    assert o["x-widget"] == "my-custom-widget"


# --- RJSF annotations passthrough ----------------------------------------
def test_ui_help_title_description_survive():
    _, o = merge_ui_schema(_base(), {
        "ui:placeholder": "type here",
        "ui:help":        "helpful note",
        "ui:title":       "nice title",
        "ui:description": "long text",
        "ui:disabled":    True,
        "ui:readonly":    False,
        "ui:autofocus":   True,
        "ui:emptyValue":  "",
        "ui:options":     {"rows": 5, "inline": True},
    })
    assert o["placeholder"]     == "type here"
    assert o["x-help"]          == "helpful note"
    assert o["x-title"]         == "nice title"
    assert o["x-description"]   == "long text"
    assert o["x-disabled"]      is True
    assert o["x-readonly"]      is False
    assert o["x-autofocus"]     is True
    assert o["x-empty-value"]   == ""
    assert o["x-ui-options"]    == {"rows": 5, "inline": True}


def test_empty_ui_schema_is_noop():
    tup = _base()
    assert merge_ui_schema(tup, None) == tup
    assert merge_ui_schema(tup, {}) == tup
