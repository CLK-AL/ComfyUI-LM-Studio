package al.clk.api

import com.fasterxml.jackson.databind.JsonNode
import com.fasterxml.jackson.databind.node.ArrayNode
import com.fasterxml.jackson.databind.node.ObjectNode
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertSame

// JVM-specific guards for the JClass / KClass / PyClass bridge.
// Exercises the Jackson JsonNode pairing that `common/` can't
// reference directly (Kotlin Multiplatform doesn't ship Jackson).
class JClassKClassTest {

    @Test fun jclass_enum_resolves_real_java_classes() {
        assertSame(JClassEnum.STRING,          JClassEnum.fromJClass(java.lang.String::class.java))
        assertSame(JClassEnum.INTEGER,         JClassEnum.fromJClass(java.lang.Integer::class.java))
        assertSame(JClassEnum.LONG,            JClassEnum.fromJClass(java.lang.Long::class.java))
        assertSame(JClassEnum.INSTANT,         JClassEnum.fromJClass(java.time.Instant::class.java))
        assertSame(JClassEnum.LOCAL_DATE,      JClassEnum.fromJClass(java.time.LocalDate::class.java))
        assertSame(JClassEnum.UUID,            JClassEnum.fromJClass(java.util.UUID::class.java))
    }

    @Test fun jackson_jsonnode_entries_resolve_at_runtime() {
        // Real Class refs (no Object::class.java placeholder).
        assertSame(JClassEnum.JSON_NODE,   JClassEnum.fromJClass(JsonNode::class.java))
        assertSame(JClassEnum.OBJECT_NODE, JClassEnum.fromJClass(ObjectNode::class.java))
        assertSame(JClassEnum.ARRAY_NODE,  JClassEnum.fromJClass(ArrayNode::class.java))
    }

    @Test fun kclass_carries_paired_jclass_and_pyclass() {
        // KMP → JVM crosswalk lives in the KClassEnum rows themselves.
        assertSame(JClassEnum.LOCAL_DATE, KClassEnum.LOCAL_DATE.jclass)
        assertSame(JClassEnum.INSTANT,    KClassEnum.INSTANT.jclass)
        assertSame(JClassEnum.ZONE_ID,    KClassEnum.TIME_ZONE.jclass)   // kotlinx → java.time
        assertSame(JClassEnum.OBJECT_NODE, KClassEnum.JSON_OBJECT.jclass)
        assertSame(JClassEnum.ARRAY_NODE,  KClassEnum.JSON_ARRAY.jclass)

        assertSame(PyClassEnum.DATETIME,  KClassEnum.INSTANT.pyclass)
        assertSame(PyClassEnum.ZONE_INFO, KClassEnum.TIME_ZONE.pyclass)
        assertSame(PyClassEnum.DICT,      KClassEnum.JSON_OBJECT.pyclass)
    }

    @Test fun kmp_to_jvm_bridge_unwraps_to_java_class() {
        assertEquals(java.time.Instant::class.java,
                     JClassKClass.kmpToJvm(kotlinx.datetime.Instant::class))
        assertEquals(java.time.LocalDate::class.java,
                     JClassKClass.kmpToJvm(kotlinx.datetime.LocalDate::class))
        assertEquals(java.time.ZoneId::class.java,
                     JClassKClass.kmpToJvm(kotlinx.datetime.TimeZone::class))
    }

    @Test fun jvm_time_aliases_fold_into_datetime_via_formatFor() {
        // LocalDateTime / OffsetDateTime / ZonedDateTime all map to
        // FormatType.DATETIME via the JClassKClass.formatFor fallback.
        assertSame(FormatType.DATETIME,
                   JClassKClass.formatFor(java.time.LocalDateTime::class.java))
        assertSame(FormatType.DATETIME,
                   JClassKClass.formatFor(java.time.OffsetDateTime::class.java))
        assertSame(FormatType.DATETIME,
                   JClassKClass.formatFor(java.time.ZonedDateTime::class.java))
    }

    @Test fun bigint_and_bigdecimal_fold_via_formatFor() {
        assertSame(FormatType.INT64,   JClassKClass.formatFor(java.math.BigInteger::class.java))
        assertSame(FormatType.DOUBLE_, JClassKClass.formatFor(java.math.BigDecimal::class.java))
    }
}
