// Five-way bridge: one enum value per format, six mappings per value.
// Mirror of comfyui_openapi_node/format_type.py — the shared fixture
// `tests/fixtures/format-type-bridge.json` drives parity tests on both
// sides so the two implementations never drift.
//
// JSON Schema ↔ SQL ↔ Kotlin KClass ↔ Compose widget ↔ HTML <input>
//   ↔ ComfyUI INPUT_TYPES primitive.

data class FormatMapping(
    val jsonType: String,
    val jsonFormat: String?,
    val sqlType: String,
    val kclass: String,
    val composable: String,
    val htmlInput: String,
    val comfy: String,
    val placeholder: String = "",
)

enum class FormatType(val mapping: FormatMapping) {
    TEXT(           FormatMapping("string",  null,         "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING")),
    TEXTAREA(       FormatMapping("string",  "textarea",   "LONGVARCHAR", "kotlin.String",                         "OutlinedTextField","text",            "STRING")),
    PASSWORD(       FormatMapping("string",  "password",   "VARCHAR",     "kotlin.String",                         "TextField(visualTransformation=PasswordVisualTransformation())", "password", "STRING")),
    EMAIL(          FormatMapping("string",  "email",      "VARCHAR",     "kotlin.String",                         "TextField",        "email",           "STRING", "user@example.com")),
    TEL(            FormatMapping("string",  "tel",        "VARCHAR",     "kotlin.String",                         "TextField",        "tel",             "STRING", "+1 555 0100")),
    URL(            FormatMapping("string",  "uri",        "VARCHAR",     "kotlin.String",                         "TextField",        "url",             "STRING", "https://…")),
    UUID(           FormatMapping("string",  "uuid",       "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING", "00000000-0000-0000-0000-000000000000")),
    COLOR(          FormatMapping("string",  "color",      "VARCHAR",     "kotlin.String",                         "ColorPicker",      "color",           "STRING", "#RRGGBB")),
    DATE(           FormatMapping("string",  "date",       "DATE",        "kotlinx.datetime.LocalDate",            "DatePicker",       "date",            "STRING", "YYYY-MM-DD")),
    TIME(           FormatMapping("string",  "time",       "TIME",        "kotlinx.datetime.LocalTime",            "TimePicker",       "time",            "STRING", "HH:MM:SS")),
    DATETIME(       FormatMapping("string",  "date-time",  "TIMESTAMP",   "kotlinx.datetime.Instant",              "DateTimePicker",   "datetime-local",  "STRING", "YYYY-MM-DDTHH:MM:SSZ")),
    DURATION(       FormatMapping("string",  "duration",   "VARCHAR",     "kotlin.time.Duration",                  "TextField",        "text",            "STRING", "P1DT2H")),
    IPV4(           FormatMapping("string",  "ipv4",       "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING", "0.0.0.0")),
    IPV6(           FormatMapping("string",  "ipv6",       "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING", "::1")),
    HOSTNAME(       FormatMapping("string",  "hostname",   "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING", "example.com")),
    REGEX(          FormatMapping("string",  "regex",      "VARCHAR",     "kotlin.String",                         "TextField",        "text",            "STRING", "^.*$")),
    JSON_POINTER(   FormatMapping("string",  "json-pointer","VARCHAR",    "kotlin.String",                         "TextField",        "text",            "STRING", "/foo/bar")),
    BYTE(           FormatMapping("string",  "byte",       "VARBINARY",   "kotlin.ByteArray",                      "FilePicker",       "file",            "STRING")),
    BINARY(         FormatMapping("string",  "binary",     "BLOB",        "kotlin.ByteArray",                      "FilePicker",       "file",            "STRING")),
    GEOJSON(        FormatMapping("object",  "geojson",    "OTHER",       "kotlinx.serialization.json.JsonObject", "MapPicker",        "text",            "STRING", "{\"type\":\"Point\",\"coordinates\":[0,0]}")),
    JSON_OBJECT(    FormatMapping("object",  "json",       "OTHER",       "kotlinx.serialization.json.JsonObject", "OutlinedTextField","text",            "STRING")),
    JSON_ARRAY(     FormatMapping("array",   "json",       "ARRAY",       "kotlinx.serialization.json.JsonArray",  "OutlinedTextField","text",            "STRING")),
    INT32(          FormatMapping("integer", "int32",      "INTEGER",     "kotlin.Int",                            "Slider",           "number",          "INT")),
    INT64(          FormatMapping("integer", "int64",      "BIGINT",      "kotlin.Long",                           "Slider",           "number",          "INT")),
    FLOAT_(         FormatMapping("number",  "float",      "REAL",        "kotlin.Float",                          "Slider",           "number",          "FLOAT")),
    DOUBLE_(        FormatMapping("number",  "double",     "DOUBLE",      "kotlin.Double",                         "Slider",           "number",          "FLOAT")),
    BOOL(           FormatMapping("boolean", null,         "BOOLEAN",     "kotlin.Boolean",                        "Switch",           "checkbox",        "BOOLEAN")),
    ENUM(           FormatMapping("string",  "enum",       "VARCHAR",     "kotlin.String",                         "DropdownMenu",     "text",            "COMBO")),
    ;

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

        fun fromSql(sqlType: String): FormatType {
            val norm = sqlType.uppercase()
            return entries.firstOrNull { it.mapping.sqlType == norm } ?: TEXT
        }
    }
}
