// JClass / KClass bridge — closed-set enums over the JVM classes the
// FormatType bridge actually touches.
//
// Open `KClass<*>` / `Class<*>` types on `FormatMapping` are expressive
// but hard to validate across parity tests. These two enums enumerate
// the *supported* types so a JDBC column, Kotlin reflection handle,
// or Java reflection handle can all resolve into the same slot.

import kotlin.reflect.KClass
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.datetime.TimeZone
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject

/** Closed set of Python classes the bridge recognises. Mirrors
 *  `comfyui_openapi_node/format_type.py` `PyClassEnum`. */
enum class PyClassEnum(val fqn: String) {
    STR           ("str"),
    INT           ("int"),
    FLOAT         ("float"),
    BOOL          ("bool"),
    BYTES         ("bytes"),
    BYTEARRAY_    ("bytearray"),
    LIST          ("list"),
    DICT          ("dict"),
    TUPLE         ("tuple"),
    SET           ("set"),
    DATE          ("datetime.date"),
    TIME          ("datetime.time"),
    DATETIME      ("datetime.datetime"),
    TIMEDELTA     ("datetime.timedelta"),
    TZINFO        ("datetime.tzinfo"),
    ZONE_INFO     ("zoneinfo.ZoneInfo"),
    UUID          ("uuid.UUID"),
    DECIMAL       ("decimal.Decimal"),
    FRACTION      ("fractions.Fraction"),
    PATH          ("pathlib.Path"),
    URL           ("urllib.parse.ParseResult"),
    IPV4_ADDRESS  ("ipaddress.IPv4Address"),
    IPV6_ADDRESS  ("ipaddress.IPv6Address");

    companion object {
        fun fromFqn(fqn: String): PyClassEnum? =
            entries.firstOrNull { it.fqn == fqn }
    }
}

/** Closed set of Kotlin KClasses referenced by FormatType rows.
 *  Each row carries the paired [JClassEnum] and [PyClassEnum] so a
 *  single `FormatMapping.kclass: KClassEnum` gives the UI / JDBC /
 *  Python-bridge sides everything they need.
 *
 *  KMP → JVM crosswalk (readable in the rows below):
 *  ```
 *    kotlinx.datetime.LocalDate            → java.time.LocalDate
 *    kotlinx.datetime.LocalTime            → java.time.LocalTime
 *    kotlinx.datetime.Instant              → java.time.Instant
 *    kotlinx.datetime.TimeZone             → java.time.ZoneId
 *    kotlin.time.Duration                  → java.time.Duration
 *    kotlinx.serialization.json.JsonObject → com.fasterxml.jackson.databind.node.ObjectNode
 *    kotlinx.serialization.json.JsonArray  → com.fasterxml.jackson.databind.node.ArrayNode
 *  ```
 *  `common/` code stays KMP-portable (kotlinx), while the Spring JDBC /
 *  WireMock / Jackson handlers on the JVM path pick up the paired
 *  `JClassEnum` value via `kclass.jclass`. */
enum class KClassEnum(
    val kclass: KClass<*>,
    val fqn: String,
    val jclass: JClassEnum,
    val pyclass: PyClassEnum,
) {
    STRING    (String::class,    "kotlin.String",                         JClassEnum.STRING,    PyClassEnum.STR),
    INT       (Int::class,       "kotlin.Int",                            JClassEnum.INTEGER,   PyClassEnum.INT),
    LONG      (Long::class,      "kotlin.Long",                           JClassEnum.LONG,      PyClassEnum.INT),
    FLOAT     (Float::class,     "kotlin.Float",                          JClassEnum.FLOAT,     PyClassEnum.FLOAT),
    DOUBLE    (Double::class,    "kotlin.Double",                         JClassEnum.DOUBLE,    PyClassEnum.FLOAT),
    BOOLEAN   (Boolean::class,   "kotlin.Boolean",                        JClassEnum.BOOLEAN,   PyClassEnum.BOOL),
    BYTE_ARRAY(ByteArray::class, "kotlin.ByteArray",                      JClassEnum.BYTE_ARRAY,PyClassEnum.BYTES),
    LIST      (List::class,      "kotlin.collections.List",               JClassEnum.STRING,    PyClassEnum.LIST),
    LOCAL_DATE(LocalDate::class, "kotlinx.datetime.LocalDate",            JClassEnum.LOCAL_DATE,PyClassEnum.DATE),
    LOCAL_TIME(LocalTime::class, "kotlinx.datetime.LocalTime",            JClassEnum.LOCAL_TIME,PyClassEnum.TIME),
    INSTANT   (Instant::class,   "kotlinx.datetime.Instant",              JClassEnum.INSTANT,   PyClassEnum.DATETIME),
    TIME_ZONE (TimeZone::class,  "kotlinx.datetime.TimeZone",             JClassEnum.ZONE_ID,   PyClassEnum.ZONE_INFO),
    DURATION  (kotlin.time.Duration::class, "kotlin.time.Duration",       JClassEnum.DURATION,  PyClassEnum.TIMEDELTA),
    JSON_OBJECT(JsonObject::class,"kotlinx.serialization.json.JsonObject",JClassEnum.OBJECT_NODE,PyClassEnum.DICT),
    JSON_ARRAY (JsonArray::class, "kotlinx.serialization.json.JsonArray", JClassEnum.ARRAY_NODE, PyClassEnum.LIST);

    companion object {
        fun fromKClass(kcls: KClass<*>): KClassEnum? =
            entries.firstOrNull { it.kclass == kcls }
        fun fromFqn(fqn: String): KClassEnum? =
            entries.firstOrNull { it.fqn == fqn }
    }
}

/** Closed set of Java Classes we translate to FormatType. JDBC and
 *  other Java reflection-driven call sites hand us `Class<*>` handles,
 *  not `KClass<*>` — this enum lists the ones we recognise. */
/** Closed set of Java `Class<*>` handles FormatType rows resolve to.
 *  JSON entries resolve to Jackson's tree (`JsonNode` / `ObjectNode`
 *  / `ArrayNode` — `com.fasterxml.jackson.databind`), the idiomatic
 *  JVM JSON shape. Kotlin `common/` code stays KMP-portable by
 *  holding `kotlinx.serialization.json.JsonObject` / `JsonArray` on
 *  the KClass side; the paired JClassEnum value is how JVM-only
 *  consumers (Spring JDBC, Jackson-native handlers) materialise the
 *  tree at runtime. Jackson is optional — omit the dep and the FQN
 *  strings still work, but `Class.forName` / reflection lookups will
 *  of course fail until the jar is on the classpath. */
enum class JClassEnum(val jclass: Class<*>, val fqn: String) {
    STRING         (java.lang.String::class.java,                           "java.lang.String"),
    INTEGER        (java.lang.Integer::class.java,                          "java.lang.Integer"),
    LONG           (java.lang.Long::class.java,                             "java.lang.Long"),
    FLOAT          (java.lang.Float::class.java,                            "java.lang.Float"),
    DOUBLE         (java.lang.Double::class.java,                           "java.lang.Double"),
    BOOLEAN        (java.lang.Boolean::class.java,                          "java.lang.Boolean"),
    BIG_INTEGER    (java.math.BigInteger::class.java,                       "java.math.BigInteger"),
    BIG_DECIMAL    (java.math.BigDecimal::class.java,                       "java.math.BigDecimal"),
    BYTE_ARRAY     (ByteArray::class.java,                                  "byte[]"),
    LOCAL_DATE     (java.time.LocalDate::class.java,                        "java.time.LocalDate"),
    LOCAL_TIME     (java.time.LocalTime::class.java,                        "java.time.LocalTime"),
    LOCAL_DATETIME (java.time.LocalDateTime::class.java,                    "java.time.LocalDateTime"),
    INSTANT        (java.time.Instant::class.java,                          "java.time.Instant"),
    OFFSET_DATETIME(java.time.OffsetDateTime::class.java,                   "java.time.OffsetDateTime"),
    ZONED_DATETIME (java.time.ZonedDateTime::class.java,                    "java.time.ZonedDateTime"),
    ZONE_ID        (java.time.ZoneId::class.java,                           "java.time.ZoneId"),
    DURATION       (java.time.Duration::class.java,                         "java.time.Duration"),
    UUID           (java.util.UUID::class.java,                             "java.util.UUID"),
    URI            (java.net.URI::class.java,                               "java.net.URI"),
    URL            (java.net.URL::class.java,                               "java.net.URL"),
    // Jackson JSON tree (JVM JSON lib). `ObjectNode` / `ArrayNode`
    // extend `JsonNode`; kept as three distinct entries so the bridge
    // lands on the narrowest type available.
    JSON_NODE      (com.fasterxml.jackson.databind.JsonNode::class.java,    "com.fasterxml.jackson.databind.JsonNode"),
    OBJECT_NODE    (com.fasterxml.jackson.databind.node.ObjectNode::class.java, "com.fasterxml.jackson.databind.node.ObjectNode"),
    ARRAY_NODE     (com.fasterxml.jackson.databind.node.ArrayNode::class.java,  "com.fasterxml.jackson.databind.node.ArrayNode");

    companion object {
        fun fromJClass(jcls: Class<*>): JClassEnum? =
            entries.firstOrNull { it.jclass == jcls }
        fun fromFqn(fqn: String): JClassEnum? =
            entries.firstOrNull { it.fqn == fqn }
    }
}

/** Bridge utility. `FormatType` itself is the mapper — every row
 *  carries its KClassEnum (which in turn carries its JClassEnum and
 *  PyClassEnum sibling), so any language-class handle resolves via
 *  `FormatType.fromXxx(...)` in one hop. The helpers here are thin
 *  conveniences + aliases that map non-canonical reflection handles
 *  (`LocalDateTime`, `OffsetDateTime`, `BigInteger`, `URI`…) onto
 *  their FormatType sibling. */
object JClassKClass {
    fun toJClass(kcls: KClass<*>): Class<*> = kcls.java
    fun toKClass(jcls: Class<*>): KClass<*> = jcls.kotlin

    fun formatFor(kcls: KClass<*>): FormatType = FormatType.fromKClass(kcls)

    /** `Class<*>` → `FormatType`, via FormatType's JClassEnum bridge.
     *  Aliases outside the direct KClass↔JClass pairing fall through
     *  to explicit targets (LocalDateTime/OffsetDateTime/ZonedDateTime
     *  → DATETIME, BigInteger → INT64, URI → URL, …). */
    fun formatFor(jcls: Class<*>): FormatType {
        val je = JClassEnum.fromJClass(jcls) ?: return FormatType.fromKClass(jcls.kotlin)
        return when (je) {
            JClassEnum.LOCAL_DATETIME,
            JClassEnum.OFFSET_DATETIME,
            JClassEnum.ZONED_DATETIME  -> FormatType.DATETIME
            JClassEnum.BIG_INTEGER     -> FormatType.INT64
            JClassEnum.BIG_DECIMAL     -> FormatType.DOUBLE_
            JClassEnum.URI             -> FormatType.URL
            else                       -> FormatType.fromJClassEnum(je)
        }
    }

    /** Python FQN → FormatType. FormatType bridges via PyClassEnum. */
    fun formatForPyClass(fqn: String): FormatType = FormatType.fromPyClass(fqn)

    /** KMP-side [KClass] → JVM-side [Class]. Walks through
     *  KClassEnum's paired JClassEnum so `common/` code stays
     *  KMP-portable while JVM consumers (Spring JDBC, Jackson, …)
     *  get the java.* handle they expect. */
    fun kmpToJvm(kcls: KClass<*>): Class<*> =
        KClassEnum.fromKClass(kcls)?.jclass?.jclass ?: kcls.java

    /** JVM-side [Class] → KMP-side [KClass]. Reverse of [kmpToJvm]. */
    fun jvmToKmp(jcls: Class<*>): KClass<*> =
        JClassEnum.fromJClass(jcls)?.let { je ->
            KClassEnum.entries.firstOrNull { it.jclass == je }?.kclass
        } ?: jcls.kotlin
}
