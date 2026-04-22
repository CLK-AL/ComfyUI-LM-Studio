"""Named-group regex + template patterns on FormatType.

Compound formats (ISO date, ISO time, ISO date-time, ISO month, ISO
week, ISO duration, UTC offset) decompose into atomic FormatType
parts. parse() returns the named-group dict; render() rebuilds the
canonical string from the parts.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node.format_type import (
    FormatType, FormatPattern, PATTERNS,
)


# --- pattern presence ---------------------------------------------------
def test_complex_formats_have_patterns():
    for ft in (FormatType.DATE, FormatType.TIME, FormatType.DATETIME,
               FormatType.MONTH, FormatType.WEEK, FormatType.DURATION,
               FormatType.OFFSET):
        assert ft.pattern() is not None, ft.name


def test_simple_formats_have_no_pattern():
    for ft in (FormatType.TEXT, FormatType.EMAIL, FormatType.INT32,
               FormatType.BOOL, FormatType.JSON_OBJECT):
        assert ft.pattern() is None, ft.name


# --- named-group parts reference real FormatTypes -----------------------
def test_pattern_parts_name_real_format_types():
    valid = {ft.name for ft in FormatType}
    for ft, p in PATTERNS.items():
        for group, ref in p.parts.items():
            assert ref in valid, (ft.name, group, ref)


# --- parse: ISO date-time ----------------------------------------------
def test_parse_iso_datetime_full():
    parts = FormatType.DATETIME.parse("2026-04-22T12:34:56.789+02:00")
    assert parts["year"]          == "2026"
    assert parts["month_of_year"] == "04"
    assert parts["day"]           == "22"
    assert parts["hour"]          == "12"
    assert parts["minute"]        == "34"
    assert parts["second"]        == "56"
    assert parts["millisecond"]   == "789"
    assert parts["offset"]        == "+02:00"


def test_parse_iso_datetime_no_offset():
    parts = FormatType.DATETIME.parse("2026-04-22T12:34:56")
    assert parts["offset"]      == ""
    assert parts["millisecond"] == ""


def test_parse_iso_datetime_z():
    parts = FormatType.DATETIME.parse("2026-04-22T12:34:56Z")
    assert parts["offset"] == "Z"


def test_parse_returns_none_on_mismatch():
    assert FormatType.DATETIME.parse("not a date") is None
    assert FormatType.DATE.parse("2026/04/22") is None


# --- parse: other ISO formats ------------------------------------------
def test_parse_iso_date():
    parts = FormatType.DATE.parse("2026-04-22")
    assert parts == {"year": "2026", "month_of_year": "04", "day": "22"}


def test_parse_iso_time():
    parts = FormatType.TIME.parse("12:34:56.789")
    assert parts["hour"]        == "12"
    assert parts["minute"]      == "34"
    assert parts["second"]      == "56"
    assert parts["millisecond"] == "789"


def test_parse_iso_month():
    parts = FormatType.MONTH.parse("2026-04")
    assert parts == {"year": "2026", "month_of_year": "04"}


def test_parse_iso_week():
    parts = FormatType.WEEK.parse("2026-W17")
    assert parts == {"year": "2026", "iso_week_num": "17"}


def test_parse_iso_duration():
    parts = FormatType.DURATION.parse("P1Y2M3DT4H5M6S")
    assert parts == {
        "year": "1", "month_of_year": "2", "day": "3",
        "hour": "4", "minute": "5", "second": "6",
    }


def test_parse_offset_utc_z():
    parts = FormatType.OFFSET.parse("Z")
    # Z form leaves sign/hour/minute as "" since they're inside the
    # alternation that didn't fire.
    assert parts is not None
    assert parts.get("sign", "") == ""


def test_parse_offset_signed():
    parts = FormatType.OFFSET.parse("+02:30")
    assert parts == {"sign": "+", "hour": "02", "minute": "30"}


# --- render: round-trip -------------------------------------------------
def test_render_iso_datetime_round_trip():
    rendered = FormatType.DATETIME.render({
        "year": 2026, "month_of_year": 4, "day": 22,
        "hour": 12, "minute": 34, "second": 56,
        "millisecond": "", "offset": "Z",
    })
    parts = FormatType.DATETIME.parse(rendered)
    assert parts["year"]   == "2026"
    assert parts["month_of_year"] == "04"
    assert parts["day"]    == "22"
    assert parts["hour"]   == "12"
    assert parts["offset"] == "Z"


def test_render_iso_date():
    s = FormatType.DATE.render({"year": 2026, "month_of_year": 4, "day": 22})
    assert s == "2026-04-22"


def test_render_iso_month_pads_single_digit():
    s = FormatType.MONTH.render({"year": 1999, "month_of_year": 1})
    assert s == "1999-01"


# --- parts → atomic FormatType ----------------------------------------
def test_year_part_is_year_format_type():
    p = FormatType.DATETIME.pattern()
    assert p.parts["year"] == "YEAR"
    # The corresponding atomic FormatType actually exists.
    assert FormatType[p.parts["year"]].name == "YEAR"


def test_every_pattern_part_resolves_to_a_format_type():
    for ft, p in PATTERNS.items():
        for group, ref in p.parts.items():
            FormatType[ref]   # would raise KeyError if missing
