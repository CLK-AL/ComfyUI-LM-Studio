"""Map every JSON Schema / OpenAPI primitive + format + constraint
into ComfyUI INPUT_TYPES and assert the projection is lossless.

ComfyUI's built-in widgets ignore keys they don't know, so the test
verifies that a) the right base type is chosen, and b) every
constraint survives into the options dict where a smarter UI (or a
validation layer) can see it.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.schema import json_schema_to_comfy as to_comfy


# --- primitives ----------------------------------------------------------
def test_empty_schema_is_string():
    assert to_comfy({})[0] == "STRING"


def test_enum_is_dropdown():
    t, = to_comfy({"enum": ["user", "assistant", "system"]})
    assert t == ["user", "assistant", "system"]


def test_enum_is_dropdown_even_without_type():
    t, = to_comfy({"enum": [1, 2, 3]})
    assert t == ["1", "2", "3"]


def test_integer_defaults_and_bounds():
    t, o = to_comfy({"type": "integer", "default": 5, "minimum": 0, "maximum": 10})
    assert t == "INT"
    assert o["default"] == 5 and o["min"] == 0 and o["max"] == 10


def test_integer_exclusive_bounds_openapi_31():
    # Numeric exclusiveMinimum (OpenAPI 3.1 style) tightens the bound.
    t, o = to_comfy({"type": "integer", "exclusiveMinimum": 0, "exclusiveMaximum": 100})
    assert t == "INT"
    assert o["min"] == 1 and o["max"] == 99
    assert o["exclusive_minimum"] == 0 and o["exclusive_maximum"] == 100


def test_integer_exclusive_bounds_openapi_30():
    # Boolean exclusiveMinimum (OpenAPI 3.0 style) paired with minimum.
    t, o = to_comfy({"type": "integer", "minimum": 0, "exclusiveMinimum": True})
    assert o["min"] == 1


def test_integer_multipleof_becomes_step():
    _, o = to_comfy({"type": "integer", "multipleOf": 5})
    assert o["step"] == 5
    assert o["multiple_of"] == 5


def test_integer_format_int32_and_int64_bounds():
    _, o32 = to_comfy({"type": "integer", "format": "int32"})
    assert o32["min"] == -(2 ** 31) and o32["max"] == 2 ** 31 - 1
    _, o64 = to_comfy({"type": "integer", "format": "int64"})
    assert o64["min"] == -(2 ** 63) and o64["max"] == 2 ** 63 - 1


def test_number_float_and_double():
    t, o = to_comfy({"type": "number", "format": "double",
                     "minimum": 0.0, "maximum": 1.0, "default": 0.5})
    assert t == "FLOAT"
    assert o["default"] == 0.5 and o["min"] == 0.0 and o["max"] == 1.0
    assert o["format"] == "double"


def test_number_multipleof_becomes_step():
    _, o = to_comfy({"type": "number", "multipleOf": 0.05})
    assert abs(o["step"] - 0.05) < 1e-9


def test_boolean():
    t, o = to_comfy({"type": "boolean", "default": True})
    assert t == "BOOLEAN" and o["default"] is True


# --- string & formats ---------------------------------------------------
def test_string_minmax_and_pattern():
    t, o = to_comfy({"type": "string", "minLength": 2, "maxLength": 64,
                     "pattern": "^[A-Z]+$"})
    assert t == "STRING"
    assert o["min_length"] == 2 and o["max_length"] == 64
    assert o["pattern"] == "^[A-Z]+$"


def test_string_format_email_adds_default_pattern_and_placeholder():
    _, o = to_comfy({"type": "string", "format": "email"})
    assert o["format"] == "email"
    assert "@" in o["placeholder"]
    assert o["pattern"].startswith("^")


def test_string_format_uuid_placeholder_and_pattern():
    _, o = to_comfy({"type": "string", "format": "uuid"})
    assert o["format"] == "uuid"
    assert o["pattern"] is not None
    assert "0000" in o["placeholder"]


def test_string_format_password_marks_password():
    _, o = to_comfy({"type": "string", "format": "password"})
    assert o["password"] is True


def test_string_format_binary_marks_file_path():
    _, o = to_comfy({"type": "string", "format": "binary"})
    assert o["is_file_path"] is True
    assert o["multiline"] is False


def test_string_format_byte_marks_base64():
    _, o = to_comfy({"type": "string", "format": "byte"})
    assert o["is_base64"] is True


def test_string_format_textarea_enables_multiline():
    _, o = to_comfy({"type": "string", "format": "textarea"})
    assert o["multiline"] is True


def test_string_format_json_marks_json_and_multiline():
    _, o = to_comfy({"type": "string", "format": "json"})
    assert o["is_json"] is True and o["multiline"] is True


def test_string_x_multiline_extension_enables_multiline():
    _, o = to_comfy({"type": "string", "x-multiline": True})
    assert o["multiline"] is True


def test_string_default_survives():
    _, o = to_comfy({"type": "string", "default": "hello"})
    assert o["default"] == "hello"


# --- array ---------------------------------------------------------------
def test_array_becomes_multiline_json_with_constraints():
    t, o = to_comfy({"type": "array",
                     "minItems": 1, "maxItems": 10, "uniqueItems": True,
                     "items": {"type": "string"}})
    assert t == "STRING"
    assert o["is_json"] is True and o["format"] == "array"
    assert o["min_items"] == 1 and o["max_items"] == 10
    assert o["unique_items"] is True
    assert o["items_type"] == "string"


# --- object / $ref / oneOf ---------------------------------------------
def test_object_becomes_multiline_json():
    t, o = to_comfy({"type": "object",
                     "properties": {"x": {"type": "string"}}})
    assert t == "STRING"
    assert o["multiline"] is True and o["is_json"] is True


def test_oneof_without_type_falls_back_to_json():
    t, o = to_comfy({"oneOf": [{"type": "string"}, {"type": "integer"}]})
    assert t == "STRING"
    assert o["is_json"] is True


def test_null_type_is_advised_as_null_format():
    _, o = to_comfy({"type": "null"})
    assert o["format"] == "null"
