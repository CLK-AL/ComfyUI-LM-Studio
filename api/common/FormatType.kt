// Five-way bridge: one enum value per format, all fields are typed.
// Mirror of comfyui_openapi_node/format_type.py.
// JsonType + JsonFormat ↔ SqlTypes ↔ KClass<*> ↔ ComposeWidget ↔
// HtmlInputType ↔ ComfyType.
//
// Covers every HTML5 <input> type plus <textarea> / <select>, every
// Compose Multiplatform widget, and every ComfyUI primitive —
// including dropdown / radio / multi-select enum variants.

import kotlin.reflect.KClass
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlin.time.Duration

// ----- vocabulary enums -------------------------------------------------
enum class JsonType(val value: String) {
    STRING("string"), INTEGER("integer"), NUMBER("number"),
    BOOLEAN("boolean"), OBJECT("object"), ARRAY("array"),
    NULL_("null");
    companion object {
        fun fromValue(v: String?): JsonType =
            entries.firstOrNull { it.value == v } ?: STRING
    }
}

enum class JsonFormat(val value: String) {
    NONE(""),
    TEXTAREA("textarea"), PASSWORD("password"),
    EMAIL("email"), TEL("tel"), URI("uri"), UUID("uuid"), COLOR("color"),
    DATE("date"), TIME("time"), DATE_TIME("date-time"),
    MONTH("month"), WEEK("week"),
    DURATION("duration"),
    IPV4("ipv4"), IPV6("ipv6"), HOSTNAME("hostname"),
    REGEX("regex"), JSON_POINTER("json-pointer"),
    BYTE("byte"), BINARY("binary"),
    GEOJSON("geojson"), JSON("json"),
    INT32("int32"), INT64("int64"), FLOAT("float"), DOUBLE("double"),
    ENUM("enum"), SEARCH("search"), HIDDEN("hidden");
    companion object {
        fun fromValue(v: String?): JsonFormat =
            if (v.isNullOrEmpty()) NONE
            else entries.firstOrNull { it.value == v } ?: NONE
    }
}

enum class HtmlInputType(val value: String) {
    TEXT("text"), EMAIL("email"), URL("url"), TEL("tel"),
    NUMBER("number"),
    DATE("date"), TIME("time"), DATETIME_LOCAL("datetime-local"),
    MONTH("month"), WEEK("week"),
    COLOR("color"),
    CHECKBOX("checkbox"), RADIO("radio"),
    FILE("file"), PASSWORD("password"),
    RANGE("range"), SEARCH("search"), HIDDEN("hidden"),
    // non-<input> form elements
    TEXTAREA("textarea"),
    SELECT("select"),
    SELECT_MULTI("select[multiple]");
}

enum class ComfyType(val value: String) {
    STRING_("STRING"), INT_("INT"), FLOAT_("FLOAT"),
    BOOLEAN_("BOOLEAN"), COMBO("COMBO");
}

enum class ComposeWidget(val value: String) {
    TEXT_FIELD("TextField"),
    OUTLINED_TEXT_FIELD("OutlinedTextField"),
    PASSWORD_FIELD("TextField(visualTransformation=PasswordVisualTransformation())"),
    SEARCH_FIELD("SearchBar"),
    COLOR_PICKER("ColorPicker"),
    DATE_PICKER("DatePicker"),
    TIME_PICKER("TimePicker"),
    DATETIME_PICKER("DateTimePicker"),
    MONTH_PICKER("MonthPicker"),
    WEEK_PICKER("WeekPicker"),
    FILE_PICKER("FilePicker"),
    MAP_PICKER("MapPicker"),
    SLIDER("Slider"),
    RANGE_SLIDER("RangeSlider"),
    SWITCH("Switch"),
    CHECKBOX("Checkbox"),
    CHECKBOX_GROUP("CheckboxGroup"),
    RADIO_GROUP("RadioGroup"),
    DROPDOWN_MENU("DropdownMenu"),
    HIDDEN_FIELD("HiddenField");
}

// ----- the bridge -------------------------------------------------------
data class FormatMapping(
    val jsonType:   JsonType,
    val jsonFormat: JsonFormat,
    val sqlType:    SqlTypes,
    val kclass:     KClass<*>,
    val composable: ComposeWidget,
    val htmlInput:  HtmlInputType,
    val comfy:      ComfyType,
    val placeholder:String = "",
)

enum class FormatType(val mapping: FormatMapping) {
    TEXT(         FormatMapping(JsonType.STRING,  JsonFormat.NONE,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    TEXTAREA(     FormatMapping(JsonType.STRING,  JsonFormat.TEXTAREA,     SqlTypes.LONGVARCHAR, String::class,     ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    PASSWORD(     FormatMapping(JsonType.STRING,  JsonFormat.PASSWORD,     SqlTypes.VARCHAR,     String::class,     ComposeWidget.PASSWORD_FIELD,      HtmlInputType.PASSWORD,       ComfyType.STRING_)),
    EMAIL(        FormatMapping(JsonType.STRING,  JsonFormat.EMAIL,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.EMAIL,          ComfyType.STRING_, "user@example.com")),
    TEL(          FormatMapping(JsonType.STRING,  JsonFormat.TEL,          SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEL,            ComfyType.STRING_, "+1 555 0100")),
    URL(          FormatMapping(JsonType.STRING,  JsonFormat.URI,          SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.URL,            ComfyType.STRING_, "https://…")),
    SEARCH(       FormatMapping(JsonType.STRING,  JsonFormat.SEARCH,       SqlTypes.VARCHAR,     String::class,     ComposeWidget.SEARCH_FIELD,        HtmlInputType.SEARCH,         ComfyType.STRING_, "Search…")),
    UUID(         FormatMapping(JsonType.STRING,  JsonFormat.UUID,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "00000000-0000-0000-0000-000000000000")),
    COLOR(        FormatMapping(JsonType.STRING,  JsonFormat.COLOR,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.COLOR_PICKER,        HtmlInputType.COLOR,          ComfyType.STRING_, "#RRGGBB")),
    DATE(         FormatMapping(JsonType.STRING,  JsonFormat.DATE,         SqlTypes.DATE,        LocalDate::class,  ComposeWidget.DATE_PICKER,         HtmlInputType.DATE,           ComfyType.STRING_, "YYYY-MM-DD")),
    TIME(         FormatMapping(JsonType.STRING,  JsonFormat.TIME,         SqlTypes.TIME,        LocalTime::class,  ComposeWidget.TIME_PICKER,         HtmlInputType.TIME,           ComfyType.STRING_, "HH:MM:SS")),
    DATETIME(     FormatMapping(JsonType.STRING,  JsonFormat.DATE_TIME,    SqlTypes.TIMESTAMP,   Instant::class,    ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_, "YYYY-MM-DDTHH:MM:SSZ")),
    MONTH(        FormatMapping(JsonType.STRING,  JsonFormat.MONTH,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.MONTH_PICKER,        HtmlInputType.MONTH,          ComfyType.STRING_, "YYYY-MM")),
    WEEK(         FormatMapping(JsonType.STRING,  JsonFormat.WEEK,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.WEEK_PICKER,         HtmlInputType.WEEK,           ComfyType.STRING_, "YYYY-Www")),
    DURATION(     FormatMapping(JsonType.STRING,  JsonFormat.DURATION,     SqlTypes.VARCHAR,     Duration::class,   ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "P1DT2H")),
    IPV4(         FormatMapping(JsonType.STRING,  JsonFormat.IPV4,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "0.0.0.0")),
    IPV6(         FormatMapping(JsonType.STRING,  JsonFormat.IPV6,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "::1")),
    HOSTNAME(     FormatMapping(JsonType.STRING,  JsonFormat.HOSTNAME,     SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "example.com")),
    REGEX(        FormatMapping(JsonType.STRING,  JsonFormat.REGEX,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "^.*$")),
    JSON_POINTER( FormatMapping(JsonType.STRING,  JsonFormat.JSON_POINTER, SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "/foo/bar")),
    BYTE(         FormatMapping(JsonType.STRING,  JsonFormat.BYTE,         SqlTypes.VARBINARY,   ByteArray::class,  ComposeWidget.FILE_PICKER,         HtmlInputType.FILE,           ComfyType.STRING_)),
    BINARY(       FormatMapping(JsonType.STRING,  JsonFormat.BINARY,       SqlTypes.BLOB,        ByteArray::class,  ComposeWidget.FILE_PICKER,         HtmlInputType.FILE,           ComfyType.STRING_)),
    HIDDEN(       FormatMapping(JsonType.STRING,  JsonFormat.HIDDEN,       SqlTypes.VARCHAR,     String::class,     ComposeWidget.HIDDEN_FIELD,        HtmlInputType.HIDDEN,         ComfyType.STRING_)),
    GEOJSON(      FormatMapping(JsonType.OBJECT,  JsonFormat.GEOJSON,      SqlTypes.OTHER,       JsonObject::class, ComposeWidget.MAP_PICKER,          HtmlInputType.TEXTAREA,       ComfyType.STRING_, "{\"type\":\"Point\",\"coordinates\":[0,0]}")),
    JSON_OBJECT(  FormatMapping(JsonType.OBJECT,  JsonFormat.JSON,         SqlTypes.OTHER,       JsonObject::class, ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    JSON_ARRAY(   FormatMapping(JsonType.ARRAY,   JsonFormat.JSON,         SqlTypes.ARRAY,       JsonArray::class,  ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    INT32(        FormatMapping(JsonType.INTEGER, JsonFormat.INT32,        SqlTypes.INTEGER,     Int::class,        ComposeWidget.SLIDER,              HtmlInputType.NUMBER,         ComfyType.INT_)),
    INT64(        FormatMapping(JsonType.INTEGER, JsonFormat.INT64,        SqlTypes.BIGINT,      Long::class,       ComposeWidget.SLIDER,              HtmlInputType.NUMBER,         ComfyType.INT_)),
    FLOAT_(       FormatMapping(JsonType.NUMBER,  JsonFormat.FLOAT,        SqlTypes.REAL,        Float::class,      ComposeWidget.SLIDER,              HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    DOUBLE_(      FormatMapping(JsonType.NUMBER,  JsonFormat.DOUBLE,       SqlTypes.DOUBLE,      Double::class,     ComposeWidget.SLIDER,              HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    RANGE(        FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        Float::class,      ComposeWidget.RANGE_SLIDER,        HtmlInputType.RANGE,          ComfyType.FLOAT_)),
    BOOL(         FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     Boolean::class,    ComposeWidget.SWITCH,              HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    CHECKBOX(     FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     Boolean::class,    ComposeWidget.CHECKBOX,            HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    ENUM(         FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO)),
    RADIO(        FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.RADIO_GROUP,         HtmlInputType.RADIO,          ComfyType.COMBO)),
    MULTI_SELECT( FormatMapping(JsonType.ARRAY,   JsonFormat.ENUM,         SqlTypes.ARRAY,       List::class,       ComposeWidget.CHECKBOX_GROUP,      HtmlInputType.SELECT_MULTI,   ComfyType.COMBO)),
    ;

    val kclassFqn: String
        get() = mapping.kclass.qualifiedName ?: mapping.kclass.simpleName ?: ""

    companion object {
        fun fromJsonSchema(schema: Map<String, Any?>): FormatType {
            if ("enum" in schema) return ENUM
            val t = JsonType.fromValue(schema["type"] as? String)
            val f = JsonFormat.fromValue(schema["format"] as? String)
            return when (t) {
                JsonType.BOOLEAN -> BOOL
                JsonType.INTEGER -> if (f == JsonFormat.INT64) INT64 else INT32
                JsonType.NUMBER  -> if (f == JsonFormat.DOUBLE) DOUBLE_ else FLOAT_
                JsonType.ARRAY   -> JSON_ARRAY
                JsonType.OBJECT  -> if (f == JsonFormat.GEOJSON) GEOJSON else JSON_OBJECT
                JsonType.STRING, JsonType.NULL_ -> entries.firstOrNull {
                    it.mapping.jsonType == JsonType.STRING && it.mapping.jsonFormat == f
                } ?: TEXT
            }
        }

        fun fromSql(sqlType: SqlTypes): FormatType =
            entries.firstOrNull { it.mapping.sqlType == sqlType } ?: TEXT

        fun fromSql(sqlTypeName: String): FormatType =
            try { fromSql(SqlTypes.fromName(sqlTypeName)) }
            catch (e: IllegalArgumentException) { TEXT }

        fun fromKClass(kcls: KClass<*>): FormatType =
            entries.firstOrNull { it.mapping.kclass == kcls } ?: TEXT
    }
}
