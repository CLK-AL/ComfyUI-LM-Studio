"""The FormatType 5-way bridge — JSON Schema ↔ SQL ↔ Kotlin KClass
↔ Compose ↔ HTML ↔ ComfyUI. Parity-tested against a shared fixture
(the Kotlin mirror in api/common/FormatType.kt reads the same file)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

FIXTURE = Path(__file__).parent / "fixtures" / "format-type-bridge.json"

from comfyui_openapi_node.format_type import FormatType


def _cases():
    return json.loads(FIXTURE.read_text())


def test_every_enum_row_matches_fixture():
    data = _cases()
    by_name = {row["name"]: row for row in data["rows"]}
    # Every fixture row has a matching enum member — nothing missing, nothing extra.
    fixture_names = set(by_name)
    enum_names    = {m.name for m in FormatType}
    assert fixture_names == enum_names, (
        f"fixture vs enum mismatch — "
        f"missing in enum: {fixture_names - enum_names}; "
        f"missing in fixture: {enum_names - fixture_names}"
    )
    for ft in FormatType:
        row = by_name[ft.name]
        m = ft.value
        assert m.json_type         == row["json_type"],   ft.name
        assert m.json_format       == row["json_format"], ft.name
        # sql_type is a real SqlTypes enum — compare by name + int code
        # so the fixture stays human-readable while the contract is
        # typed.
        assert m.sql_type.name     == row["sql_type"],    ft.name
        assert m.sql_type.value    == row["sql_type_code"], ft.name
        assert m.kclass            == row["kclass"],      ft.name
        assert m.html_input        == row["html_input"],  ft.name
        assert m.comfy             == row["comfy"],       ft.name


def test_json_schema_dispatch_matches_fixture():
    for case in _cases()["json_schema_dispatch"]:
        got = FormatType.from_json_schema(case["schema"])
        assert got.name == case["expected"], case


def test_sql_dispatch_matches_fixture():
    for case in _cases()["sql_dispatch"]:
        got = FormatType.from_sql(case["sql"])
        assert got.name == case["expected"], case


def test_kotlin_mirror_is_sourced():
    kt = (REPO / "api" / "api.mock.jbang.kt").read_text()
    assert "common/FormatType.kt" in kt
    assert "common/SqlTypes.kt" in kt
    mirror = (REPO / "api" / "common" / "FormatType.kt").read_text()
    sql_kt = (REPO / "api" / "common" / "SqlTypes.kt").read_text()
    # Canary strings — the Kt side now uses real class references
    # instead of FQN strings, so we look for the class tokens.
    for needle in (
        "Long::class",
        "LocalDate::class",
        "DatePicker",
        "datetime-local",
        "JsonObject::class",
        "SqlTypes.VARCHAR",
        "SqlTypes.BIGINT",
    ):
        assert needle in mirror, needle
    # SqlTypes enum canaries.
    assert "enum class SqlTypes" in sql_kt
    assert "BIGINT(-5)" in sql_kt
    assert "VARCHAR(12)" in sql_kt


def test_compose_widget_per_row_is_nonempty():
    for ft in FormatType:
        assert ft.value.composable, ft.name


def test_placeholder_present_where_expected():
    assert FormatType.EMAIL.value.placeholder.startswith("user@")
    assert FormatType.DATE.value.placeholder.startswith("YYYY")
    assert FormatType.UUID.value.placeholder.startswith("00000000")
    assert FormatType.GEOJSON.value.placeholder.startswith('{"type"')
