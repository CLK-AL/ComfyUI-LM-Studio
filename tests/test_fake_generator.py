"""Seeded fake-data generator for the mock servers."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node.fake_generator import FakeGenerator, HAVE_FAKER
from comfyui_openapi_node.format_type import FormatType


def test_every_format_type_is_handled():
    gen = FakeGenerator(seed=42)
    for ft in FormatType:
        v = gen.for_format(ft)
        assert isinstance(v, str) and v, ft.name


def test_seed_reproducibility():
    a = FakeGenerator(seed=42)
    b = FakeGenerator(seed=42)
    # Random-driven columns must produce the same value for the same
    # seed. Use TEXT (Lorem-driven) and DATETIME (random-driven).
    for ft in (FormatType.TEXT, FormatType.DATETIME, FormatType.INT32,
               FormatType.EMAIL, FormatType.TEL):
        if HAVE_FAKER:
            assert a.for_format(ft) == b.for_format(ft), ft.name
        else:
            # Without `Faker` the RNG drives most values so seed match still holds.
            assert a.for_format(ft) == b.for_format(ft), ft.name


def test_nextid_is_monotonic():
    gen = FakeGenerator(seed=1)
    ids = [gen.next_id() for _ in range(5)]
    assert ids == [1, 2, 3, 4, 5]


def test_int64_uses_counter():
    gen = FakeGenerator(seed=1)
    a = gen.for_format(FormatType.INT64)
    b = gen.for_format(FormatType.INT64)
    assert int(b) == int(a) + 1


def test_reset_restarts_counter():
    gen = FakeGenerator(seed=1)
    for _ in range(3):
        gen.next_id()
    gen.reset()
    assert gen.next_id() == 1


def test_email_and_url_shape():
    gen = FakeGenerator(seed=7)
    assert "@" in gen.for_format(FormatType.EMAIL)
    assert gen.for_format(FormatType.URL).startswith("http")


def test_geojson_parses_as_valid_json():
    import json
    gen = FakeGenerator(seed=3)
    s = gen.for_format(FormatType.GEOJSON)
    obj = json.loads(s)
    assert obj["type"] == "Point"
    assert len(obj["coordinates"]) == 2


def test_vcard_n_has_five_semicolon_parts():
    gen = FakeGenerator(seed=9)
    s = gen.for_format(FormatType.VCARD_N)
    assert s.count(";") == 4  # "last;first;additional;prefix;suffix"


def test_vcard_adr_has_seven_parts():
    gen = FakeGenerator(seed=9)
    s = gen.for_format(FormatType.VCARD_ADR)
    assert s.count(";") == 6


def test_ical_attendee_is_mailto():
    gen = FakeGenerator(seed=11)
    assert gen.for_format(FormatType.ICAL_ATTENDEE).startswith("mailto:")


def test_uuid_shape():
    gen = FakeGenerator(seed=11)
    s = gen.for_format(FormatType.UUID)
    assert re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", s)


def test_color_shape():
    gen = FakeGenerator(seed=11)
    s = gen.for_format(FormatType.COLOR)
    assert re.match(r"^#[0-9a-f]{6}$", s)


def test_kotlin_side_declares_faker_stack():
    """Kotlin side registers the abstract FakeProvider + datafaker
    implementation. `--faker <name>` picks a provider at runtime."""
    kt = (REPO / "api" / "api.mock.jbang.kt").read_text()
    assert "net.datafaker:datafaker" in kt
    fp = (REPO / "api" / "common" / "FakeProvider.kt").read_text()
    assert "interface FakeProvider" in fp
    assert "nextId" in fp
    assert "FakeProviderFactory" in fp
    df = (REPO / "api" / "common" / "DatafakerProvider.kt").read_text()
    assert "class DatafakerProvider" in df
    assert "net.datafaker.Faker" in df
    assert "AtomicLong" in fp
    assert "override fun generate" in df
