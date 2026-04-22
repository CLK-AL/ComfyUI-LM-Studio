// Five-way bridge: one enum value per format, all fields are typed.
// Mirror of comfyui_openapi_node/format_type.py.
// Covers: full HTML5 form roster, Compose Multiplatform widgets,
// every ComfyUI primitive AND domain type (IMAGE / LATENT / MASK /
// MODEL / CLIP / VAE / CONDITIONING / CONTROL_NET / STYLE_MODEL /
// CLIP_VISION / CLIP_VISION_OUTPUT / UPSCALE_MODEL / AUDIO / VIDEO /
// WEBCAM), date/time-part inputs (year, quarter, day, hour, minute,
// second, millisecond, timezone), and dynamic-UI flags.

import kotlin.reflect.KClass
import kotlinx.datetime.Instant
import kotlinx.datetime.LocalDate
import kotlinx.datetime.LocalTime
import kotlinx.datetime.TimeZone
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlin.time.Duration

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
    TEXTAREA("textarea"), PASSWORD("password"), MARKDOWN("markdown"),
    EMAIL("email"), TEL("tel"), URI("uri"), UUID("uuid"), COLOR("color"),
    DATE("date"), TIME("time"), DATE_TIME("date-time"),
    MONTH("month"), WEEK("week"),
    YEAR("year"), QUARTER("quarter"),
    DAY("day"), HOUR("hour"), MINUTE("minute"),
    SECOND("second"), MILLISECOND("millisecond"),
    TIMEZONE("timezone"),
    DURATION("duration"),
    IPV4("ipv4"), IPV6("ipv6"), HOSTNAME("hostname"),
    REGEX("regex"), JSON_POINTER("json-pointer"),
    BYTE("byte"), BINARY("binary"),
    GEOJSON("geojson"), JSON("json"),
    INT32("int32"), INT64("int64"), FLOAT("float"), DOUBLE("double"),
    ENUM("enum"), SEARCH("search"), HIDDEN("hidden"),
    // ComfyUI domain media formats
    IMAGE("image"), LATENT("latent"), MASK("mask"),
    AUDIO("audio"), VIDEO("video"),
    MODEL_REF("model-ref"), CONDITIONING("conditioning"),

    // vCard 4.0 (RFC 6350)
    VCARD_FN("vcard.fn"), VCARD_N("vcard.n"),
    VCARD_NICKNAME("vcard.nickname"),
    VCARD_BDAY("vcard.bday"), VCARD_ANNIVERSARY("vcard.anniversary"),
    VCARD_GENDER("vcard.gender"),
    VCARD_ADR("vcard.adr"),
    VCARD_TEL("vcard.tel"), VCARD_EMAIL("vcard.email"),
    VCARD_GEO("vcard.geo"), VCARD_TZ("vcard.tz"),
    VCARD_TITLE("vcard.title"), VCARD_ROLE("vcard.role"),
    VCARD_ORG("vcard.org"), VCARD_NOTE("vcard.note"),
    VCARD_URL("vcard.url"), VCARD_UID("vcard.uid"),
    VCARD_REV("vcard.rev"), VCARD_CATEGORIES("vcard.categories"),

    // iCalendar (RFC 5545)
    ICAL_DTSTART("ical.dtstart"), ICAL_DTEND("ical.dtend"),
    ICAL_DTSTAMP("ical.dtstamp"), ICAL_DUE("ical.due"),
    ICAL_COMPLETED("ical.completed"), ICAL_DURATION("ical.duration"),
    ICAL_LOCATION("ical.location"), ICAL_DESCRIPTION("ical.description"),
    ICAL_SUMMARY("ical.summary"), ICAL_COMMENT("ical.comment"),
    ICAL_STATUS("ical.status"), ICAL_CLASS("ical.class"),
    ICAL_TRANSP("ical.transp"), ICAL_PRIORITY("ical.priority"),
    ICAL_SEQUENCE("ical.sequence"), ICAL_GEO("ical.geo"),
    ICAL_RRULE("ical.rrule"), ICAL_RDATE("ical.rdate"),
    ICAL_EXDATE("ical.exdate"),
    ICAL_ATTENDEE("ical.attendee"), ICAL_ORGANIZER("ical.organizer"),
    ICAL_CATEGORIES("ical.categories"),
    ICAL_UID("ical.uid"), ICAL_TZID("ical.tzid"),
    ICAL_METHOD("ical.method"), ICAL_CALSCALE("ical.calscale"),
    ICAL_RELATED_TO("ical.related-to"),
    ICAL_RECUR_ID("ical.recurrence-id"),

    // Delimited cell formats (POI XLSX / CSV / TSV / vCard / iCal)
    SEMI_DELIMITED("semi-delimited"),
    CSV("csv"),
    TSV("tsv"),
    // Compound-date parts
    MONTH_OF_YEAR("month-of-year"),
    DAY_OF_WEEK("day-of-week"),
    DAY_OF_YEAR("day-of-year"),
    ISO_WEEK_NUM("iso-week-num"),
    OFFSET("offset");
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
    TEXTAREA("textarea"),
    SELECT("select"),
    SELECT_MULTI("select[multiple]");
}

enum class ComfyType(val value: String) {
    STRING_("STRING"), INT_("INT"), FLOAT_("FLOAT"),
    BOOLEAN_("BOOLEAN"), COMBO("COMBO"),
    // domain types
    IMAGE("IMAGE"), LATENT("LATENT"), MASK("MASK"),
    MODEL("MODEL"), CLIP("CLIP"), VAE("VAE"),
    CONDITIONING("CONDITIONING"), CONTROL_NET("CONTROL_NET"),
    STYLE_MODEL("STYLE_MODEL"),
    CLIP_VISION("CLIP_VISION"), CLIP_VISION_OUTPUT("CLIP_VISION_OUTPUT"),
    UPSCALE_MODEL("UPSCALE_MODEL"),
    AUDIO("AUDIO"), VIDEO("VIDEO"), WEBCAM("WEBCAM");
}

enum class ComposeWidget(val value: String) {
    TEXT_FIELD("TextField"),
    OUTLINED_TEXT_FIELD("OutlinedTextField"),
    PASSWORD_FIELD("TextField(visualTransformation=PasswordVisualTransformation())"),
    SEARCH_FIELD("SearchBar"),
    DYNAMIC_PROMPT_FIELD("DynamicPromptField"),
    MARKDOWN_VIEW("MarkdownView"),
    COLOR_PICKER("ColorPicker"),
    DATE_PICKER("DatePicker"),
    TIME_PICKER("TimePicker"),
    DATETIME_PICKER("DateTimePicker"),
    MONTH_PICKER("MonthPicker"),
    WEEK_PICKER("WeekPicker"),
    FILE_PICKER("FilePicker"),
    MAP_PICKER("MapPicker"),
    IMAGE_UPLOAD("ImageUpload"),
    MASK_EDITOR("MaskEditor"),
    WEBCAM_CAPTURE("WebcamCapture"),
    AUDIO_PLAYER("AudioPlayer"),
    VIDEO_PLAYER("VideoPlayer"),
    MODEL_PICKER("ModelPicker"),
    LATENT_PREVIEW("LatentPreview"),
    CONDITIONING_VIEW("ConditioningView"),
    SLIDER("Slider"),
    RANGE_SLIDER("RangeSlider"),
    KNOB("Knob"),
    NUMBER_FIELD("NumberField"),
    SWITCH("Switch"),
    CHECKBOX("Checkbox"),
    CHECKBOX_GROUP("CheckboxGroup"),
    RADIO_GROUP("RadioGroup"),
    DROPDOWN_MENU("DropdownMenu"),
    HIDDEN_FIELD("HiddenField");
}

/** Boolean flags ComfyUI's frontend reads off the widget options dict. */
enum class ComfyOption(val key: String) {
    FORCE_INPUT("forceInput"),
    DEFAULT_INPUT("defaultInput"),
    LAZY("lazy"),
    DYNAMIC_PROMPTS("dynamicPrompts"),
    MULTILINE("multiline"),
    IMAGE_UPLOAD("image_upload"),
    IMAGE_FOLDER("image_folder"),
    DIRECTORY("directory"),
    TOOLTIP_MARKDOWN("tooltip_md");
}

/** Value of the `display` widget option for INT / FLOAT widgets. */
enum class ComfyDisplay(val value: String) {
    NUMBER("number"), SLIDER("slider"), KNOB("knob"), COLOR("color");
}

// ----- RFC vocabulary enums (iCal + vCard full coverage) ----------------
enum class IcalComponent(val value: String) {
    VCALENDAR("VCALENDAR"),
    VEVENT("VEVENT"), VTODO("VTODO"), VJOURNAL("VJOURNAL"),
    VFREEBUSY("VFREEBUSY"), VTIMEZONE("VTIMEZONE"),
    VALARM("VALARM"),
    STANDARD("STANDARD"), DAYLIGHT("DAYLIGHT");
}

enum class IcalStatus(val value: String) {
    TENTATIVE("TENTATIVE"), CONFIRMED("CONFIRMED"), CANCELLED("CANCELLED"),
    NEEDS_ACTION("NEEDS-ACTION"), IN_PROCESS("IN-PROCESS"),
    COMPLETED("COMPLETED"), DRAFT("DRAFT"), FINAL("FINAL");
}

enum class IcalMethod(val value: String) {
    PUBLISH("PUBLISH"), REQUEST("REQUEST"), REPLY("REPLY"),
    ADD("ADD"), CANCEL("CANCEL"), REFRESH("REFRESH"),
    COUNTER("COUNTER"), DECLINE_COUNTER("DECLINECOUNTER");
}

enum class IcalClass(val value: String) {
    PUBLIC("PUBLIC"), PRIVATE("PRIVATE"), CONFIDENTIAL("CONFIDENTIAL");
}

enum class IcalTransp(val value: String) {
    OPAQUE("OPAQUE"), TRANSPARENT("TRANSPARENT");
}

enum class IcalAction(val value: String) {
    AUDIO("AUDIO"), DISPLAY("DISPLAY"), EMAIL("EMAIL");
}

enum class VCardEmailType(val value: String) {
    WORK("work"), HOME("home"), INTERNET("internet"), PREF("pref"), OTHER("other");
}

enum class VCardTelType(val value: String) {
    VOICE("voice"), FAX("fax"), CELL("cell"),
    HOME("home"), WORK("work"), TEXT("text"),
    VIDEO("video"), PAGER("pager"), TEXTPHONE("textphone"),
    CAR("car"), ISDN("isdn"), PCS("pcs");
}

enum class VCardGender(val value: String) {
    MALE("M"), FEMALE("F"), OTHER("O"), NONE_("N"), UNKNOWN("U");
}

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
    TEXT(           FormatMapping(JsonType.STRING,  JsonFormat.NONE,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_)),
    TEXTAREA(       FormatMapping(JsonType.STRING,  JsonFormat.TEXTAREA,     SqlTypes.LONGVARCHAR, String::class,     ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    DYNAMIC_PROMPT( FormatMapping(JsonType.STRING,  JsonFormat.TEXTAREA,     SqlTypes.LONGVARCHAR, String::class,     ComposeWidget.DYNAMIC_PROMPT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    MARKDOWN(       FormatMapping(JsonType.STRING,  JsonFormat.MARKDOWN,     SqlTypes.LONGVARCHAR, String::class,     ComposeWidget.MARKDOWN_VIEW,        HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    PASSWORD(       FormatMapping(JsonType.STRING,  JsonFormat.PASSWORD,     SqlTypes.VARCHAR,     String::class,     ComposeWidget.PASSWORD_FIELD,       HtmlInputType.PASSWORD,       ComfyType.STRING_)),
    EMAIL(          FormatMapping(JsonType.STRING,  JsonFormat.EMAIL,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.EMAIL,          ComfyType.STRING_, "user@example.com")),
    TEL(            FormatMapping(JsonType.STRING,  JsonFormat.TEL,          SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEL,            ComfyType.STRING_, "+1 555 0100")),
    URL(            FormatMapping(JsonType.STRING,  JsonFormat.URI,          SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.URL,            ComfyType.STRING_, "https://…")),
    SEARCH(         FormatMapping(JsonType.STRING,  JsonFormat.SEARCH,       SqlTypes.VARCHAR,     String::class,     ComposeWidget.SEARCH_FIELD,         HtmlInputType.SEARCH,         ComfyType.STRING_, "Search…")),
    UUID(           FormatMapping(JsonType.STRING,  JsonFormat.UUID,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "00000000-0000-0000-0000-000000000000")),
    COLOR(          FormatMapping(JsonType.STRING,  JsonFormat.COLOR,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.COLOR_PICKER,         HtmlInputType.COLOR,          ComfyType.STRING_, "#RRGGBB")),
    DATE(           FormatMapping(JsonType.STRING,  JsonFormat.DATE,         SqlTypes.DATE,        LocalDate::class,  ComposeWidget.DATE_PICKER,          HtmlInputType.DATE,           ComfyType.STRING_, "YYYY-MM-DD")),
    TIME(           FormatMapping(JsonType.STRING,  JsonFormat.TIME,         SqlTypes.TIME,        LocalTime::class,  ComposeWidget.TIME_PICKER,          HtmlInputType.TIME,           ComfyType.STRING_, "HH:MM:SS")),
    DATETIME(       FormatMapping(JsonType.STRING,  JsonFormat.DATE_TIME,    SqlTypes.TIMESTAMP,   Instant::class,    ComposeWidget.DATETIME_PICKER,      HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_, "YYYY-MM-DDTHH:MM:SSZ")),
    MONTH(          FormatMapping(JsonType.STRING,  JsonFormat.MONTH,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.MONTH_PICKER,         HtmlInputType.MONTH,          ComfyType.STRING_, "YYYY-MM")),
    WEEK(           FormatMapping(JsonType.STRING,  JsonFormat.WEEK,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.WEEK_PICKER,          HtmlInputType.WEEK,           ComfyType.STRING_, "YYYY-Www")),
    TIMEZONE(       FormatMapping(JsonType.STRING,  JsonFormat.TIMEZONE,     SqlTypes.VARCHAR,     TimeZone::class,   ComposeWidget.DROPDOWN_MENU,        HtmlInputType.SELECT,         ComfyType.COMBO,  "Europe/London")),
    DURATION(       FormatMapping(JsonType.STRING,  JsonFormat.DURATION,     SqlTypes.VARCHAR,     Duration::class,   ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "P1DT2H")),
    IPV4(           FormatMapping(JsonType.STRING,  JsonFormat.IPV4,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "0.0.0.0")),
    IPV6(           FormatMapping(JsonType.STRING,  JsonFormat.IPV6,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "::1")),
    HOSTNAME(       FormatMapping(JsonType.STRING,  JsonFormat.HOSTNAME,     SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "example.com")),
    REGEX(          FormatMapping(JsonType.STRING,  JsonFormat.REGEX,        SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "^.*$")),
    JSON_POINTER(   FormatMapping(JsonType.STRING,  JsonFormat.JSON_POINTER, SqlTypes.VARCHAR,     String::class,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "/foo/bar")),
    BYTE(           FormatMapping(JsonType.STRING,  JsonFormat.BYTE,         SqlTypes.VARBINARY,   ByteArray::class,  ComposeWidget.FILE_PICKER,          HtmlInputType.FILE,           ComfyType.STRING_)),
    BINARY(         FormatMapping(JsonType.STRING,  JsonFormat.BINARY,       SqlTypes.BLOB,        ByteArray::class,  ComposeWidget.FILE_PICKER,          HtmlInputType.FILE,           ComfyType.STRING_)),
    HIDDEN(         FormatMapping(JsonType.STRING,  JsonFormat.HIDDEN,       SqlTypes.VARCHAR,     String::class,     ComposeWidget.HIDDEN_FIELD,         HtmlInputType.HIDDEN,         ComfyType.STRING_)),
    GEOJSON(        FormatMapping(JsonType.OBJECT,  JsonFormat.GEOJSON,      SqlTypes.OTHER,       JsonObject::class, ComposeWidget.MAP_PICKER,           HtmlInputType.TEXTAREA,       ComfyType.STRING_, "{\"type\":\"Point\",\"coordinates\":[0,0]}")),
    JSON_OBJECT(    FormatMapping(JsonType.OBJECT,  JsonFormat.JSON,         SqlTypes.OTHER,       JsonObject::class, ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    JSON_ARRAY(     FormatMapping(JsonType.ARRAY,   JsonFormat.JSON,         SqlTypes.ARRAY,       JsonArray::class,  ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    INT32(          FormatMapping(JsonType.INTEGER, JsonFormat.INT32,        SqlTypes.INTEGER,     Int::class,        ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.INT_)),
    INT64(          FormatMapping(JsonType.INTEGER, JsonFormat.INT64,        SqlTypes.BIGINT,      Long::class,       ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.INT_)),
    FLOAT_(         FormatMapping(JsonType.NUMBER,  JsonFormat.FLOAT,        SqlTypes.REAL,        Float::class,      ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    DOUBLE_(        FormatMapping(JsonType.NUMBER,  JsonFormat.DOUBLE,       SqlTypes.DOUBLE,      Double::class,     ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    RANGE(          FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        Float::class,      ComposeWidget.RANGE_SLIDER,         HtmlInputType.RANGE,          ComfyType.FLOAT_)),
    KNOB(           FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        Float::class,      ComposeWidget.KNOB,                 HtmlInputType.RANGE,          ComfyType.FLOAT_)),
    NUMBER_FIELD(   FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        Float::class,      ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    // Date/time *parts* — defined after the generic numeric forms so
    // SQL→FormatType dispatch picks INT32 / INT64 / FLOAT first.
    YEAR(           FormatMapping(JsonType.INTEGER, JsonFormat.YEAR,         SqlTypes.INTEGER,     Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "YYYY")),
    QUARTER(        FormatMapping(JsonType.INTEGER, JsonFormat.QUARTER,      SqlTypes.SMALLINT,    Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "1..4")),
    DAY(            FormatMapping(JsonType.INTEGER, JsonFormat.DAY,          SqlTypes.SMALLINT,    Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "1..31")),
    HOUR(           FormatMapping(JsonType.INTEGER, JsonFormat.HOUR,         SqlTypes.SMALLINT,    Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..23")),
    MINUTE(         FormatMapping(JsonType.INTEGER, JsonFormat.MINUTE,       SqlTypes.SMALLINT,    Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..59")),
    SECOND(         FormatMapping(JsonType.INTEGER, JsonFormat.SECOND,       SqlTypes.SMALLINT,    Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..59")),
    MILLISECOND(    FormatMapping(JsonType.INTEGER, JsonFormat.MILLISECOND,  SqlTypes.INTEGER,     Int::class,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..999")),
    BOOL(           FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     Boolean::class,    ComposeWidget.SWITCH,               HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    CHECKBOX(       FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     Boolean::class,    ComposeWidget.CHECKBOX,             HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    ENUM(           FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.DROPDOWN_MENU,        HtmlInputType.SELECT,         ComfyType.COMBO)),
    RADIO(          FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     String::class,     ComposeWidget.RADIO_GROUP,          HtmlInputType.RADIO,          ComfyType.COMBO)),
    MULTI_SELECT(   FormatMapping(JsonType.ARRAY,   JsonFormat.ENUM,         SqlTypes.ARRAY,       List::class,       ComposeWidget.CHECKBOX_GROUP,       HtmlInputType.SELECT_MULTI,   ComfyType.COMBO)),
    // ComfyUI domain types
    IMAGE(              FormatMapping(JsonType.STRING, JsonFormat.IMAGE,        SqlTypes.VARCHAR, String::class,     ComposeWidget.IMAGE_UPLOAD,      HtmlInputType.FILE,   ComfyType.IMAGE)),
    LATENT(             FormatMapping(JsonType.OBJECT, JsonFormat.LATENT,       SqlTypes.OTHER,   JsonObject::class, ComposeWidget.LATENT_PREVIEW,    HtmlInputType.HIDDEN, ComfyType.LATENT)),
    MASK(               FormatMapping(JsonType.STRING, JsonFormat.MASK,         SqlTypes.VARCHAR, String::class,     ComposeWidget.MASK_EDITOR,       HtmlInputType.FILE,   ComfyType.MASK)),
    MODEL(              FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.MODEL,            "model.safetensors")),
    CLIP(               FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CLIP)),
    VAE(                FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.VAE)),
    CONDITIONING(       FormatMapping(JsonType.OBJECT, JsonFormat.CONDITIONING, SqlTypes.OTHER,   JsonObject::class, ComposeWidget.CONDITIONING_VIEW, HtmlInputType.HIDDEN, ComfyType.CONDITIONING)),
    CONTROL_NET(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CONTROL_NET)),
    STYLE_MODEL(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.STYLE_MODEL)),
    CLIP_VISION(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CLIP_VISION)),
    CLIP_VISION_OUTPUT( FormatMapping(JsonType.OBJECT, JsonFormat.JSON,         SqlTypes.OTHER,   JsonObject::class, ComposeWidget.OUTLINED_TEXT_FIELD,HtmlInputType.HIDDEN,ComfyType.CLIP_VISION_OUTPUT)),
    UPSCALE_MODEL(      FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, String::class,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.UPSCALE_MODEL)),
    AUDIO(              FormatMapping(JsonType.STRING, JsonFormat.AUDIO,        SqlTypes.VARCHAR, String::class,     ComposeWidget.AUDIO_PLAYER,      HtmlInputType.FILE,   ComfyType.AUDIO)),
    VIDEO(              FormatMapping(JsonType.STRING, JsonFormat.VIDEO,        SqlTypes.VARCHAR, String::class,     ComposeWidget.VIDEO_PLAYER,      HtmlInputType.FILE,   ComfyType.VIDEO)),
    WEBCAM(             FormatMapping(JsonType.STRING, JsonFormat.IMAGE,        SqlTypes.VARCHAR, String::class,     ComposeWidget.WEBCAM_CAPTURE,    HtmlInputType.HIDDEN, ComfyType.WEBCAM)),
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
