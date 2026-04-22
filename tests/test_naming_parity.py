"""Cross-implementation parity for the naming convention.

Both Python (`comfyui_openapi_node.naming`) and Kotlin
(`api/common/Naming.kt`) consume `tests/fixtures/naming-cases.json`.
This test exercises the Python side against every case; the Kotlin
compile test (tests/test_jbang_scripts_compile.py) confirms the
Kotlin mirror is included as //SOURCES in api/api.mock.jbang.kt so
the same file is the contract both implementations meet.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FIXTURE = Path(__file__).parent / "fixtures" / "naming-cases.json"

from comfyui_openapi_node.naming import (
    camel, component_name, message_name, node_class, node_display,
    patch_name, pascal, snake, table_name,
)


def _cases():
    return json.loads(FIXTURE.read_text())


def test_snake_cases_match_fixture():
    for src, expected in _cases()["snake"].items():
        assert snake(src) == expected, (src, expected, snake(src))


def test_pascal_cases_match_fixture():
    for src, expected in _cases()["pascal"].items():
        assert pascal(src) == expected, (src, expected, pascal(src))


def test_camel_cases_match_fixture():
    for src, expected in _cases()["camel"].items():
        assert camel(src) == expected, (src, expected, camel(src))


def test_table_name_cases_match_fixture():
    for src, expected in _cases()["table_name"].items():
        assert table_name(src) == expected


def test_component_name_cases_match_fixture():
    for src, expected in _cases()["component_name"].items():
        assert component_name(src) == expected


def test_message_name_cases_match_fixture():
    for row in _cases()["message_name"]:
        got = message_name(row["component"], verb=row["verb"])
        assert got == row["expected"], row


def test_patch_name_cases_match_fixture():
    for src, expected in _cases()["patch_name"].items():
        assert patch_name(src) == expected


def test_node_class_cases_match_fixture():
    for row in _cases()["node_class"]:
        assert node_class(row["api"], row["op"]) == row["expected"]


def test_node_display_cases_match_fixture():
    for row in _cases()["node_display"]:
        assert node_display(row["api"], row["op"]) == row["expected"]


def test_kotlin_mirror_is_sourced_into_api_mock():
    # Parity contract: api/api.mock.jbang.kt includes the shared Kotlin
    # naming file so `jbang info classpath` produces a binary that
    # ships the mirror next to the Python side.
    kt = (REPO / "api" / "api.mock.jbang.kt").read_text()
    assert "common/Naming.kt" in kt, "shared naming Kotlin file must be //SOURCES-included"
    assert "common/ComponentTables.kt" in kt
