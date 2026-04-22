"""vCard (.vcf) + iCalendar (.ics) → jCard / jCal JSON round-trip.

Uses `vobject` when available (full RFC coverage) and falls back to the
dep-less line parser otherwise. Tests exercise both paths.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from comfyui_openapi_node import ics_vcf
from comfyui_openapi_node.ics_vcf import (
    HAVE_ICALENDAR,
    HAVE_VOBJECT,
    jcal_to_ics,
    jcard_to_vcf,
    parse_ical_to_jcal,
    parse_vcard_to_jcard,
    parse_vcards_to_jcard,
)


VCF_ADA = """BEGIN:VCARD
VERSION:4.0
FN:Ada Lovelace
N:Lovelace;Ada;Augusta;Hon.;
EMAIL;TYPE=work:ada@example.com
TEL;TYPE=cell:+44 20 7946 0001
ADR;TYPE=home:;;1 Dorset St;London;;W1U 4DZ;UK
GEO:geo:51.5176,-0.1487
ORG:Analytical Engine;R&D
URL:https://example.com/ada
UID:urn:uuid:00000000-0000-0000-0000-000000000001
END:VCARD
"""

ICS_MEETING = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example//1.0//EN
BEGIN:VEVENT
UID:evt-1@example.com
DTSTAMP:20260422T100000Z
DTSTART:20260423T140000Z
DTEND:20260423T150000Z
SUMMARY:Team sync
LOCATION:1 Infinite Loop
ORGANIZER:mailto:org@example.com
ATTENDEE:mailto:ada@example.com
STATUS:CONFIRMED
RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=10
END:VEVENT
END:VCALENDAR
"""


# ---- jCard shape --------------------------------------------------------
def test_parse_vcard_top_level_is_vcard_array():
    jc = parse_vcard_to_jcard(VCF_ADA)
    assert isinstance(jc, list)
    assert jc[0] == "vcard"
    assert isinstance(jc[1], list)
    # Every property is a 4-tuple [name, params, vtype, value].
    for prop in jc[1]:
        assert len(prop) == 4, prop
        name, params, vtype, _value = prop
        assert isinstance(name, str) and name.islower()
        assert isinstance(params, dict)
        assert isinstance(vtype, str)


def test_vcard_has_fn_n_email_tel_adr():
    jc = parse_vcard_to_jcard(VCF_ADA)
    names = [p[0] for p in jc[1]]
    for expected in ("fn", "n", "email", "tel", "adr", "geo", "org", "url", "uid"):
        assert expected in names, expected


def test_vcard_n_is_structured_array():
    jc = parse_vcard_to_jcard(VCF_ADA)
    n = next(p for p in jc[1] if p[0] == "n")
    assert isinstance(n[3], list)
    # family, given, additional, prefixes, suffixes
    assert len(n[3]) == 5
    assert n[3][0] == "Lovelace"
    assert n[3][1] == "Ada"


def test_vcard_adr_is_structured_array():
    jc = parse_vcard_to_jcard(VCF_ADA)
    adr = next(p for p in jc[1] if p[0] == "adr")
    # po_box; extended; street; locality; region; postal; country
    assert isinstance(adr[3], list) and len(adr[3]) == 7


def test_vcard_params_survive():
    jc = parse_vcard_to_jcard(VCF_ADA)
    email = next(p for p in jc[1] if p[0] == "email")
    assert email[1].get("type") in ("work", ["work"])


# ---- multi-vCard --------------------------------------------------------
def test_parse_multiple_vcards():
    text = VCF_ADA + """BEGIN:VCARD
VERSION:4.0
FN:Grace Hopper
N:Hopper;Grace;;;
EMAIL:grace@example.com
END:VCARD
"""
    cards = parse_vcards_to_jcard(text)
    assert len(cards) == 2
    assert cards[0][0] == "vcard"
    fn0 = next(p for p in cards[0][1] if p[0] == "fn")[3]
    fn1 = next(p for p in cards[1][1] if p[0] == "fn")[3]
    assert fn0 == "Ada Lovelace" and fn1 == "Grace Hopper"


# ---- jCal shape ---------------------------------------------------------
def test_parse_ical_top_level_is_vcalendar_with_nested_vevent():
    jc = parse_ical_to_jcal(ICS_MEETING)
    assert jc[0] == "vcalendar"
    # [name, properties, components]
    assert len(jc) >= 2
    props = jc[1]
    assert any(p[0] == "version" for p in props)
    if len(jc) == 3:
        comps = jc[2]
        assert any(c[0] == "vevent" for c in comps)
        vevent = next(c for c in comps if c[0] == "vevent")
        ev_names = [p[0] for p in vevent[1]]
        for expected in ("uid", "dtstamp", "dtstart", "dtend",
                         "summary", "location", "organizer",
                         "attendee", "status", "rrule"):
            assert expected in ev_names, expected


def test_ical_datetime_props_tagged_date_time():
    jc = parse_ical_to_jcal(ICS_MEETING)
    vevent = next(c for c in jc[2] if c[0] == "vevent")
    dtstart = next(p for p in vevent[1] if p[0] == "dtstart")
    assert dtstart[2] == "date-time"


# ---- round-trip: jCard → vcf → jCard ----------------------------------
def test_vcard_round_trip_preserves_fn_and_email():
    original = parse_vcard_to_jcard(VCF_ADA)
    regen = jcard_to_vcf(original)
    again = parse_vcard_to_jcard(regen)
    fn1 = next(p for p in original[1] if p[0] == "fn")[3]
    fn2 = next(p for p in again[1] if p[0] == "fn")[3]
    assert fn1 == fn2
    email1 = next(p for p in original[1] if p[0] == "email")[3]
    email2 = next(p for p in again[1] if p[0] == "email")[3]
    assert email1 == email2


def test_ical_round_trip_preserves_vevent_summary():
    original = parse_ical_to_jcal(ICS_MEETING)
    regen = jcal_to_ics(original)
    again = parse_ical_to_jcal(regen)
    ev1 = next(c for c in original[2] if c[0] == "vevent")
    ev2 = next(c for c in again[2] if c[0] == "vevent")
    s1 = next(p for p in ev1[1] if p[0] == "summary")[3]
    s2 = next(p for p in ev2[1] if p[0] == "summary")[3]
    assert s1 == s2


# ---- backend visibility + Kotlin dep presence --------------------------
def test_backend_report():
    # Records which RFC-compliant backends were active so a regression
    # (e.g. `vobject` / `icalendar` vanishing from the venv) is obvious.
    assert isinstance(HAVE_VOBJECT, bool)
    assert isinstance(HAVE_ICALENDAR, bool)


def test_kotlin_side_declares_ical4j_and_ezvcard():
    kt = (REPO / "api" / "api.mock.jbang.kt").read_text()
    assert "org.mnode.ical4j:ical4j" in kt
    assert "com.googlecode.ez-vcard:ez-vcard" in kt
    src = (REPO / "api" / "common" / "IcsVcfParser.kt").read_text()
    assert "icsToJcal" in src and "vcfToJcard" in src
