// Five-way bridge: one enum value per format, mappings per row.
// Mirror of comfyui_openapi_node/format_type.py — the shared fixture
// `tests/fixtures/format-type-bridge.json` drives parity tests on both
// sides so the two implementations never drift.
//
// JSON Schema ↔ SQL ↔ **Kotlin KClass (real, not a string)** ↔
// Compose widget ↔ HTML <input> ↔ ComfyUI INPUT_TYPES primitive.

import kotlin.reflect.KClass
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlin.time.Duration

data class FormatMapping(
    val jsonType: String,
    val jsonFormat: String?,
    /** The JDBC `SqlTypes` enum value — `sqlType.code` is the
     *  `java.sql.Types` int, `sqlType.name` is the readable form
     *  used in DDL and fixtures. */
    val sqlType: SqlTypes,
    /** Real Kotlin KClass — callers can do reflection, type-check,
     *  serialise, etc. directly. `kclass.qualifiedName` produces the
     *  FQN the parity fixture compares against. */
    val kclass: KClass<*>,
    val composable: String,
    val htmlInput: String,
    val comfy: String,
    val placeholder: String = "",
)

enum class FormatType(val mapping: FormatMapping) {
    TEXT(           FormatMapping("string",  null,          SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING")),
    TEXTAREA(       FormatMapping("string",  "textarea",    SqlTypes.LONGVARCHAR, String::class,     "OutlinedTextField","text",            "STRING")),
    PASSWORD(       FormatMapping("string",  "password",    SqlTypes.VARCHAR,     String::class,     "TextField(visualTransformation=PasswordVisualTransformation())", "password", "STRING")),
    EMAIL(          FormatMapping("string",  "email",       SqlTypes.VARCHAR,     String::class,     "TextField",        "email",           "STRING", "user@example.com")),
    TEL(            FormatMapping("string",  "tel",         SqlTypes.VARCHAR,     String::class,     "TextField",        "tel",             "STRING", "+1 555 0100")),
    URL(            FormatMapping("string",  "uri",         SqlTypes.VARCHAR,     String::class,     "TextField",        "url",             "STRING", "https://…")),
    UUID(           FormatMapping("string",  "uuid",        SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "00000000-0000-0000-0000-000000000000")),
    COLOR(          FormatMapping("string",  "color",       SqlTypes.VARCHAR,     String::class,     "ColorPicker",      "color",           "STRING", "#RRGGBB")),
    DATE(           FormatMapping("string",  "date",        SqlTypes.DATE,        LocalDate::class,  "DatePicker",       "date",            "STRING", "YYYY-MM-DD")),
    TIME(           FormatMapping("string",  "time",        SqlTypes.TIME,        LocalTime::class,  "TimePicker",       "time",            "STRING", "HH:MM:SS")),
    DATETIME(       FormatMapping("string",  "date-time",   SqlTypes.TIMESTAMP,   Instant::class,    "DateTimePicker",   "datetime-local",  "STRING", "YYYY-MM-DDTHH:MM:SSZ")),
    DURATION(       FormatMapping("string",  "duration",    SqlTypes.VARCHAR,     Duration::class,   "TextField",        "text",            "STRING", "P1DT2H")),
    IPV4(           FormatMapping("string",  "ipv4",        SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "0.0.0.0")),
    IPV6(           FormatMapping("string",  "ipv6",        SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "::1")),
    HOSTNAME(       FormatMapping("string",  "hostname",    SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "example.com")),
    REGEX(          FormatMapping("string",  "regex",       SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "^.*$")),
    JSON_POINTER(   FormatMapping("string",  "json-pointer",SqlTypes.VARCHAR,     String::class,     "TextField",        "text",            "STRING", "/foo/bar")),
    BYTE(           FormatMapping("string",  "byte",        SqlTypes.VARBINARY,   ByteArray::class,  "FilePicker",       "file",            "STRING")),
    BINARY(         FormatMapping("string",  "binary",      SqlTypes.BLOB,        ByteArray::class,  "FilePicker",       "file",            "STRING")),
    GEOJSON(        FormatMapping("object",  "geojson",     SqlTypes.OTHER,       JsonObject::class, "MapPicker",        "text",            "STRING", "{\"type\":\"Point\",\"coordinates\":[0,0]}")),
    JSON_OBJECT(    FormatMapping("object",  "json",        SqlTypes.OTHER,       JsonObject::class, "OutlinedTextField","text",            "STRING")),
    JSON_ARRAY(     FormatMapping("array",   "json",        SqlTypes.ARRAY,       JsonArray::class,  "OutlinedTextField","text",            "STRING")),
    INT32(          FormatMapping("integer", "int32",       SqlTypes.INTEGER,     Int::class,        "Slider",           "number",          "INT")),
    INT64(          FormatMapping("integer", "int64",       SqlTypes.BIGINT,      Long::class,       "Slider",           "number",          "INT")),
    FLOAT_(         FormatMapping("number",  "float",       SqlTypes.REAL,        Float::class,      "Slider",           "number",          "FLOAT")),
    DOUBLE_(        FormatMapping("number",  "double",      SqlTypes.DOUBLE,      Double::class,     "Slider",           "number",          "FLOAT")),
    BOOL(           FormatMapping("boolean", null,          SqlTypes.BOOLEAN,     Boolean::class,    "Switch",           "checkbox",        "BOOLEAN")),
    ENUM(           FormatMapping("string",  "enum",        SqlTypes.VARCHAR,     String::class,     "DropdownMenu",     "text",            "COMBO")),
    ;

    /** FQN string (matches the Python `kclass` field in the fixture). */
    val kclassFqn: String
        get() = mapping.kclass.qualifiedName ?: mapping.kclass.simpleName ?: ""

    companion object {
        fun fromJsonSchema(schema: Map<String, Any?>): FormatType {
            if ("enum" in schema) return ENUM
            val t = schema["type"] as? String
            val f = (schema["format"] as? String) ?: ""
            return when (t) {
                "boolean" -> BOOL
                "integer" -> if (f == "int64") INT64 else INT32
                "number"  -> if (f == "double") DOUBLE_ else FLOAT_
                "array"   -> JSON_ARRAY
                "object"  -> if (f == "geojson") GEOJSON else JSON_OBJECT
                "string", null -> entries.firstOrNull {
                    it.mapping.jsonType == "string" && (it.mapping.jsonFormat ?: "") == f
                } ?: TEXT
                else -> TEXT
            }
        }

        fun fromSql(sqlType: SqlTypes): FormatType =
            entries.firstOrNull { it.mapping.sqlType == sqlType } ?: TEXT

        /** Convenience overload — accepts the JDBC name. */
        fun fromSql(sqlTypeName: String): FormatType =
            try { fromSql(SqlTypes.fromName(sqlTypeName)) }
            catch (e: IllegalArgumentException) { TEXT }

        /** Reverse lookup by KClass — any format declaring this
         *  runtime type. Takes the first match. */
        fun fromKClass(kcls: KClass<*>): FormatType =
            entries.firstOrNull { it.mapping.kclass == kcls } ?: TEXT
    }
}
