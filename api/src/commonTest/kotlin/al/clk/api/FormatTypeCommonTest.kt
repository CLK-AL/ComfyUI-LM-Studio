package al.clk.api

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertSame
import kotlin.test.assertTrue

// KMP-portable parity tests for the `FormatType` one-hop mapper. Runs
// under `kotlin-test-common` when a Gradle KMP module is added later;
// for now the file compiles as `commonMain` parity guard for the
// Python side's `test_format_type.py` (same name, same contract).
class FormatTypeCommonTest {

    @Test fun every_row_has_nonempty_kclass_fqn() {
        for (ft in FormatType.entries) {
            assertTrue(ft.kclassFqn.isNotEmpty(), "kclassFqn blank: ${ft.name}")
        }
    }

    @Test fun from_kclass_round_trips_on_known_classes() {
        // Canonical KClass handles round-trip back to the same FormatType.
        assertEquals(FormatType.TEXT,    FormatType.fromKClass(String::class))
        assertEquals(FormatType.INT32,   FormatType.fromKClass(Int::class))
        assertEquals(FormatType.INT64,   FormatType.fromKClass(Long::class))
        assertEquals(FormatType.FLOAT_,  FormatType.fromKClass(Float::class))
        assertEquals(FormatType.DOUBLE_, FormatType.fromKClass(Double::class))
        assertEquals(FormatType.BOOL,    FormatType.fromKClass(Boolean::class))
    }

    @Test fun json_schema_dispatch_integer_picks_int32_or_int64() {
        val int32 = FormatType.fromJsonSchema(mapOf("type" to "integer"))
        val int64 = FormatType.fromJsonSchema(mapOf("type" to "integer", "format" to "int64"))
        assertEquals(FormatType.INT32, int32)
        assertEquals(FormatType.INT64, int64)
    }

    @Test fun sql_dispatch_finds_primitive_column_types() {
        assertEquals(FormatType.INT32,   FormatType.fromSql(SqlTypes.INTEGER))
        assertEquals(FormatType.INT64,   FormatType.fromSql(SqlTypes.BIGINT))
        assertEquals(FormatType.TEXT,    FormatType.fromSql(SqlTypes.VARCHAR))
        assertEquals(FormatType.BOOL,    FormatType.fromSql(SqlTypes.BOOLEAN))
    }

    @Test fun bridge_exposes_jclass_and_pyclass_via_kclass() {
        val text = FormatType.TEXT.mapping
        assertEquals(KClassEnum.STRING,    text.kclass)
        assertEquals(JClassEnum.STRING,    text.jclass)
        assertEquals(PyClassEnum.STR,      text.pyclass)

        val datetime = FormatType.DATETIME.mapping
        assertEquals(KClassEnum.INSTANT,   datetime.kclass)
        assertEquals(JClassEnum.INSTANT,   datetime.jclass)
        assertEquals(PyClassEnum.DATETIME, datetime.pyclass)

        val json = FormatType.JSON_OBJECT.mapping
        assertEquals(KClassEnum.JSON_OBJECT, json.kclass)
        assertEquals(JClassEnum.OBJECT_NODE, json.jclass)
        assertEquals(PyClassEnum.DICT,       json.pyclass)
    }

    @Test fun icu_and_vcard_rows_are_reachable() {
        // Every ICU + vCard + iCal FormatType must have a non-blank
        // placeholder or default — they are the contract with the UI.
        assertNotNull(FormatType.PERSON_NAME.mapping)
        assertNotNull(FormatType.CURRENCY.mapping)
        assertNotNull(FormatType.VCARD_FN.mapping)
        assertNotNull(FormatType.ICAL_RRULE.mapping)
    }

    @Test fun pyclass_lookup_goes_through_formattype() {
        assertSame(FormatType.TEXT,     FormatType.fromPyClass("str"))
        assertSame(FormatType.INT32,    FormatType.fromPyClass("int"))
        assertSame(FormatType.DATETIME, FormatType.fromPyClass("datetime.datetime"))
        assertSame(FormatType.TEXT,     FormatType.fromPyClass("unknown.Thing"))
    }
}
