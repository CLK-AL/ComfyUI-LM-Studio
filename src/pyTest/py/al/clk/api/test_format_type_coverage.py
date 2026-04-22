"""Every HtmlInputType and ComfyType value is reachable.

Proves the FormatType catalog's contract: for every UI-side enum
value we claim to support, at least one FormatType row produces it.
Also sanity-checks the reverse — no row uses an enum value that isn't
declared.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.format_type import (
    ComfyType, ComposeWidget, FormatType, HtmlInputType,
    JsonFormat, JsonType,
)


# --- every enum value is used by at least one FormatType row -----------
def test_every_html_input_type_is_mapped():
    used = {ft.value.html_input for ft in FormatType}
    declared = set(HtmlInputType)
    missing = declared - used
    assert not missing, f"HtmlInputType values with no FormatType row: {missing}"


def test_every_comfy_type_is_mapped():
    used = {ft.value.comfy for ft in FormatType}
    declared = set(ComfyType)
    missing = declared - used
    assert not missing, f"ComfyType values with no FormatType row: {missing}"


def test_every_json_type_used_is_declared():
    # The reverse direction: anything a row declares must be part of
    # the JsonType vocabulary (enforced by the type system, but this
    # asserts the value, not the instance).
    for ft in FormatType:
        assert ft.value.json_type in set(JsonType), ft.name


def test_every_compose_widget_used_is_declared():
    for ft in FormatType:
        assert ft.value.composable in set(ComposeWidget), ft.name


def test_every_json_format_used_is_declared():
    for ft in FormatType:
        assert ft.value.json_format in set(JsonFormat), ft.name


# --- proto source of truth is wired through -----------------------------
def test_proto_source_is_present():
    proto = REPO / "api" / "src" / "proto" / "al" / "clk" / "api" / "types.proto"
    assert proto.is_file(), "proto schema missing"
    text = proto.read_text()
    # Every UI-side enum value must also be present in the proto's
    # corresponding enum — this is how Wire / protoc consume it.
    for v in HtmlInputType:
        # proto names are HI_<UPPER_SNAKE> of the Python member name.
        expected = "HI_" + v.name
        assert expected in text, f"missing {expected} in types.proto"
    for v in ComfyType:
        expected = "CY_" + v.name
        assert expected in text, f"missing {expected} in types.proto"
    for v in JsonType:
        expected = "JT_" + v.name
        assert expected in text, f"missing {expected} in types.proto"
    for v in ComposeWidget:
        expected = "CW_" + v.name
        assert expected in text, f"missing {expected} in types.proto"


def test_wire_and_moshi_deps_sourced_into_api_mock():
    kt = (REPO / "api" / "api.mock.jbang.kt").read_text()
    for needle in (
        "com.squareup.wire:wire-runtime-jvm",
        "com.squareup.moshi:moshi",
        "com.squareup.wire:wire-moshi-adapter",
    ):
        assert needle in kt, f"missing dep: {needle}"
