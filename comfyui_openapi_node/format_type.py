"""The five-way bridge: one `FormatType` tying together

    JsonType        (the JSON Schema primitive)
    JsonFormat      (the `format` keyword)
    SqlTypes        (JDBC enum — see sql_types.py)
    KClass (Kotlin) (as a FQN string on this side; real KClass<*> on Kt)
    ComposeWidget   (Compose Multiplatform widget)
    HtmlInputType   (HTML <input type=…> / <select> / <textarea>)
    ComfyType       (ComfyUI INPUT_TYPES primitive **and** every
                     domain type — IMAGE, LATENT, MASK, MODEL, CLIP,
                     VAE, CONDITIONING, CONTROL_NET, STYLE_MODEL,
                     CLIP_VISION, CLIP_VISION_OUTPUT, UPSCALE_MODEL,
                     AUDIO, VIDEO, WEBCAM)

`ComfyOption` is the separate flag set that goes inside the widget
options dict — `forceInput`, `lazy`, `dynamicPrompts`, `defaultInput`,
`multiline`, `image_upload`, etc. — surfacing every dynamic-UI knob
ComfyUI's frontend recognises.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, Flag, auto

from .sql_types import SqlTypes


# ---- canonical vocabulary enums ----------------------------------------
class JsonType(str, Enum):
    STRING   = "string"
    INTEGER  = "integer"
    NUMBER   = "number"
    BOOLEAN  = "boolean"
    OBJECT   = "object"
    ARRAY    = "array"
    NULL     = "null"


class JsonFormat(str, Enum):
    NONE         = ""
    TEXTAREA     = "textarea"
    PASSWORD     = "password"
    EMAIL        = "email"
    TEL          = "tel"
    URI          = "uri"
    UUID         = "uuid"
    COLOR        = "color"
    DATE         = "date"
    TIME         = "time"
    DATE_TIME    = "date-time"
    MONTH        = "month"
    WEEK         = "week"
    YEAR         = "year"
    QUARTER      = "quarter"
    MONTH_OF_YEAR= "month-of-year"  # 1..12
    DAY          = "day"          # day-of-month (1..31)
    DAY_OF_WEEK  = "day-of-week"  # 1..7 (ISO Mon=1)
    DAY_OF_YEAR  = "day-of-year"  # 1..366
    ISO_WEEK_NUM = "iso-week-num" # 1..53
    HOUR         = "hour"         # 0..23
    MINUTE       = "minute"       # 0..59
    SECOND       = "second"       # 0..59
    MILLISECOND  = "millisecond"  # 0..999
    TIMEZONE     = "timezone"     # IANA tz name, e.g. "Europe/London"
    OFFSET       = "offset"       # ±HH:MM or Z
    DURATION     = "duration"
    IPV4         = "ipv4"
    IPV6         = "ipv6"
    HOSTNAME     = "hostname"
    REGEX        = "regex"
    JSON_POINTER = "json-pointer"
    BYTE         = "byte"
    BINARY       = "binary"
    GEOJSON      = "geojson"
    JSON         = "json"
    INT32        = "int32"
    INT64        = "int64"
    FLOAT        = "float"
    DOUBLE       = "double"
    ENUM         = "enum"
    SEARCH       = "search"
    HIDDEN       = "hidden"
    MARKDOWN     = "markdown"
    # ComfyUI-specific media formats
    IMAGE        = "image"
    LATENT       = "latent"
    MASK         = "mask"
    AUDIO        = "audio"
    VIDEO        = "video"
    MODEL_REF    = "model-ref"
    CONDITIONING = "conditioning"
    # vCard 4.0 (RFC 6350)
    VCARD_FN        = "vcard.fn"
    VCARD_N         = "vcard.n"
    VCARD_NICKNAME  = "vcard.nickname"
    VCARD_BDAY      = "vcard.bday"
    VCARD_ANNIVERSARY = "vcard.anniversary"
    VCARD_GENDER    = "vcard.gender"
    VCARD_ADR       = "vcard.adr"
    VCARD_TEL       = "vcard.tel"
    VCARD_EMAIL     = "vcard.email"
    VCARD_GEO       = "vcard.geo"
    VCARD_TZ        = "vcard.tz"
    VCARD_TITLE     = "vcard.title"
    VCARD_ROLE      = "vcard.role"
    VCARD_ORG       = "vcard.org"
    VCARD_NOTE      = "vcard.note"
    VCARD_URL       = "vcard.url"
    VCARD_UID       = "vcard.uid"
    VCARD_REV       = "vcard.rev"
    VCARD_CATEGORIES= "vcard.categories"
    # iCalendar (RFC 5545)
    ICAL_DTSTART    = "ical.dtstart"
    ICAL_DTEND      = "ical.dtend"
    ICAL_DTSTAMP    = "ical.dtstamp"
    ICAL_DUE        = "ical.due"
    ICAL_COMPLETED  = "ical.completed"
    ICAL_DURATION   = "ical.duration"
    ICAL_LOCATION   = "ical.location"
    ICAL_DESCRIPTION= "ical.description"
    ICAL_SUMMARY    = "ical.summary"
    ICAL_COMMENT    = "ical.comment"
    ICAL_STATUS     = "ical.status"
    ICAL_CLASS      = "ical.class"
    ICAL_TRANSP     = "ical.transp"
    ICAL_PRIORITY   = "ical.priority"
    ICAL_SEQUENCE   = "ical.sequence"
    ICAL_GEO        = "ical.geo"
    ICAL_RRULE      = "ical.rrule"
    ICAL_RDATE      = "ical.rdate"
    ICAL_EXDATE     = "ical.exdate"
    ICAL_ATTENDEE   = "ical.attendee"
    ICAL_ORGANIZER  = "ical.organizer"
    ICAL_CATEGORIES = "ical.categories"
    ICAL_UID        = "ical.uid"
    ICAL_TZID       = "ical.tzid"
    ICAL_METHOD     = "ical.method"
    ICAL_CALSCALE   = "ical.calscale"
    ICAL_RELATED_TO = "ical.related-to"
    ICAL_RECUR_ID   = "ical.recurrence-id"
    # Delimited cell formats (POI XLSX / TSV / CSV complex columns).
    # `;` is the same array delimiter vCard N / ADR use.
    SEMI_DELIMITED  = "semi-delimited"
    CSV             = "csv"
    TSV             = "tsv"
    # ICU / Unicode locale + calendar integration
    LOCALE          = "locale"          # BCP 47 language tag
    CALENDAR_SYSTEM = "calendar-system" # ICU calendar identifier


class HtmlInputType(str, Enum):
    TEXT           = "text"
    EMAIL          = "email"
    URL            = "url"
    TEL            = "tel"
    NUMBER         = "number"
    DATE           = "date"
    TIME           = "time"
    DATETIME_LOCAL = "datetime-local"
    MONTH          = "month"
    WEEK           = "week"
    COLOR          = "color"
    CHECKBOX       = "checkbox"
    RADIO          = "radio"
    FILE           = "file"
    PASSWORD       = "password"
    RANGE          = "range"
    SEARCH         = "search"
    HIDDEN         = "hidden"
    TEXTAREA       = "textarea"
    SELECT         = "select"
    SELECT_MULTI   = "select[multiple]"


class ComfyType(str, Enum):
    # primitives
    STRING            = "STRING"
    INT               = "INT"
    FLOAT             = "FLOAT"
    BOOLEAN           = "BOOLEAN"
    COMBO             = "COMBO"
    # ComfyUI domain types (carried by every modern node graph)
    IMAGE             = "IMAGE"
    LATENT            = "LATENT"
    MASK              = "MASK"
    MODEL             = "MODEL"
    CLIP              = "CLIP"
    VAE               = "VAE"
    CONDITIONING      = "CONDITIONING"
    CONTROL_NET       = "CONTROL_NET"
    STYLE_MODEL       = "STYLE_MODEL"
    CLIP_VISION       = "CLIP_VISION"
    CLIP_VISION_OUTPUT= "CLIP_VISION_OUTPUT"
    UPSCALE_MODEL     = "UPSCALE_MODEL"
    AUDIO             = "AUDIO"
    VIDEO             = "VIDEO"
    WEBCAM            = "WEBCAM"


class ComposeWidget(str, Enum):
    TEXT_FIELD            = "TextField"
    OUTLINED_TEXT_FIELD   = "OutlinedTextField"
    PASSWORD_FIELD        = "TextField(visualTransformation=PasswordVisualTransformation())"
    SEARCH_FIELD          = "SearchBar"
    DYNAMIC_PROMPT_FIELD  = "DynamicPromptField"
    MARKDOWN_VIEW         = "MarkdownView"
    COLOR_PICKER          = "ColorPicker"
    DATE_PICKER           = "DatePicker"
    TIME_PICKER           = "TimePicker"
    DATETIME_PICKER       = "DateTimePicker"
    MONTH_PICKER          = "MonthPicker"
    WEEK_PICKER           = "WeekPicker"
    FILE_PICKER           = "FilePicker"
    MAP_PICKER            = "MapPicker"
    IMAGE_UPLOAD          = "ImageUpload"
    MASK_EDITOR           = "MaskEditor"
    WEBCAM_CAPTURE        = "WebcamCapture"
    AUDIO_PLAYER          = "AudioPlayer"
    VIDEO_PLAYER          = "VideoPlayer"
    MODEL_PICKER          = "ModelPicker"
    LATENT_PREVIEW        = "LatentPreview"
    CONDITIONING_VIEW     = "ConditioningView"
    SLIDER                = "Slider"
    RANGE_SLIDER          = "RangeSlider"
    KNOB                  = "Knob"
    NUMBER_FIELD          = "NumberField"
    SWITCH                = "Switch"
    CHECKBOX              = "Checkbox"
    CHECKBOX_GROUP        = "CheckboxGroup"
    RADIO_GROUP           = "RadioGroup"
    DROPDOWN_MENU         = "DropdownMenu"
    HIDDEN_FIELD          = "HiddenField"


class ComfyOption(Flag):
    """Boolean knobs that ride along on the `INPUT_TYPES` options
    dict. ComfyUI's frontend reads them to switch the widget's
    rendering / behaviour.

    `forceInput`        — render as an input socket, not a widget
    `defaultInput`      — start as input socket, allow widget toggle
    `lazy`              — defer execution until the node actually fires
    `dynamicPrompts`    — interpret the value with the dynamic-prompts
                          DSL ([alt|alt2], wildcards, …)
    `multiline`         — STRING widget grows; renders <textarea>
    `image_upload`      — COMBO of files plus a drag-and-drop area
    `image_folder`      — COMBO sources files from a folder
    `directory`         — file picker becomes a directory picker
    `tooltip_md`        — interpret tooltip text as Markdown
    """
    NONE              = 0
    FORCE_INPUT       = auto()
    DEFAULT_INPUT     = auto()
    LAZY              = auto()
    DYNAMIC_PROMPTS   = auto()
    MULTILINE         = auto()
    IMAGE_UPLOAD      = auto()
    IMAGE_FOLDER      = auto()
    DIRECTORY         = auto()
    TOOLTIP_MARKDOWN  = auto()


class ComfyDisplay(str, Enum):
    """Value of the `display` widget option. INT / FLOAT widgets
    pick the rendering mode; STRING / BOOLEAN ignore it."""
    NUMBER  = "number"
    SLIDER  = "slider"
    KNOB    = "knob"
    COLOR   = "color"


# ---- RFC vocabulary enums (full coverage) ------------------------------
class IcalComponent(str, Enum):
    """iCalendar (RFC 5545) components — `BEGIN:<name>` / `END:<name>`."""
    VCALENDAR = "VCALENDAR"
    VEVENT    = "VEVENT"
    VTODO     = "VTODO"
    VJOURNAL  = "VJOURNAL"
    VFREEBUSY = "VFREEBUSY"
    VTIMEZONE = "VTIMEZONE"
    VALARM    = "VALARM"
    STANDARD  = "STANDARD"    # VTIMEZONE sub-component
    DAYLIGHT  = "DAYLIGHT"    # VTIMEZONE sub-component


class IcalStatus(str, Enum):
    """Values of the iCal STATUS property. Context-dependent:
    VEVENT → TENTATIVE/CONFIRMED/CANCELLED;
    VTODO  → NEEDS-ACTION/IN-PROCESS/COMPLETED/CANCELLED;
    VJOURNAL → DRAFT/FINAL/CANCELLED."""
    TENTATIVE    = "TENTATIVE"
    CONFIRMED    = "CONFIRMED"
    CANCELLED    = "CANCELLED"
    NEEDS_ACTION = "NEEDS-ACTION"
    IN_PROCESS   = "IN-PROCESS"
    COMPLETED    = "COMPLETED"
    DRAFT        = "DRAFT"
    FINAL        = "FINAL"


class IcalMethod(str, Enum):
    PUBLISH         = "PUBLISH"
    REQUEST         = "REQUEST"
    REPLY           = "REPLY"
    ADD             = "ADD"
    CANCEL          = "CANCEL"
    REFRESH         = "REFRESH"
    COUNTER         = "COUNTER"
    DECLINE_COUNTER = "DECLINECOUNTER"


class IcalClass(str, Enum):
    PUBLIC       = "PUBLIC"
    PRIVATE      = "PRIVATE"
    CONFIDENTIAL = "CONFIDENTIAL"


class IcalTransp(str, Enum):
    OPAQUE      = "OPAQUE"
    TRANSPARENT = "TRANSPARENT"


class IcalAction(str, Enum):
    """VALARM ACTION property."""
    AUDIO   = "AUDIO"
    DISPLAY = "DISPLAY"
    EMAIL   = "EMAIL"


class VCardEmailType(str, Enum):
    """vCard 4.0 EMAIL `TYPE=` parameter values."""
    WORK     = "work"
    HOME     = "home"
    INTERNET = "internet"     # retained from 3.0
    PREF     = "pref"
    OTHER    = "other"


class VCardTelType(str, Enum):
    """vCard 4.0 TEL `TYPE=` parameter values."""
    VOICE     = "voice"
    FAX       = "fax"
    CELL      = "cell"
    HOME      = "home"
    WORK      = "work"
    TEXT      = "text"
    VIDEO     = "video"
    PAGER     = "pager"
    TEXTPHONE = "textphone"
    CAR       = "car"
    ISDN      = "isdn"
    PCS       = "pcs"


class VCardGender(str, Enum):
    """vCard 4.0 GENDER property first component."""
    MALE      = "M"
    FEMALE    = "F"
    OTHER     = "O"
    NONE_     = "N"
    UNKNOWN   = "U"


class CalendarSystem(str, Enum):
    """ICU / CLDR calendar identifiers (RFC 6350 / LDML)."""
    GREGORIAN            = "gregorian"
    BUDDHIST             = "buddhist"
    CHINESE              = "chinese"
    COPTIC               = "coptic"
    ETHIOPIC             = "ethiopic"
    ETHIOPIC_AMETE_ALEM  = "ethiopic-amete-alem"
    HEBREW               = "hebrew"
    INDIAN               = "indian"
    ISLAMIC              = "islamic"
    ISLAMIC_CIVIL        = "islamic-civil"
    ISLAMIC_TBLA         = "islamic-tbla"
    ISLAMIC_UMALQURA     = "islamic-umalqura"
    ISLAMIC_RGSA         = "islamic-rgsa"
    ISO8601              = "iso8601"
    JAPANESE             = "japanese"
    PERSIAN              = "persian"
    ROC                  = "roc"
    DANGI                = "dangi"


class IcalWeekDay(str, Enum):
    """RRULE BYDAY values (RFC 5545 §3.3.10)."""
    SU = "SU"
    MO = "MO"
    TU = "TU"
    WE = "WE"
    TH = "TH"
    FR = "FR"
    SA = "SA"


class IcalFreq(str, Enum):
    """RRULE FREQ values."""
    SECONDLY = "SECONDLY"
    MINUTELY = "MINUTELY"
    HOURLY   = "HOURLY"
    DAILY    = "DAILY"
    WEEKLY   = "WEEKLY"
    MONTHLY  = "MONTHLY"
    YEARLY   = "YEARLY"


# ---- mapping + enum ----------------------------------------------------
@dataclass(frozen=True)
class FormatPattern:
    """Named-group regex + matching template + per-group FormatType.

    Lets a complex format (ISO date-time, ISO week, ISO duration, …)
    decompose into its atomic parts. The regex is a Python `re`
    pattern using `(?P<name>…)` groups; the template uses Python
    `str.format` `{name}` placeholders. Each name maps to the atomic
    `FormatType` representing that part — picked up by UIs to render
    sub-widgets, by validators to range-check each field, by the
    Kotlin/JS sides via the same shared regex string.
    """
    regex:    str
    template: str
    parts:    dict[str, str] = field(default_factory=dict)
    # `parts` keys are the named groups; values are FormatType.name
    # strings (avoids forward-reference at decoration time).


@dataclass(frozen=True)
class FormatMapping:
    json_type:   JsonType
    json_format: JsonFormat
    sql_type:    SqlTypes
    kclass:      str
    composable:  ComposeWidget
    html_input:  HtmlInputType
    comfy:       ComfyType
    placeholder: str = ""
    pattern:     FormatPattern | None = None


T  = JsonType
F  = JsonFormat
S  = SqlTypes
C  = ComposeWidget
H  = HtmlInputType
Y  = ComfyType


class FormatType(Enum):
    # String & its formats
    TEXT          = FormatMapping(T.STRING,  F.NONE,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    TEXTAREA      = FormatMapping(T.STRING,  F.TEXTAREA,     S.LONGVARCHAR, "kotlin.String",                         C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    DYNAMIC_PROMPT= FormatMapping(T.STRING,  F.TEXTAREA,     S.LONGVARCHAR, "kotlin.String",                         C.DYNAMIC_PROMPT_FIELD,H.TEXTAREA,       Y.STRING)
    MARKDOWN      = FormatMapping(T.STRING,  F.MARKDOWN,     S.LONGVARCHAR, "kotlin.String",                         C.MARKDOWN_VIEW,       H.TEXTAREA,       Y.STRING)
    PASSWORD      = FormatMapping(T.STRING,  F.PASSWORD,     S.VARCHAR,     "kotlin.String",                         C.PASSWORD_FIELD,      H.PASSWORD,       Y.STRING)
    EMAIL         = FormatMapping(T.STRING,  F.EMAIL,        S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.EMAIL,          Y.STRING, "user@example.com")
    TEL           = FormatMapping(T.STRING,  F.TEL,          S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEL,            Y.STRING, "+1 555 0100")
    URL           = FormatMapping(T.STRING,  F.URI,          S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.URL,            Y.STRING, "https://…")
    SEARCH        = FormatMapping(T.STRING,  F.SEARCH,       S.VARCHAR,     "kotlin.String",                         C.SEARCH_FIELD,        H.SEARCH,         Y.STRING, "Search…")
    UUID          = FormatMapping(T.STRING,  F.UUID,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "00000000-0000-0000-0000-000000000000")
    COLOR         = FormatMapping(T.STRING,  F.COLOR,        S.VARCHAR,     "kotlin.String",                         C.COLOR_PICKER,        H.COLOR,          Y.STRING, "#RRGGBB")
    DATE          = FormatMapping(T.STRING,  F.DATE,         S.DATE,        "kotlinx.datetime.LocalDate",            C.DATE_PICKER,         H.DATE,           Y.STRING, "YYYY-MM-DD")
    TIME          = FormatMapping(T.STRING,  F.TIME,         S.TIME,        "kotlinx.datetime.LocalTime",            C.TIME_PICKER,         H.TIME,           Y.STRING, "HH:MM:SS")
    DATETIME      = FormatMapping(T.STRING,  F.DATE_TIME,    S.TIMESTAMP,   "kotlinx.datetime.Instant",              C.DATETIME_PICKER,     H.DATETIME_LOCAL, Y.STRING, "YYYY-MM-DDTHH:MM:SSZ")
    MONTH         = FormatMapping(T.STRING,  F.MONTH,        S.VARCHAR,     "kotlin.String",                         C.MONTH_PICKER,        H.MONTH,          Y.STRING, "YYYY-MM")
    WEEK          = FormatMapping(T.STRING,  F.WEEK,         S.VARCHAR,     "kotlin.String",                         C.WEEK_PICKER,         H.WEEK,           Y.STRING, "YYYY-Www")
    TIMEZONE      = FormatMapping(T.STRING,  F.TIMEZONE,     S.VARCHAR,     "kotlinx.datetime.TimeZone",             C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "Europe/London")
    DURATION      = FormatMapping(T.STRING,  F.DURATION,     S.VARCHAR,     "kotlin.time.Duration",                  C.TEXT_FIELD,          H.TEXT,           Y.STRING, "P1DT2H")
    IPV4          = FormatMapping(T.STRING,  F.IPV4,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "0.0.0.0")
    IPV6          = FormatMapping(T.STRING,  F.IPV6,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "::1")
    HOSTNAME      = FormatMapping(T.STRING,  F.HOSTNAME,     S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "example.com")
    REGEX         = FormatMapping(T.STRING,  F.REGEX,        S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "^.*$")
    JSON_POINTER  = FormatMapping(T.STRING,  F.JSON_POINTER, S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "/foo/bar")
    BYTE          = FormatMapping(T.STRING,  F.BYTE,         S.VARBINARY,   "kotlin.ByteArray",                      C.FILE_PICKER,         H.FILE,           Y.STRING)
    BINARY        = FormatMapping(T.STRING,  F.BINARY,       S.BLOB,        "kotlin.ByteArray",                      C.FILE_PICKER,         H.FILE,           Y.STRING)
    HIDDEN        = FormatMapping(T.STRING,  F.HIDDEN,       S.VARCHAR,     "kotlin.String",                         C.HIDDEN_FIELD,        H.HIDDEN,         Y.STRING)
    # Object / array formats
    GEOJSON       = FormatMapping(T.OBJECT,  F.GEOJSON,      S.OTHER,       "kotlinx.serialization.json.JsonObject", C.MAP_PICKER,          H.TEXTAREA,       Y.STRING, '{"type":"Point","coordinates":[0,0]}')
    JSON_OBJECT   = FormatMapping(T.OBJECT,  F.JSON,         S.OTHER,       "kotlinx.serialization.json.JsonObject", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    JSON_ARRAY    = FormatMapping(T.ARRAY,   F.JSON,         S.ARRAY,       "kotlinx.serialization.json.JsonArray",  C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    # Numeric formats
    INT32         = FormatMapping(T.INTEGER, F.INT32,        S.INTEGER,     "kotlin.Int",                            C.SLIDER,              H.NUMBER,         Y.INT)
    INT64         = FormatMapping(T.INTEGER, F.INT64,        S.BIGINT,      "kotlin.Long",                           C.SLIDER,              H.NUMBER,         Y.INT)
    FLOAT         = FormatMapping(T.NUMBER,  F.FLOAT,        S.REAL,        "kotlin.Float",                          C.SLIDER,              H.NUMBER,         Y.FLOAT)
    DOUBLE        = FormatMapping(T.NUMBER,  F.DOUBLE,       S.DOUBLE,      "kotlin.Double",                         C.SLIDER,              H.NUMBER,         Y.FLOAT)
    RANGE         = FormatMapping(T.NUMBER,  F.NONE,         S.REAL,        "kotlin.Float",                          C.RANGE_SLIDER,        H.RANGE,          Y.FLOAT)
    KNOB          = FormatMapping(T.NUMBER,  F.NONE,         S.REAL,        "kotlin.Float",                          C.KNOB,                H.RANGE,          Y.FLOAT)
    NUMBER_FIELD  = FormatMapping(T.NUMBER,  F.NONE,         S.REAL,        "kotlin.Float",                          C.NUMBER_FIELD,        H.NUMBER,         Y.FLOAT)
    # Date/time *parts* — rendered as `<input type="number">` with
    # min/max bounds the operation's JSON Schema supplies. Defined
    # AFTER INT32/INT64/FLOAT/DOUBLE so the SQL→FormatType dispatch
    # picks the generic numeric form first for a bare INTEGER /
    # SMALLINT column.
    YEAR          = FormatMapping(T.INTEGER, F.YEAR,         S.INTEGER,     "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "YYYY")
    QUARTER       = FormatMapping(T.INTEGER, F.QUARTER,      S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..4")
    MONTH_OF_YEAR = FormatMapping(T.INTEGER, F.MONTH_OF_YEAR,S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..12")
    DAY           = FormatMapping(T.INTEGER, F.DAY,          S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..31")
    DAY_OF_WEEK   = FormatMapping(T.INTEGER, F.DAY_OF_WEEK,  S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..7")
    DAY_OF_YEAR   = FormatMapping(T.INTEGER, F.DAY_OF_YEAR,  S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..366")
    ISO_WEEK_NUM  = FormatMapping(T.INTEGER, F.ISO_WEEK_NUM, S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..53")
    HOUR          = FormatMapping(T.INTEGER, F.HOUR,         S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..23")
    MINUTE        = FormatMapping(T.INTEGER, F.MINUTE,       S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..59")
    SECOND        = FormatMapping(T.INTEGER, F.SECOND,       S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..59")
    MILLISECOND   = FormatMapping(T.INTEGER, F.MILLISECOND,  S.INTEGER,     "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..999")
    OFFSET        = FormatMapping(T.STRING,  F.OFFSET,       S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "+00:00")
    # Boolean rendering variants
    BOOL          = FormatMapping(T.BOOLEAN, F.NONE,         S.BOOLEAN,     "kotlin.Boolean",                        C.SWITCH,              H.CHECKBOX,       Y.BOOLEAN)
    CHECKBOX      = FormatMapping(T.BOOLEAN, F.NONE,         S.BOOLEAN,     "kotlin.Boolean",                        C.CHECKBOX,            H.CHECKBOX,       Y.BOOLEAN)
    # Enum presentation variants
    ENUM          = FormatMapping(T.STRING,  F.ENUM,         S.VARCHAR,     "kotlin.String",                         C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO)
    RADIO         = FormatMapping(T.STRING,  F.ENUM,         S.VARCHAR,     "kotlin.String",                         C.RADIO_GROUP,         H.RADIO,          Y.COMBO)
    MULTI_SELECT  = FormatMapping(T.ARRAY,   F.ENUM,         S.ARRAY,       "kotlin.collections.List",               C.CHECKBOX_GROUP,      H.SELECT_MULTI,   Y.COMBO)
    # ComfyUI domain types — most arrive over the wire as a reference
    # name (model id, file path) so VARCHAR storage; the in-memory
    # ComfyUI tensor types are runtime-only.
    IMAGE              = FormatMapping(T.STRING, F.IMAGE,        S.VARCHAR,   "kotlin.String", C.IMAGE_UPLOAD,      H.FILE,   Y.IMAGE)
    LATENT             = FormatMapping(T.OBJECT, F.LATENT,       S.OTHER,     "kotlinx.serialization.json.JsonObject", C.LATENT_PREVIEW,    H.HIDDEN, Y.LATENT)
    MASK               = FormatMapping(T.STRING, F.MASK,         S.VARCHAR,   "kotlin.String", C.MASK_EDITOR,       H.FILE,   Y.MASK)
    MODEL              = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.MODEL,             "model.safetensors")
    CLIP               = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.CLIP)
    VAE                = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.VAE)
    CONDITIONING       = FormatMapping(T.OBJECT, F.CONDITIONING, S.OTHER,     "kotlinx.serialization.json.JsonObject", C.CONDITIONING_VIEW, H.HIDDEN, Y.CONDITIONING)
    CONTROL_NET        = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.CONTROL_NET)
    STYLE_MODEL        = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.STYLE_MODEL)
    CLIP_VISION        = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.CLIP_VISION)
    CLIP_VISION_OUTPUT = FormatMapping(T.OBJECT, F.JSON,         S.OTHER,     "kotlinx.serialization.json.JsonObject", C.OUTLINED_TEXT_FIELD, H.HIDDEN, Y.CLIP_VISION_OUTPUT)
    UPSCALE_MODEL      = FormatMapping(T.STRING, F.MODEL_REF,    S.VARCHAR,   "kotlin.String", C.MODEL_PICKER,      H.SELECT, Y.UPSCALE_MODEL)
    AUDIO              = FormatMapping(T.STRING, F.AUDIO,        S.VARCHAR,   "kotlin.String", C.AUDIO_PLAYER,      H.FILE,   Y.AUDIO)
    VIDEO              = FormatMapping(T.STRING, F.VIDEO,        S.VARCHAR,   "kotlin.String", C.VIDEO_PLAYER,      H.FILE,   Y.VIDEO)
    WEBCAM             = FormatMapping(T.STRING, F.IMAGE,        S.VARCHAR,   "kotlin.String", C.WEBCAM_CAPTURE,    H.HIDDEN, Y.WEBCAM)

    # vCard 4.0 (RFC 6350) — text-typed properties extending string.
    VCARD_FN           = FormatMapping(T.STRING, F.VCARD_FN,        S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "Ada Lovelace")
    VCARD_N            = FormatMapping(T.STRING, F.VCARD_N,         S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "Lovelace;Ada;Augusta;Hon.;")
    VCARD_NICKNAME     = FormatMapping(T.STRING, F.VCARD_NICKNAME,  S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    VCARD_BDAY         = FormatMapping(T.STRING, F.VCARD_BDAY,      S.DATE,        "kotlinx.datetime.LocalDate", C.DATE_PICKER, H.DATE,        Y.STRING, "YYYY-MM-DD")
    VCARD_ANNIVERSARY  = FormatMapping(T.STRING, F.VCARD_ANNIVERSARY,S.DATE,       "kotlinx.datetime.LocalDate", C.DATE_PICKER, H.DATE,        Y.STRING, "YYYY-MM-DD")
    VCARD_GENDER       = FormatMapping(T.STRING, F.VCARD_GENDER,    S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "M / F / O / N / U")
    VCARD_ADR          = FormatMapping(T.STRING, F.VCARD_ADR,       S.VARCHAR,     "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING, ";;Street;City;Region;ZIP;Country")
    VCARD_TEL          = FormatMapping(T.STRING, F.VCARD_TEL,       S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEL,            Y.STRING, "+1 555 0100")
    VCARD_EMAIL        = FormatMapping(T.STRING, F.VCARD_EMAIL,     S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.EMAIL,          Y.STRING, "user@example.com")
    VCARD_GEO          = FormatMapping(T.STRING, F.VCARD_GEO,       S.VARCHAR,     "kotlin.String", C.MAP_PICKER,          H.TEXT,           Y.STRING, "geo:51.5074,-0.1278")
    VCARD_TZ           = FormatMapping(T.STRING, F.VCARD_TZ,        S.VARCHAR,     "kotlinx.datetime.TimeZone", C.DROPDOWN_MENU, H.SELECT,    Y.COMBO,  "Europe/London")
    VCARD_TITLE        = FormatMapping(T.STRING, F.VCARD_TITLE,     S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    VCARD_ROLE         = FormatMapping(T.STRING, F.VCARD_ROLE,      S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    VCARD_ORG          = FormatMapping(T.STRING, F.VCARD_ORG,       S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    VCARD_NOTE         = FormatMapping(T.STRING, F.VCARD_NOTE,      S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    VCARD_URL          = FormatMapping(T.STRING, F.VCARD_URL,       S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.URL,            Y.STRING, "https://…")
    VCARD_UID          = FormatMapping(T.STRING, F.VCARD_UID,       S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "urn:uuid:…")
    VCARD_REV          = FormatMapping(T.STRING, F.VCARD_REV,       S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)
    VCARD_CATEGORIES   = FormatMapping(T.STRING, F.VCARD_CATEGORIES,S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "tag1,tag2,tag3")

    # iCalendar (RFC 5545)
    ICAL_DTSTART       = FormatMapping(T.STRING, F.ICAL_DTSTART,    S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING, "YYYYMMDDTHHMMSSZ")
    ICAL_DTEND         = FormatMapping(T.STRING, F.ICAL_DTEND,      S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)
    ICAL_DTSTAMP       = FormatMapping(T.STRING, F.ICAL_DTSTAMP,    S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)
    ICAL_DUE           = FormatMapping(T.STRING, F.ICAL_DUE,        S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)
    ICAL_COMPLETED     = FormatMapping(T.STRING, F.ICAL_COMPLETED,  S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)
    ICAL_DURATION      = FormatMapping(T.STRING, F.ICAL_DURATION,   S.VARCHAR,     "kotlin.time.Duration",     C.TEXT_FIELD,      H.TEXT,           Y.STRING, "P1DT2H")
    ICAL_LOCATION      = FormatMapping(T.STRING, F.ICAL_LOCATION,   S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "1 Infinite Loop")
    ICAL_DESCRIPTION   = FormatMapping(T.STRING, F.ICAL_DESCRIPTION,S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    ICAL_SUMMARY       = FormatMapping(T.STRING, F.ICAL_SUMMARY,    S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    ICAL_COMMENT       = FormatMapping(T.STRING, F.ICAL_COMMENT,    S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    ICAL_STATUS        = FormatMapping(T.STRING, F.ICAL_STATUS,     S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "TENTATIVE / CONFIRMED / CANCELLED / NEEDS-ACTION / COMPLETED / IN-PROCESS / DRAFT / FINAL")
    ICAL_CLASS         = FormatMapping(T.STRING, F.ICAL_CLASS,      S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "PUBLIC / PRIVATE / CONFIDENTIAL")
    ICAL_TRANSP        = FormatMapping(T.STRING, F.ICAL_TRANSP,     S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "OPAQUE / TRANSPARENT")
    ICAL_PRIORITY      = FormatMapping(T.INTEGER,F.ICAL_PRIORITY,   S.SMALLINT,    "kotlin.Int",    C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..9")
    ICAL_SEQUENCE      = FormatMapping(T.INTEGER,F.ICAL_SEQUENCE,   S.INTEGER,     "kotlin.Int",    C.NUMBER_FIELD,        H.NUMBER,         Y.INT)
    ICAL_GEO           = FormatMapping(T.STRING, F.ICAL_GEO,        S.VARCHAR,     "kotlin.String", C.MAP_PICKER,          H.TEXT,           Y.STRING, "51.5074;-0.1278")
    ICAL_RRULE         = FormatMapping(T.STRING, F.ICAL_RRULE,      S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING, "FREQ=WEEKLY;BYDAY=MO,WE,FR")
    ICAL_RDATE         = FormatMapping(T.STRING, F.ICAL_RDATE,      S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    ICAL_EXDATE        = FormatMapping(T.STRING, F.ICAL_EXDATE,     S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING)
    ICAL_ATTENDEE      = FormatMapping(T.STRING, F.ICAL_ATTENDEE,   S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.EMAIL,          Y.STRING, "mailto:user@example.com")
    ICAL_ORGANIZER     = FormatMapping(T.STRING, F.ICAL_ORGANIZER,  S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.EMAIL,          Y.STRING, "mailto:org@example.com")
    ICAL_CATEGORIES    = FormatMapping(T.STRING, F.ICAL_CATEGORIES, S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "tag1,tag2")
    ICAL_UID           = FormatMapping(T.STRING, F.ICAL_UID,        S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "uid@example.com")
    ICAL_TZID          = FormatMapping(T.STRING, F.ICAL_TZID,       S.VARCHAR,     "kotlinx.datetime.TimeZone", C.DROPDOWN_MENU, H.SELECT,    Y.COMBO,  "Europe/London")
    ICAL_METHOD        = FormatMapping(T.STRING, F.ICAL_METHOD,     S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "PUBLISH / REQUEST / REPLY / ADD / CANCEL / REFRESH / COUNTER / DECLINECOUNTER")
    ICAL_CALSCALE      = FormatMapping(T.STRING, F.ICAL_CALSCALE,   S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "GREGORIAN")
    ICAL_RELATED_TO    = FormatMapping(T.STRING, F.ICAL_RELATED_TO, S.VARCHAR,     "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    ICAL_RECUR_ID      = FormatMapping(T.STRING, F.ICAL_RECUR_ID,   S.TIMESTAMP,   "kotlinx.datetime.Instant", C.DATETIME_PICKER, H.DATETIME_LOCAL, Y.STRING)

    # Delimited-row cell formats for tabular (POI XLSX / CSV / TSV /
    # vCard / iCal) use. Stored as TEXT; the array layout is a
    # FormatPattern concern (see PATTERNS below).
    SEMI_DELIMITED     = FormatMapping(T.STRING, F.SEMI_DELIMITED, S.LONGVARCHAR, "kotlin.String", C.TEXT_FIELD,          H.TEXT,           Y.STRING, "a;b;c")
    CSV_ROW            = FormatMapping(T.STRING, F.CSV,            S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING, "a,b,c")
    TSV_ROW            = FormatMapping(T.STRING, F.TSV,            S.LONGVARCHAR, "kotlin.String", C.OUTLINED_TEXT_FIELD, H.TEXTAREA,       Y.STRING, "a\\tb\\tc")
    # ICU / Unicode locale + calendar system integration
    LOCALE             = FormatMapping(T.STRING, F.LOCALE,         S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "en-US")
    CALENDAR_SYSTEM    = FormatMapping(T.STRING, F.CALENDAR_SYSTEM,S.VARCHAR,     "kotlin.String", C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO,  "gregorian")


# ---- dispatch helpers --------------------------------------------------
def _from_json_schema(schema: dict) -> "FormatType":
    if not isinstance(schema, dict):
        return FormatType.TEXT
    if "enum" in schema:
        return FormatType.ENUM
    try:
        t = JsonType(schema.get("type") or "string")
    except ValueError:
        t = JsonType.STRING
    raw_f = schema.get("format") or ""
    try:
        f = JsonFormat(raw_f) if raw_f else JsonFormat.NONE
    except ValueError:
        f = JsonFormat.NONE
    if t is JsonType.BOOLEAN:
        return FormatType.BOOL
    if t is JsonType.INTEGER:
        return FormatType.INT64 if f is JsonFormat.INT64 else FormatType.INT32
    if t is JsonType.NUMBER:
        return FormatType.DOUBLE if f is JsonFormat.DOUBLE else FormatType.FLOAT
    if t is JsonType.ARRAY:
        return FormatType.JSON_ARRAY
    if t is JsonType.OBJECT:
        return FormatType.GEOJSON if f is JsonFormat.GEOJSON else FormatType.JSON_OBJECT
    for ft in FormatType:
        m = ft.value
        if m.json_type is JsonType.STRING and m.json_format is f:
            return ft
    return FormatType.TEXT


def _from_sql(sql_type) -> "FormatType":
    if isinstance(sql_type, SqlTypes):
        resolved = sql_type
    elif isinstance(sql_type, int):
        try:
            resolved = SqlTypes(sql_type)
        except ValueError:
            return FormatType.TEXT
    else:
        try:
            resolved = SqlTypes.from_name(str(sql_type or ""))
        except KeyError:
            return FormatType.TEXT
    for ft in FormatType:
        if ft.value.sql_type is resolved:
            return ft
    return FormatType.TEXT


FormatType.from_json_schema = staticmethod(_from_json_schema)   # type: ignore[attr-defined]
FormatType.from_sql         = staticmethod(_from_sql)           # type: ignore[attr-defined]


# ---- Canonical FormatPatterns for compound formats --------------------
# Defined here (not on the enum value) so they can reference other
# FormatType members without forward-ref gymnastics. The patterns dict
# below is consulted by `FormatType.pattern()` and the parse / render
# helpers.
PATTERNS: dict["FormatType", FormatPattern] = {
    FormatType.DATE: FormatPattern(
        regex    = r"^(?P<year>\d{4})-(?P<month_of_year>\d{2})-(?P<day>\d{2})$",
        template = "{year:04d}-{month_of_year:02d}-{day:02d}",
        parts    = {"year": "YEAR", "month_of_year": "MONTH_OF_YEAR", "day": "DAY"},
    ),
    FormatType.TIME: FormatPattern(
        regex    = r"^(?P<hour>\d{2}):(?P<minute>\d{2})(?::(?P<second>\d{2})(?:\.(?P<millisecond>\d{1,3}))?)?$",
        template = "{hour:02d}:{minute:02d}:{second:02d}",
        parts    = {"hour": "HOUR", "minute": "MINUTE",
                    "second": "SECOND", "millisecond": "MILLISECOND"},
    ),
    FormatType.DATETIME: FormatPattern(
        regex    = (r"^(?P<year>\d{4})-(?P<month_of_year>\d{2})-(?P<day>\d{2})"
                    r"T(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
                    r"(?:\.(?P<millisecond>\d{1,3}))?"
                    r"(?P<offset>Z|[+-]\d{2}:?\d{2})?$"),
        template = "{year:04d}-{month_of_year:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}{offset}",
        parts    = {"year": "YEAR", "month_of_year": "MONTH_OF_YEAR", "day": "DAY",
                    "hour": "HOUR", "minute": "MINUTE", "second": "SECOND",
                    "millisecond": "MILLISECOND", "offset": "OFFSET"},
    ),
    FormatType.MONTH: FormatPattern(
        regex    = r"^(?P<year>\d{4})-(?P<month_of_year>\d{2})$",
        template = "{year:04d}-{month_of_year:02d}",
        parts    = {"year": "YEAR", "month_of_year": "MONTH_OF_YEAR"},
    ),
    FormatType.WEEK: FormatPattern(
        regex    = r"^(?P<year>\d{4})-W(?P<iso_week_num>\d{2})$",
        template = "{year:04d}-W{iso_week_num:02d}",
        parts    = {"year": "YEAR", "iso_week_num": "ISO_WEEK_NUM"},
    ),
    FormatType.DURATION: FormatPattern(
        # ISO 8601 duration — abbreviated (years / months / days / time)
        regex    = (r"^P(?:(?P<year>\d+)Y)?(?:(?P<month_of_year>\d+)M)?(?:(?P<day>\d+)D)?"
                    r"(?:T(?:(?P<hour>\d+)H)?(?:(?P<minute>\d+)M)?(?:(?P<second>\d+)S)?)?$"),
        template = "P{year}Y{month_of_year}M{day}DT{hour}H{minute}M{second}S",
        parts    = {"year": "YEAR", "month_of_year": "MONTH_OF_YEAR", "day": "DAY",
                    "hour": "HOUR", "minute": "MINUTE", "second": "SECOND"},
    ),
    FormatType.OFFSET: FormatPattern(
        regex    = r"^(?:Z|(?P<sign>[+-])(?P<hour>\d{2}):?(?P<minute>\d{2}))$",
        template = "{sign}{hour:02d}:{minute:02d}",
        parts    = {"sign": "TEXT", "hour": "HOUR", "minute": "MINUTE"},
    ),

    # --- vCard 4.0 (RFC 6350) structured properties ---------------------
    # N: family;given;additional;prefixes;suffixes
    FormatType.VCARD_N: FormatPattern(
        regex    = r"^(?P<family>[^;]*);(?P<given>[^;]*);(?P<additional>[^;]*);(?P<prefixes>[^;]*);(?P<suffixes>[^;]*)$",
        template = "{family};{given};{additional};{prefixes};{suffixes}",
        parts    = {"family": "TEXT", "given": "TEXT",
                    "additional": "TEXT", "prefixes": "TEXT",
                    "suffixes": "TEXT"},
    ),
    # ADR: po_box;extended;street;locality;region;postal_code;country
    FormatType.VCARD_ADR: FormatPattern(
        regex    = (r"^(?P<po_box>[^;]*);(?P<extended>[^;]*);(?P<street>[^;]*);"
                    r"(?P<locality>[^;]*);(?P<region>[^;]*);"
                    r"(?P<postal_code>[^;]*);(?P<country>[^;]*)$"),
        template = "{po_box};{extended};{street};{locality};{region};{postal_code};{country}",
        parts    = {"po_box": "TEXT", "extended": "TEXT", "street": "TEXT",
                    "locality": "TEXT", "region": "TEXT",
                    "postal_code": "TEXT", "country": "TEXT"},
    ),
    # GEO: geo:lat,lon (vCard URI form) — latitude,longitude
    FormatType.VCARD_GEO: FormatPattern(
        regex    = r"^(?:geo:)?(?P<latitude>-?\d+(?:\.\d+)?),(?P<longitude>-?\d+(?:\.\d+)?)$",
        template = "geo:{latitude},{longitude}",
        parts    = {"latitude": "DOUBLE", "longitude": "DOUBLE"},
    ),

    # --- iCalendar (RFC 5545) structured properties ---------------------
    # GEO: lat;lon (iCal list form — semicolon separated)
    FormatType.ICAL_GEO: FormatPattern(
        regex    = r"^(?P<latitude>-?\d+(?:\.\d+)?);(?P<longitude>-?\d+(?:\.\d+)?)$",
        template = "{latitude};{longitude}",
        parts    = {"latitude": "DOUBLE", "longitude": "DOUBLE"},
    ),
    # ATTENDEE / ORGANIZER: CAL-ADDRESS = mailto:email
    FormatType.ICAL_ATTENDEE: FormatPattern(
        regex    = r"^mailto:(?P<email>[^@\s]+@[^@\s]+\.[^@\s]+)$",
        template = "mailto:{email}",
        parts    = {"email": "EMAIL"},
    ),
    FormatType.ICAL_ORGANIZER: FormatPattern(
        regex    = r"^mailto:(?P<email>[^@\s]+@[^@\s]+\.[^@\s]+)$",
        template = "mailto:{email}",
        parts    = {"email": "EMAIL"},
    ),
    # RRULE: FREQ=WEEKLY;COUNT=10;BYDAY=MO,WE,FR — we capture the
    # most common top-level fields. Unknown keys survive untouched
    # because the regex is anchored only on the known prefixes.
    # Delimited cell formats — the "pattern" here doesn't carry named
    # groups because the arity is variable; callers split on the
    # delimiter and use `parts["item"]` as the atomic type for every
    # cell. `template` shows the rendering convention.
    FormatType.SEMI_DELIMITED: FormatPattern(
        regex    = r"^(?:[^;]*)(?:;[^;]*)*$",
        template = "{items_joined_with_semicolon}",
        parts    = {"item": "TEXT"},
    ),
    FormatType.CSV_ROW: FormatPattern(
        regex    = r"^(?:[^,\n]*)(?:,[^,\n]*)*$",
        template = "{items_joined_with_comma}",
        parts    = {"item": "TEXT"},
    ),
    FormatType.TSV_ROW: FormatPattern(
        regex    = r"^(?:[^\t\n]*)(?:\t[^\t\n]*)*$",
        template = "{items_joined_with_tab}",
        parts    = {"item": "TEXT"},
    ),
    FormatType.ICAL_RRULE: FormatPattern(
        # FREQ is always first; every other field is optional and we
        # use a single permissive alternation so order-insensitivity
        # wins over strict spec compliance. Each BY* field maps to
        # the atomic FormatType representing what its items are.
        regex    = (r"^FREQ=(?P<freq>SECONDLY|MINUTELY|HOURLY|DAILY|WEEKLY|MONTHLY|YEARLY)"
                    r"(?:;INTERVAL=(?P<interval>\d+))?"
                    r"(?:;COUNT=(?P<count>\d+))?"
                    r"(?:;UNTIL=(?P<until>[0-9TZ:+\-]+))?"
                    r"(?:;BYSECOND=(?P<bysecond>[0-9,]+))?"
                    r"(?:;BYMINUTE=(?P<byminute>[0-9,]+))?"
                    r"(?:;BYHOUR=(?P<byhour>[0-9,]+))?"
                    r"(?:;BYDAY=(?P<byday>[A-Z,0-9+\-]+))?"
                    r"(?:;BYMONTHDAY=(?P<bymonthday>[0-9,+\-]+))?"
                    r"(?:;BYYEARDAY=(?P<byyearday>[0-9,+\-]+))?"
                    r"(?:;BYWEEKNO=(?P<byweekno>[0-9,+\-]+))?"
                    r"(?:;BYMONTH=(?P<bymonth>[0-9,]+))?"
                    r"(?:;BYSETPOS=(?P<bysetpos>[0-9,+\-]+))?"
                    r"(?:;WKST=(?P<wkst>SU|MO|TU|WE|TH|FR|SA))?"
                    r"$"),
        template = "FREQ={freq}",
        parts    = {"freq":      "TEXT",
                    "interval":  "INT32",
                    "count":     "INT32",
                    "until":     "DATETIME",
                    "bysecond":  "SECOND",
                    "byminute":  "MINUTE",
                    "byhour":    "HOUR",
                    "byday":     "TEXT",
                    "bymonthday":"DAY",
                    "byyearday": "DAY_OF_YEAR",
                    "byweekno":  "ISO_WEEK_NUM",
                    "bymonth":   "MONTH_OF_YEAR",
                    "bysetpos":  "INT32",
                    "wkst":      "TEXT"},
    ),

    # BCP 47 locale: lang[-script][-region][-variant]. Script is always
    # 4 chars, region 2-3 chars, variant 5-8 chars.
    FormatType.LOCALE: FormatPattern(
        regex    = (r"^(?P<lang>[a-z]{2,3})"
                    r"(?:-(?P<script>[A-Z][a-z]{3}))?"
                    r"(?:-(?P<region>[A-Z]{2}|\d{3}))?"
                    r"(?:-(?P<variant>[A-Za-z0-9]{5,8}))?$"),
        template = "{lang}-{script}-{region}-{variant}",
        parts    = {"lang": "TEXT", "script": "TEXT",
                    "region": "TEXT", "variant": "TEXT"},
    ),
}


def _pattern_for(self: "FormatType") -> FormatPattern | None:
    """Return the FormatPattern attached to this FormatType, if any."""
    return PATTERNS.get(self)


def _parse(self: "FormatType", text: str) -> dict[str, str] | None:
    """Match `text` against the pattern; return the named-group dict
    or None if it doesn't match. Group values are the raw strings
    (not yet typed) — pair with `parts` to know what each is."""
    p = PATTERNS.get(self)
    if p is None:
        return None
    m = re.match(p.regex, text or "")
    if m is None:
        return None
    return {k: (v if v is not None else "") for k, v in m.groupdict().items()}


def _render(self: "FormatType", parts: dict[str, object]) -> str:
    """Fill the template with `parts`. Missing optional groups become
    empty strings; integer-typed groups go through the template's
    standard `:02d` / `:04d` formatters."""
    p = PATTERNS.get(self)
    if p is None:
        raise ValueError(f"{self.name!r} has no FormatPattern")
    safe: dict[str, object] = {}
    # Preserve every named placeholder; supply "" for missing.
    for name in re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)", p.template):
        v = parts.get(name, "")
        if isinstance(v, str) and v == "" and "{" + name + ":" in p.template:
            # Numeric placeholder + missing value → 0 keeps the
            # template valid (caller can omit optional fields).
            safe[name] = 0
        else:
            safe[name] = v
    return p.template.format(**safe)


# Bind helpers as static methods on the enum.
FormatType.pattern = _pattern_for     # type: ignore[attr-defined]
FormatType.parse   = _parse           # type: ignore[attr-defined]
FormatType.render  = _render          # type: ignore[attr-defined]
