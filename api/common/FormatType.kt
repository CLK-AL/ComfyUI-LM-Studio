// Five-way bridge: one enum value per format, all fields are typed.
// Mirror of comfyui_openapi_node/format_type.py.
// Covers: full HTML5 form roster, Compose Multiplatform widgets,
// every ComfyUI primitive AND domain type (IMAGE / LATENT / MASK /
// MODEL / CLIP / VAE / CONDITIONING / CONTROL_NET / STYLE_MODEL /
// CLIP_VISION / CLIP_VISION_OUTPUT / UPSCALE_MODEL / AUDIO / VIDEO /
// WEBCAM), date/time-part inputs (year, quarter, day, hour, minute,
// second, millisecond, timezone), and dynamic-UI flags.

import kotlin.reflect.KClass

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
    // ICU / Unicode locale + calendar + formatter integration
    LOCALE("locale"),
    CALENDAR_SYSTEM("calendar-system"),
    PERSON_NAME("person-name"),
    NUMBER_FMT("number-fmt"),
    DECIMAL("decimal"),
    CURRENCY("currency"),
    MEASURE("measure"),
    UNIT("unit"),
    ORDINAL("ordinal"),
    PLURAL("plural"),
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

enum class CalendarSystem(val value: String) {
    GREGORIAN("gregorian"),
    BUDDHIST("buddhist"),
    CHINESE("chinese"),
    COPTIC("coptic"),
    ETHIOPIC("ethiopic"),
    ETHIOPIC_AMETE_ALEM("ethiopic-amete-alem"),
    HEBREW("hebrew"),
    INDIAN("indian"),
    ISLAMIC("islamic"),
    ISLAMIC_CIVIL("islamic-civil"),
    ISLAMIC_TBLA("islamic-tbla"),
    ISLAMIC_UMALQURA("islamic-umalqura"),
    ISLAMIC_RGSA("islamic-rgsa"),
    ISO8601("iso8601"),
    JAPANESE("japanese"),
    PERSIAN("persian"),
    ROC("roc"),
    DANGI("dangi");
}

enum class IcalWeekDay(val value: String) {
    SU("SU"), MO("MO"), TU("TU"), WE("WE"),
    TH("TH"), FR("FR"), SA("SA");
}

enum class IcalFreq(val value: String) {
    SECONDLY("SECONDLY"), MINUTELY("MINUTELY"), HOURLY("HOURLY"),
    DAILY("DAILY"), WEEKLY("WEEKLY"),
    MONTHLY("MONTHLY"), YEARLY("YEARLY");
}

// ----- ICU / CLDR number + unit + name vocabulary ----------------------
/** ICU `NumberFormatter` notation styles (CLDR). */
enum class IcuNumberStyle(val value: String) {
    DECIMAL("decimal"),
    PERCENT("percent"),
    PERMILLE("permille"),
    SCIENTIFIC("scientific"),
    ENGINEERING("engineering"),
    COMPACT_SHORT("compact-short"),
    COMPACT_LONG("compact-long"),
    CURRENCY("currency"),
    UNIT("unit"),
    ACCOUNTING("accounting");
}

/** CLDR plural category (RFC 6350 / CLDR plural rules). */
enum class IcuPluralCategory(val value: String) {
    ZERO("zero"), ONE("one"), TWO("two"),
    FEW("few"),  MANY("many"), OTHER("other");
}

/** CLDR measure-unit identifiers — the most common subset ICU ships.
 *  Full list: https://cldr.unicode.org/index/charts/summary/units */
enum class IcuUnit(val value: String) {
    // length
    METER("length-meter"), KILOMETER("length-kilometer"),
    CENTIMETER("length-centimeter"), MILLIMETER("length-millimeter"),
    INCH("length-inch"), FOOT("length-foot"), YARD("length-yard"),
    MILE("length-mile"),
    // mass
    GRAM("mass-gram"), KILOGRAM("mass-kilogram"),
    MILLIGRAM("mass-milligram"), POUND("mass-pound"), OUNCE("mass-ounce"),
    // volume
    LITER("volume-liter"), MILLILITER("volume-milliliter"),
    GALLON("volume-gallon"), FLUID_OUNCE("volume-fluid-ounce"),
    // duration
    SECOND("duration-second"), MINUTE("duration-minute"),
    HOUR("duration-hour"), DAY("duration-day"),
    WEEK("duration-week"), MONTH("duration-month"), YEAR("duration-year"),
    // speed
    METER_PER_SECOND("speed-meter-per-second"),
    KILOMETER_PER_HOUR("speed-kilometer-per-hour"),
    MILE_PER_HOUR("speed-mile-per-hour"),
    // temperature
    CELSIUS("temperature-celsius"),
    FAHRENHEIT("temperature-fahrenheit"), KELVIN("temperature-kelvin"),
    // digital
    BIT("digital-bit"), BYTE_("digital-byte"),
    KILOBYTE("digital-kilobyte"), MEGABYTE("digital-megabyte"),
    GIGABYTE("digital-gigabyte"), TERABYTE("digital-terabyte"),
    // angle / area / energy — light coverage
    DEGREE("angle-degree"), RADIAN("angle-radian"),
    HECTARE("area-hectare"), ACRE("area-acre"),
    JOULE("energy-joule"), CALORIE("energy-calorie");
}

/** ISO 4217 currency codes — representative set. Full alpha-3 list
 *  comes from the runtime (java.util.Currency.getAvailableCurrencies). */
enum class IcuCurrency(val code: String) {
    USD("USD"), EUR("EUR"), GBP("GBP"), JPY("JPY"),
    CNY("CNY"), INR("INR"), BRL("BRL"), CAD("CAD"),
    AUD("AUD"), CHF("CHF"), SEK("SEK"), NOK("NOK"),
    DKK("DKK"), RUB("RUB"), KRW("KRW"), MXN("MXN"),
    ZAR("ZAR"), SGD("SGD"), HKD("HKD"), NZD("NZD");
}

/** ICU `PersonNameFormatter` styles / lengths. */
enum class IcuPersonNameStyle(val value: String) {
    LONG("long"), MEDIUM("medium"), SHORT("short"),
    GIVEN_FIRST("given-first"), SURNAME_FIRST("surname-first"),
    INFORMAL("informal"), FORMAL("formal"),
    MONOGRAM("monogram"), INITIAL("initial");
}

/** Single-row bridge. `kclass` is the [KClassEnum] whose members carry
 *  paired [JClassEnum] and [PyClassEnum] references, so FormatType.kt
 *  really is the one-stop type bridge across Kotlin / Java / Python. */
data class FormatMapping(
    val jsonType:   JsonType,
    val jsonFormat: JsonFormat,
    val sqlType:    SqlTypes,
    val kclass:     KClassEnum,
    val composable: ComposeWidget,
    val htmlInput:  HtmlInputType,
    val comfy:      ComfyType,
    val placeholder:String = "",
) {
    val jclass:  JClassEnum  get() = kclass.jclass
    val pyclass: PyClassEnum get() = kclass.pyclass
}

enum class FormatType(val mapping: FormatMapping) {
    TEXT(           FormatMapping(JsonType.STRING,  JsonFormat.NONE,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_)),
    TEXTAREA(       FormatMapping(JsonType.STRING,  JsonFormat.TEXTAREA,     SqlTypes.LONGVARCHAR, KClassEnum.STRING,     ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    DYNAMIC_PROMPT( FormatMapping(JsonType.STRING,  JsonFormat.TEXTAREA,     SqlTypes.LONGVARCHAR, KClassEnum.STRING,     ComposeWidget.DYNAMIC_PROMPT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    MARKDOWN(       FormatMapping(JsonType.STRING,  JsonFormat.MARKDOWN,     SqlTypes.LONGVARCHAR, KClassEnum.STRING,     ComposeWidget.MARKDOWN_VIEW,        HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    PASSWORD(       FormatMapping(JsonType.STRING,  JsonFormat.PASSWORD,     SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.PASSWORD_FIELD,       HtmlInputType.PASSWORD,       ComfyType.STRING_)),
    EMAIL(          FormatMapping(JsonType.STRING,  JsonFormat.EMAIL,        SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.EMAIL,          ComfyType.STRING_, "user@example.com")),
    TEL(            FormatMapping(JsonType.STRING,  JsonFormat.TEL,          SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEL,            ComfyType.STRING_, "+1 555 0100")),
    URL(            FormatMapping(JsonType.STRING,  JsonFormat.URI,          SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.URL,            ComfyType.STRING_, "https://…")),
    SEARCH(         FormatMapping(JsonType.STRING,  JsonFormat.SEARCH,       SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.SEARCH_FIELD,         HtmlInputType.SEARCH,         ComfyType.STRING_, "Search…")),
    UUID(           FormatMapping(JsonType.STRING,  JsonFormat.UUID,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "00000000-0000-0000-0000-000000000000")),
    COLOR(          FormatMapping(JsonType.STRING,  JsonFormat.COLOR,        SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.COLOR_PICKER,         HtmlInputType.COLOR,          ComfyType.STRING_, "#RRGGBB")),
    DATE(           FormatMapping(JsonType.STRING,  JsonFormat.DATE,         SqlTypes.DATE,        KClassEnum.LOCAL_DATE, ComposeWidget.DATE_PICKER,          HtmlInputType.DATE,           ComfyType.STRING_, "YYYY-MM-DD")),
    TIME(           FormatMapping(JsonType.STRING,  JsonFormat.TIME,         SqlTypes.TIME,        KClassEnum.LOCAL_TIME, ComposeWidget.TIME_PICKER,          HtmlInputType.TIME,           ComfyType.STRING_, "HH:MM:SS")),
    DATETIME(       FormatMapping(JsonType.STRING,  JsonFormat.DATE_TIME,    SqlTypes.TIMESTAMP,   KClassEnum.INSTANT, ComposeWidget.DATETIME_PICKER,      HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_, "YYYY-MM-DDTHH:MM:SSZ")),
    MONTH(          FormatMapping(JsonType.STRING,  JsonFormat.MONTH,        SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.MONTH_PICKER,         HtmlInputType.MONTH,          ComfyType.STRING_, "YYYY-MM")),
    WEEK(           FormatMapping(JsonType.STRING,  JsonFormat.WEEK,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.WEEK_PICKER,          HtmlInputType.WEEK,           ComfyType.STRING_, "YYYY-Www")),
    TIMEZONE(       FormatMapping(JsonType.STRING,  JsonFormat.TIMEZONE,     SqlTypes.VARCHAR,     KClassEnum.TIME_ZONE,   ComposeWidget.DROPDOWN_MENU,        HtmlInputType.SELECT,         ComfyType.COMBO,  "Europe/London")),
    DURATION(       FormatMapping(JsonType.STRING,  JsonFormat.DURATION,     SqlTypes.VARCHAR,     KClassEnum.DURATION,   ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "P1DT2H")),
    IPV4(           FormatMapping(JsonType.STRING,  JsonFormat.IPV4,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "0.0.0.0")),
    IPV6(           FormatMapping(JsonType.STRING,  JsonFormat.IPV6,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "::1")),
    HOSTNAME(       FormatMapping(JsonType.STRING,  JsonFormat.HOSTNAME,     SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "example.com")),
    REGEX(          FormatMapping(JsonType.STRING,  JsonFormat.REGEX,        SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "^.*$")),
    JSON_POINTER(   FormatMapping(JsonType.STRING,  JsonFormat.JSON_POINTER, SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.TEXT_FIELD,           HtmlInputType.TEXT,           ComfyType.STRING_, "/foo/bar")),
    BYTE(           FormatMapping(JsonType.STRING,  JsonFormat.BYTE,         SqlTypes.VARBINARY,   KClassEnum.BYTE_ARRAY,  ComposeWidget.FILE_PICKER,          HtmlInputType.FILE,           ComfyType.STRING_)),
    BINARY(         FormatMapping(JsonType.STRING,  JsonFormat.BINARY,       SqlTypes.BLOB,        KClassEnum.BYTE_ARRAY,  ComposeWidget.FILE_PICKER,          HtmlInputType.FILE,           ComfyType.STRING_)),
    HIDDEN(         FormatMapping(JsonType.STRING,  JsonFormat.HIDDEN,       SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.HIDDEN_FIELD,         HtmlInputType.HIDDEN,         ComfyType.STRING_)),
    GEOJSON(        FormatMapping(JsonType.OBJECT,  JsonFormat.GEOJSON,      SqlTypes.OTHER,       KClassEnum.JSON_OBJECT, ComposeWidget.MAP_PICKER,           HtmlInputType.TEXTAREA,       ComfyType.STRING_, "{\"type\":\"Point\",\"coordinates\":[0,0]}")),
    JSON_OBJECT(    FormatMapping(JsonType.OBJECT,  JsonFormat.JSON,         SqlTypes.OTHER,       KClassEnum.JSON_OBJECT, ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    JSON_ARRAY(     FormatMapping(JsonType.ARRAY,   JsonFormat.JSON,         SqlTypes.ARRAY,       KClassEnum.JSON_ARRAY,  ComposeWidget.OUTLINED_TEXT_FIELD,  HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    INT32(          FormatMapping(JsonType.INTEGER, JsonFormat.INT32,        SqlTypes.INTEGER,     KClassEnum.INT,        ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.INT_)),
    INT64(          FormatMapping(JsonType.INTEGER, JsonFormat.INT64,        SqlTypes.BIGINT,      KClassEnum.LONG,       ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.INT_)),
    FLOAT_(         FormatMapping(JsonType.NUMBER,  JsonFormat.FLOAT,        SqlTypes.REAL,        KClassEnum.FLOAT,      ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    DOUBLE_(        FormatMapping(JsonType.NUMBER,  JsonFormat.DOUBLE,       SqlTypes.DOUBLE,      KClassEnum.DOUBLE,     ComposeWidget.SLIDER,               HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    RANGE(          FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        KClassEnum.FLOAT,      ComposeWidget.RANGE_SLIDER,         HtmlInputType.RANGE,          ComfyType.FLOAT_)),
    KNOB(           FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        KClassEnum.FLOAT,      ComposeWidget.KNOB,                 HtmlInputType.RANGE,          ComfyType.FLOAT_)),
    NUMBER_FIELD(   FormatMapping(JsonType.NUMBER,  JsonFormat.NONE,         SqlTypes.REAL,        KClassEnum.FLOAT,      ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.FLOAT_)),
    // Date/time *parts* — defined after the generic numeric forms so
    // SQL→FormatType dispatch picks INT32 / INT64 / FLOAT first.
    YEAR(           FormatMapping(JsonType.INTEGER, JsonFormat.YEAR,         SqlTypes.INTEGER,     KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "YYYY")),
    QUARTER(        FormatMapping(JsonType.INTEGER, JsonFormat.QUARTER,      SqlTypes.SMALLINT,    KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "1..4")),
    DAY(            FormatMapping(JsonType.INTEGER, JsonFormat.DAY,          SqlTypes.SMALLINT,    KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "1..31")),
    HOUR(           FormatMapping(JsonType.INTEGER, JsonFormat.HOUR,         SqlTypes.SMALLINT,    KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..23")),
    MINUTE(         FormatMapping(JsonType.INTEGER, JsonFormat.MINUTE,       SqlTypes.SMALLINT,    KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..59")),
    SECOND(         FormatMapping(JsonType.INTEGER, JsonFormat.SECOND,       SqlTypes.SMALLINT,    KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..59")),
    MILLISECOND(    FormatMapping(JsonType.INTEGER, JsonFormat.MILLISECOND,  SqlTypes.INTEGER,     KClassEnum.INT,        ComposeWidget.NUMBER_FIELD,         HtmlInputType.NUMBER,         ComfyType.INT_,   "0..999")),
    BOOL(           FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     KClassEnum.BOOLEAN,    ComposeWidget.SWITCH,               HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    CHECKBOX(       FormatMapping(JsonType.BOOLEAN, JsonFormat.NONE,         SqlTypes.BOOLEAN,     KClassEnum.BOOLEAN,    ComposeWidget.CHECKBOX,             HtmlInputType.CHECKBOX,       ComfyType.BOOLEAN_)),
    ENUM(           FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.DROPDOWN_MENU,        HtmlInputType.SELECT,         ComfyType.COMBO)),
    RADIO(          FormatMapping(JsonType.STRING,  JsonFormat.ENUM,         SqlTypes.VARCHAR,     KClassEnum.STRING,     ComposeWidget.RADIO_GROUP,          HtmlInputType.RADIO,          ComfyType.COMBO)),
    MULTI_SELECT(   FormatMapping(JsonType.ARRAY,   JsonFormat.ENUM,         SqlTypes.ARRAY,       KClassEnum.LIST,       ComposeWidget.CHECKBOX_GROUP,       HtmlInputType.SELECT_MULTI,   ComfyType.COMBO)),
    // ComfyUI domain types
    IMAGE(              FormatMapping(JsonType.STRING, JsonFormat.IMAGE,        SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.IMAGE_UPLOAD,      HtmlInputType.FILE,   ComfyType.IMAGE)),
    LATENT(             FormatMapping(JsonType.OBJECT, JsonFormat.LATENT,       SqlTypes.OTHER,   KClassEnum.JSON_OBJECT, ComposeWidget.LATENT_PREVIEW,    HtmlInputType.HIDDEN, ComfyType.LATENT)),
    MASK(               FormatMapping(JsonType.STRING, JsonFormat.MASK,         SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MASK_EDITOR,       HtmlInputType.FILE,   ComfyType.MASK)),
    MODEL(              FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.MODEL,            "model.safetensors")),
    CLIP(               FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CLIP)),
    VAE(                FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.VAE)),
    CONDITIONING(       FormatMapping(JsonType.OBJECT, JsonFormat.CONDITIONING, SqlTypes.OTHER,   KClassEnum.JSON_OBJECT, ComposeWidget.CONDITIONING_VIEW, HtmlInputType.HIDDEN, ComfyType.CONDITIONING)),
    CONTROL_NET(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CONTROL_NET)),
    STYLE_MODEL(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.STYLE_MODEL)),
    CLIP_VISION(        FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.CLIP_VISION)),
    CLIP_VISION_OUTPUT( FormatMapping(JsonType.OBJECT, JsonFormat.JSON,         SqlTypes.OTHER,   KClassEnum.JSON_OBJECT, ComposeWidget.OUTLINED_TEXT_FIELD,HtmlInputType.HIDDEN,ComfyType.CLIP_VISION_OUTPUT)),
    UPSCALE_MODEL(      FormatMapping(JsonType.STRING, JsonFormat.MODEL_REF,    SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.MODEL_PICKER,      HtmlInputType.SELECT, ComfyType.UPSCALE_MODEL)),
    AUDIO(              FormatMapping(JsonType.STRING, JsonFormat.AUDIO,        SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.AUDIO_PLAYER,      HtmlInputType.FILE,   ComfyType.AUDIO)),
    VIDEO(              FormatMapping(JsonType.STRING, JsonFormat.VIDEO,        SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.VIDEO_PLAYER,      HtmlInputType.FILE,   ComfyType.VIDEO)),
    WEBCAM(             FormatMapping(JsonType.STRING, JsonFormat.IMAGE,        SqlTypes.VARCHAR, KClassEnum.STRING,     ComposeWidget.WEBCAM_CAPTURE,    HtmlInputType.HIDDEN, ComfyType.WEBCAM)),

    // Date/time *parts* — compound-date atoms.
    MONTH_OF_YEAR( FormatMapping(JsonType.INTEGER, JsonFormat.MONTH_OF_YEAR, SqlTypes.SMALLINT, KClassEnum.INT, ComposeWidget.NUMBER_FIELD, HtmlInputType.NUMBER, ComfyType.INT_, "1..12")),
    DAY_OF_WEEK(   FormatMapping(JsonType.INTEGER, JsonFormat.DAY_OF_WEEK,   SqlTypes.SMALLINT, KClassEnum.INT, ComposeWidget.NUMBER_FIELD, HtmlInputType.NUMBER, ComfyType.INT_, "1..7")),
    DAY_OF_YEAR(   FormatMapping(JsonType.INTEGER, JsonFormat.DAY_OF_YEAR,   SqlTypes.SMALLINT, KClassEnum.INT, ComposeWidget.NUMBER_FIELD, HtmlInputType.NUMBER, ComfyType.INT_, "1..366")),
    ISO_WEEK_NUM(  FormatMapping(JsonType.INTEGER, JsonFormat.ISO_WEEK_NUM,  SqlTypes.SMALLINT, KClassEnum.INT, ComposeWidget.NUMBER_FIELD, HtmlInputType.NUMBER, ComfyType.INT_, "1..53")),
    OFFSET(        FormatMapping(JsonType.STRING,  JsonFormat.OFFSET,        SqlTypes.VARCHAR,  KClassEnum.STRING, ComposeWidget.TEXT_FIELD,  HtmlInputType.TEXT,   ComfyType.STRING_, "+00:00")),

    // vCard 4.0 (RFC 6350) — text-typed properties extending string.
    VCARD_FN(          FormatMapping(JsonType.STRING, JsonFormat.VCARD_FN,         SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "Ada Lovelace")),
    VCARD_N(           FormatMapping(JsonType.STRING, JsonFormat.VCARD_N,          SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "Lovelace;Ada;Augusta;Hon.;")),
    VCARD_NICKNAME(    FormatMapping(JsonType.STRING, JsonFormat.VCARD_NICKNAME,   SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    VCARD_BDAY(        FormatMapping(JsonType.STRING, JsonFormat.VCARD_BDAY,       SqlTypes.DATE,        KClassEnum.LOCAL_DATE,ComposeWidget.DATE_PICKER,         HtmlInputType.DATE,           ComfyType.STRING_, "YYYY-MM-DD")),
    VCARD_ANNIVERSARY( FormatMapping(JsonType.STRING, JsonFormat.VCARD_ANNIVERSARY,SqlTypes.DATE,        KClassEnum.LOCAL_DATE,ComposeWidget.DATE_PICKER,         HtmlInputType.DATE,           ComfyType.STRING_, "YYYY-MM-DD")),
    VCARD_GENDER(      FormatMapping(JsonType.STRING, JsonFormat.VCARD_GENDER,     SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "M / F / O / N / U")),
    VCARD_ADR(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_ADR,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_, ";;Street;City;Region;ZIP;Country")),
    VCARD_TEL(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_TEL,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEL,            ComfyType.STRING_, "+1 555 0100")),
    VCARD_EMAIL(       FormatMapping(JsonType.STRING, JsonFormat.VCARD_EMAIL,      SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.EMAIL,          ComfyType.STRING_, "user@example.com")),
    VCARD_GEO(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_GEO,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.MAP_PICKER,          HtmlInputType.TEXT,           ComfyType.STRING_, "geo:51.5074,-0.1278")),
    VCARD_TZ(          FormatMapping(JsonType.STRING, JsonFormat.VCARD_TZ,         SqlTypes.VARCHAR,     KClassEnum.TIME_ZONE,  ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "Europe/London")),
    VCARD_TITLE(       FormatMapping(JsonType.STRING, JsonFormat.VCARD_TITLE,      SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    VCARD_ROLE(        FormatMapping(JsonType.STRING, JsonFormat.VCARD_ROLE,       SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    VCARD_ORG(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_ORG,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    VCARD_NOTE(        FormatMapping(JsonType.STRING, JsonFormat.VCARD_NOTE,       SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    VCARD_URL(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_URL,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.URL,            ComfyType.STRING_, "https://…")),
    VCARD_UID(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_UID,        SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "urn:uuid:…")),
    VCARD_REV(         FormatMapping(JsonType.STRING, JsonFormat.VCARD_REV,        SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),
    VCARD_CATEGORIES(  FormatMapping(JsonType.STRING, JsonFormat.VCARD_CATEGORIES, SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "tag1,tag2,tag3")),

    // iCalendar (RFC 5545)
    ICAL_DTSTART(      FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DTSTART,     SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_, "YYYYMMDDTHHMMSSZ")),
    ICAL_DTEND(        FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DTEND,       SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),
    ICAL_DTSTAMP(      FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DTSTAMP,     SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),
    ICAL_DUE(          FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DUE,         SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),
    ICAL_COMPLETED(    FormatMapping(JsonType.STRING,  JsonFormat.ICAL_COMPLETED,   SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),
    ICAL_DURATION(     FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DURATION,    SqlTypes.VARCHAR,     KClassEnum.DURATION,  ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "P1DT2H")),
    ICAL_LOCATION(     FormatMapping(JsonType.STRING,  JsonFormat.ICAL_LOCATION,    SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "1 Infinite Loop")),
    ICAL_DESCRIPTION(  FormatMapping(JsonType.STRING,  JsonFormat.ICAL_DESCRIPTION, SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    ICAL_SUMMARY(      FormatMapping(JsonType.STRING,  JsonFormat.ICAL_SUMMARY,     SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    ICAL_COMMENT(      FormatMapping(JsonType.STRING,  JsonFormat.ICAL_COMMENT,     SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    ICAL_STATUS(       FormatMapping(JsonType.STRING,  JsonFormat.ICAL_STATUS,      SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "TENTATIVE / CONFIRMED / CANCELLED / NEEDS-ACTION / COMPLETED / IN-PROCESS / DRAFT / FINAL")),
    ICAL_CLASS(        FormatMapping(JsonType.STRING,  JsonFormat.ICAL_CLASS,       SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "PUBLIC / PRIVATE / CONFIDENTIAL")),
    ICAL_TRANSP(       FormatMapping(JsonType.STRING,  JsonFormat.ICAL_TRANSP,      SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "OPAQUE / TRANSPARENT")),
    ICAL_PRIORITY(     FormatMapping(JsonType.INTEGER, JsonFormat.ICAL_PRIORITY,    SqlTypes.SMALLINT,    KClassEnum.INT,       ComposeWidget.NUMBER_FIELD,        HtmlInputType.NUMBER,         ComfyType.INT_,    "0..9")),
    ICAL_SEQUENCE(     FormatMapping(JsonType.INTEGER, JsonFormat.ICAL_SEQUENCE,    SqlTypes.INTEGER,     KClassEnum.INT,       ComposeWidget.NUMBER_FIELD,        HtmlInputType.NUMBER,         ComfyType.INT_)),
    ICAL_GEO(          FormatMapping(JsonType.STRING,  JsonFormat.ICAL_GEO,         SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.MAP_PICKER,          HtmlInputType.TEXT,           ComfyType.STRING_, "51.5074;-0.1278")),
    ICAL_RRULE(        FormatMapping(JsonType.STRING,  JsonFormat.ICAL_RRULE,       SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_, "FREQ=WEEKLY;BYDAY=MO,WE,FR")),
    ICAL_RDATE(        FormatMapping(JsonType.STRING,  JsonFormat.ICAL_RDATE,       SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    ICAL_EXDATE(       FormatMapping(JsonType.STRING,  JsonFormat.ICAL_EXDATE,      SqlTypes.LONGVARCHAR, KClassEnum.STRING,    ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA,       ComfyType.STRING_)),
    ICAL_ATTENDEE(     FormatMapping(JsonType.STRING,  JsonFormat.ICAL_ATTENDEE,    SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.EMAIL,          ComfyType.STRING_, "mailto:user@example.com")),
    ICAL_ORGANIZER(    FormatMapping(JsonType.STRING,  JsonFormat.ICAL_ORGANIZER,   SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.EMAIL,          ComfyType.STRING_, "mailto:org@example.com")),
    ICAL_CATEGORIES(   FormatMapping(JsonType.STRING,  JsonFormat.ICAL_CATEGORIES,  SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "tag1,tag2")),
    ICAL_UID(          FormatMapping(JsonType.STRING,  JsonFormat.ICAL_UID,         SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_, "uid@example.com")),
    ICAL_TZID(         FormatMapping(JsonType.STRING,  JsonFormat.ICAL_TZID,        SqlTypes.VARCHAR,     KClassEnum.TIME_ZONE,  ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "Europe/London")),
    ICAL_METHOD(       FormatMapping(JsonType.STRING,  JsonFormat.ICAL_METHOD,      SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "PUBLISH / REQUEST / REPLY / ADD / CANCEL / REFRESH / COUNTER / DECLINECOUNTER")),
    ICAL_CALSCALE(     FormatMapping(JsonType.STRING,  JsonFormat.ICAL_CALSCALE,    SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.DROPDOWN_MENU,       HtmlInputType.SELECT,         ComfyType.COMBO,   "GREGORIAN")),
    ICAL_RELATED_TO(   FormatMapping(JsonType.STRING,  JsonFormat.ICAL_RELATED_TO,  SqlTypes.VARCHAR,     KClassEnum.STRING,    ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,           ComfyType.STRING_)),
    ICAL_RECUR_ID(     FormatMapping(JsonType.STRING,  JsonFormat.ICAL_RECUR_ID,    SqlTypes.TIMESTAMP,   KClassEnum.INSTANT,ComposeWidget.DATETIME_PICKER,     HtmlInputType.DATETIME_LOCAL, ComfyType.STRING_)),

    // Delimited-row cell formats (POI XLSX / CSV / TSV / vCard / iCal)
    SEMI_DELIMITED(    FormatMapping(JsonType.STRING, JsonFormat.SEMI_DELIMITED, SqlTypes.LONGVARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,          HtmlInputType.TEXT,     ComfyType.STRING_, "a;b;c")),
    CSV_ROW(           FormatMapping(JsonType.STRING, JsonFormat.CSV,            SqlTypes.LONGVARCHAR, KClassEnum.STRING, ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA, ComfyType.STRING_, "a,b,c")),
    TSV_ROW(           FormatMapping(JsonType.STRING, JsonFormat.TSV,            SqlTypes.LONGVARCHAR, KClassEnum.STRING, ComposeWidget.OUTLINED_TEXT_FIELD, HtmlInputType.TEXTAREA, ComfyType.STRING_, "a\tb\tc")),

    // ICU / Unicode locale + calendar + formatter integration
    LOCALE(            FormatMapping(JsonType.STRING, JsonFormat.LOCALE,          SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.DROPDOWN_MENU, HtmlInputType.SELECT, ComfyType.COMBO,   "en-US")),
    CALENDAR_SYSTEM(   FormatMapping(JsonType.STRING, JsonFormat.CALENDAR_SYSTEM, SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.DROPDOWN_MENU, HtmlInputType.SELECT, ComfyType.COMBO,   "gregorian")),
    PERSON_NAME(       FormatMapping(JsonType.STRING, JsonFormat.PERSON_NAME,     SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,    HtmlInputType.TEXT,   ComfyType.STRING_, "Ada Lovelace")),
    NUMBER_FMT(        FormatMapping(JsonType.STRING, JsonFormat.NUMBER_FMT,      SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,    HtmlInputType.TEXT,   ComfyType.STRING_, "1,234.56")),
    DECIMAL(           FormatMapping(JsonType.STRING, JsonFormat.DECIMAL,         SqlTypes.DECIMAL, KClassEnum.STRING, ComposeWidget.NUMBER_FIELD,  HtmlInputType.NUMBER, ComfyType.STRING_, "0.00")),
    CURRENCY(          FormatMapping(JsonType.STRING, JsonFormat.CURRENCY,        SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,    HtmlInputType.TEXT,   ComfyType.STRING_, "USD 1,234.56")),
    MEASURE(           FormatMapping(JsonType.STRING, JsonFormat.MEASURE,         SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,    HtmlInputType.TEXT,   ComfyType.STRING_, "5 kg")),
    UNIT(              FormatMapping(JsonType.STRING, JsonFormat.UNIT,            SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.DROPDOWN_MENU, HtmlInputType.SELECT, ComfyType.COMBO,   "length-meter")),
    ORDINAL(           FormatMapping(JsonType.STRING, JsonFormat.ORDINAL,         SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.TEXT_FIELD,    HtmlInputType.TEXT,   ComfyType.STRING_, "1st")),
    PLURAL(            FormatMapping(JsonType.STRING, JsonFormat.PLURAL,          SqlTypes.VARCHAR, KClassEnum.STRING, ComposeWidget.DROPDOWN_MENU, HtmlInputType.SELECT, ComfyType.COMBO,   "one / other")),
    ;

    val kclassFqn: String get() = mapping.kclass.fqn
    val jclassFqn: String get() = mapping.jclass.fqn
    val pyclassFqn:String get() = mapping.pyclass.fqn

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
            KClassEnum.fromKClass(kcls)?.let(::fromKClassEnum) ?: TEXT

        fun fromKClassEnum(ke: KClassEnum): FormatType =
            entries.firstOrNull { it.mapping.kclass == ke } ?: TEXT

        fun fromJClass(jcls: Class<*>): FormatType =
            JClassEnum.fromJClass(jcls)?.let(::fromJClassEnum) ?: TEXT

        fun fromJClassEnum(je: JClassEnum): FormatType =
            entries.firstOrNull { it.mapping.jclass == je } ?: TEXT

        fun fromPyClass(fqn: String): FormatType =
            PyClassEnum.fromFqn(fqn)?.let(::fromPyClassEnum) ?: TEXT

        fun fromPyClassEnum(py: PyClassEnum): FormatType =
            entries.firstOrNull { it.mapping.pyclass == py } ?: TEXT
    }
}
