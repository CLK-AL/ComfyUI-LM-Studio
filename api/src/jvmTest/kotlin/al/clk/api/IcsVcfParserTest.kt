package al.clk.api

import kotlin.test.Test
import kotlin.test.assertTrue

// JVM-only — `IcsVcfParser` wraps `net.fortuna.ical4j` (ical4j) and
// `ezvcard.Ezvcard` (ez-vcard); neither is KMP. These tests exercise
// the signatures the bridge promises to expose. Heavy end-to-end
// parsing is covered on the Python side (vobject + icalendar) so the
// JVM side stays a thin formatter.

private val SAMPLE_ICS = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//al.clk.api//jvmTest//EN
BEGIN:VEVENT
UID:evt-1@example.com
DTSTAMP:20260422T120000Z
DTSTART:20260422T130000Z
DTEND:20260422T140000Z
SUMMARY:jvmTest calendar entry
ORGANIZER:mailto:owner@example.com
END:VEVENT
END:VCALENDAR
""".trimIndent()

private val SAMPLE_VCF = """
BEGIN:VCARD
VERSION:4.0
FN:Ada Lovelace
N:Lovelace;Ada;Augusta;Hon.;
EMAIL;TYPE=work:ada@example.com
TEL;TYPE=cell:+1 555 0100
ORG:Analytical Engine
END:VCARD
""".trimIndent()

class IcsVcfParserTest {

    @Test fun ics_to_jcal_produces_vcalendar_root() {
        val out = IcsVcfParser.icsToJcal(SAMPLE_ICS)
        // Output is jCal — RFC 7265 — a JsonElement tree whose first
        // element (component name) is "vcalendar".
        assertTrue("vcalendar" in out.toString().lowercase(),
                   "jCal output should mention the vcalendar root")
        assertTrue("vevent" in out.toString().lowercase(),
                   "jCal output should carry the VEVENT sub-component")
    }

    @Test fun vcf_to_jcard_preserves_fn_and_email() {
        val out = IcsVcfParser.vcfToJcard(SAMPLE_VCF)
        val str = out.toString()
        assertTrue("Ada Lovelace" in str, "FN should round-trip")
        assertTrue("ada@example.com" in str, "EMAIL should round-trip")
    }

    @Test fun jcal_to_ics_round_trips_component_name() {
        // Parse then render: the summary line survives.
        val jcal = IcsVcfParser.icsToJcal(SAMPLE_ICS)
        val back = IcsVcfParser.jcalToIcs(jcal)
        assertTrue("BEGIN:VCALENDAR" in back && "SUMMARY:jvmTest" in back,
                   "round-trip must preserve VCALENDAR + SUMMARY")
    }

    @Test fun jcard_to_vcf_round_trips_contact() {
        val jcard = IcsVcfParser.vcfToJcard(SAMPLE_VCF)
        val back = IcsVcfParser.jcardToVcf(jcard)
        assertTrue("BEGIN:VCARD" in back && "FN:Ada Lovelace" in back,
                   "round-trip must preserve VCARD + FN")
    }
}
