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

from dataclasses import dataclass
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
    DAY          = "day"          # day-of-month (1..31)
    HOUR         = "hour"         # 0..23
    MINUTE       = "minute"       # 0..59
    SECOND       = "second"       # 0..59
    MILLISECOND  = "millisecond"  # 0..999
    TIMEZONE     = "timezone"     # IANA tz name, e.g. "Europe/London"
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


# ---- mapping + enum ----------------------------------------------------
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
    DAY           = FormatMapping(T.INTEGER, F.DAY,          S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "1..31")
    HOUR          = FormatMapping(T.INTEGER, F.HOUR,         S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..23")
    MINUTE        = FormatMapping(T.INTEGER, F.MINUTE,       S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..59")
    SECOND        = FormatMapping(T.INTEGER, F.SECOND,       S.SMALLINT,    "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..59")
    MILLISECOND   = FormatMapping(T.INTEGER, F.MILLISECOND,  S.INTEGER,     "kotlin.Int",                            C.NUMBER_FIELD,        H.NUMBER,         Y.INT,    "0..999")
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
