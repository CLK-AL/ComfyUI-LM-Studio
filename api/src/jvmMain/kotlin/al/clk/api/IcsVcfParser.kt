package al.clk.api

// vCard/iCal string|file → jCard/jCal round-trip.
//
// Uses the two canonical JVM libraries (Wire handles the binary /
// proto side; these handle the text formats):
//
//   ical4j (org.mnode.ical4j:ical4j:4.0.5)
//       - Parse .ics text/files into `net.fortuna.ical4j.model.Calendar`.
//       - Emit jCal (RFC 7265) via the `JCalOutputter` / `JCalBuilder`.
//
//   ez-vcard (com.googlecode.ez-vcard:ez-vcard:0.12.1)
//       - Parse .vcf text/files into `ezvcard.VCard`.
//       - Emit jCard (RFC 7095) via `Ezvcard.writeJson(...)`.
//
// The functions below are thin, stable call sites — the Python
// mirror at `comfyui_openapi_node/ics_vcf.py` uses a dependency-free
// line parser because the pure-Python ecosystem doesn't have a
// maintained jCard writer.
//
// NOTE: fully wired to real types in the Compose Multiplatform
// module (commonMain). Here we keep the signatures and a skeleton so
// //SOURCES consumption + the parity assertion in
// tests/test_jcard_jcal.py work today.

object IcsVcfParser {

    /** Parse an iCalendar string (`.ics` contents) → jCal JSON text (RFC 7265).
     *
     * Implementation sketch (follow-up wiring into ical4j):
     *
     *     val cal = CalendarBuilder().build(StringReader(ics))
     *     val out = StringWriter()
     *     JCalOutputter().output(cal, out)
     *     return out.toString()
     */
    fun icsToJcal(ics: String): String {
        TODO("wire to ical4j CalendarBuilder + JCalOutputter")
    }

    /** Parse a vCard string (`.vcf` contents) → jCard JSON text (RFC 7095).
     *
     * Implementation sketch (follow-up wiring into ez-vcard):
     *
     *     val vc = Ezvcard.parse(vcf).all()
     *     return Ezvcard.writeJson(vc).go()
     */
    fun vcfToJcard(vcf: String): String {
        TODO("wire to ez-vcard Ezvcard.parse + Ezvcard.writeJson")
    }

    /** Reverse: jCal JSON → `.ics` text. */
    fun jcalToIcs(jcal: String): String {
        TODO("wire to ical4j JCalBuilder + CalendarOutputter")
    }

    /** Reverse: jCard JSON → `.vcf` text. */
    fun jcardToVcf(jcard: String): String {
        TODO("wire to ez-vcard Ezvcard.parseJson + Ezvcard.write")
    }
}
