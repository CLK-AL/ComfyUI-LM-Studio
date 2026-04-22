"""API-surface tests for the vCard / iCal layer.

Pairs with `api/src/jvmTest/kotlin/al/clk/api/IcsVcfParserTest.kt`.
The Python side drives `al.clk.api.ics_vcf` (vobject + icalendar →
jCard / jCal) — the same shape the jbang-side `IcsVcfParser` produces
via ical4j + ez-vcard. A third twin lives in `commonTest` (pure
FormatType-bridge assertions) so the same contract is guarded from
three angles: KMP portable, JVM concrete, and Python concrete.
"""
from __future__ import annotations

import json

from al.clk.api import ics_vcf
from al.clk.api.format_type import FormatType


SAMPLE_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//al.clk.api//pyTest//EN
BEGIN:VEVENT
UID:evt-1@example.com
DTSTAMP:20260422T120000Z
DTSTART:20260422T130000Z
DTEND:20260422T140000Z
SUMMARY:pyTest calendar entry
ORGANIZER:mailto:owner@example.com
END:VEVENT
END:VCALENDAR
"""

SAMPLE_VCF = """\
BEGIN:VCARD
VERSION:4.0
FN:Ada Lovelace
N:Lovelace;Ada;Augusta;Hon.;
EMAIL;TYPE=work:ada@example.com
TEL;TYPE=cell:+1 555 0100
ORG:Analytical Engine
END:VCARD
"""


# ---------- jCal (RFC 7265) -------------------------------------------
def test_ics_to_jcal_yields_vcalendar_root():
    jcal = ics_vcf.parse_ical_to_jcal(SAMPLE_ICS)
    # Serialised jCal — first element is always "vcalendar".
    payload = json.dumps(jcal).lower()
    assert "vcalendar" in payload
    assert "vevent" in payload


def test_jcal_to_ics_round_trips_summary():
    jcal = ics_vcf.parse_ical_to_jcal(SAMPLE_ICS)
    back = ics_vcf.jcal_to_ics(jcal)
    assert "BEGIN:VCALENDAR" in back
    assert "SUMMARY:pyTest" in back


# ---------- jCard (RFC 7095) ------------------------------------------
def test_vcf_to_jcard_preserves_fn_and_email():
    jcard = ics_vcf.parse_vcard_to_jcard(SAMPLE_VCF)
    payload = json.dumps(jcard)
    assert "Ada Lovelace" in payload
    assert "ada@example.com" in payload


def test_jcard_to_vcf_round_trips_contact():
    jcard = ics_vcf.parse_vcard_to_jcard(SAMPLE_VCF)
    back = ics_vcf.jcard_to_vcf(jcard)
    assert "BEGIN:VCARD" in back
    assert "FN:Ada Lovelace" in back


# ---------- FormatType bridge contract ---------------------------------
# vCard + iCal FormatType rows must be present on both sides so the
# registry can surface them as typed inputs in a ComfyUI node.
def test_vcard_rows_exist_on_formattype():
    for name in (
        "VCARD_FN", "VCARD_N", "VCARD_EMAIL", "VCARD_TEL",
        "VCARD_ADR", "VCARD_GEO", "VCARD_BDAY", "VCARD_ORG",
        "VCARD_UID", "VCARD_URL",
    ):
        assert hasattr(FormatType, name), f"Python FormatType missing {name}"


def test_ical_rows_exist_on_formattype():
    for name in (
        "ICAL_DTSTART", "ICAL_DTEND", "ICAL_SUMMARY", "ICAL_DESCRIPTION",
        "ICAL_STATUS", "ICAL_CLASS", "ICAL_TRANSP", "ICAL_PRIORITY",
        "ICAL_RRULE", "ICAL_ATTENDEE", "ICAL_ORGANIZER", "ICAL_UID",
        "ICAL_TZID", "ICAL_GEO", "ICAL_RECUR_ID",
    ):
        assert hasattr(FormatType, name), f"Python FormatType missing {name}"


def test_vcard_ical_rows_declare_string_json_type():
    # jCard / jCal both carry textual values over the wire; the
    # registry renders them as typed STRING inputs.
    from al.clk.api.format_type import FormatType, JsonType
    vcard_rows = [ft for ft in FormatType if ft.name.startswith("VCARD_")]
    ical_rows  = [ft for ft in FormatType if ft.name.startswith("ICAL_")]
    assert vcard_rows and ical_rows, "bridge rows missing on Python side"
    for ft in vcard_rows + ical_rows:
        jt = ft.value.json_type
        # INTEGER is allowed for ICAL_PRIORITY / ICAL_SEQUENCE;
        # everything else is STRING.
        assert jt in (JsonType.STRING, JsonType.INTEGER), \
            f"{ft.name}: unexpected json_type {jt}"
