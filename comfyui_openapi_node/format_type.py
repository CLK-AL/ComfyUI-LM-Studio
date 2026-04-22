"""The five-way bridge: one `FormatType` tying together

    JsonType        (the JSON Schema primitive)
    JsonFormat      (the `format` keyword)
    SqlTypes        (JDBC enum — see sql_types.py)
    KClass (Kotlin) (as a FQN string on this side; real KClass<*> on Kt)
    ComposeWidget   (Compose Multiplatform widget)
    HtmlInputType   (HTML <input type=…> / <select> / <textarea>)
    ComfyType       (ComfyUI INPUT_TYPES primitive)

`HtmlInputType` covers every form-native HTML element we render to:
the full `<input type=…>` roster (text, email, url, tel, number, date,
time, datetime-local, month, week, color, checkbox, radio, file,
password, range, search, hidden) plus the `<textarea>` and `<select>`
elements that live outside `<input>`.

`ComfyType` covers the five ComfyUI INPUT_TYPES primitives (STRING,
INT, FLOAT, BOOLEAN, COMBO); COMBO absorbs dropdowns, radio groups,
and multi-selects — rendering variant is picked by the Compose /
HTML widgets next to it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

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


class HtmlInputType(str, Enum):
    # <input type="…">
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
    # non-<input> form elements carried under the same enum for
    # uniform widget dispatch.
    TEXTAREA       = "textarea"
    SELECT         = "select"
    SELECT_MULTI   = "select[multiple]"


class ComfyType(str, Enum):
    STRING  = "STRING"
    INT     = "INT"
    FLOAT   = "FLOAT"
    BOOLEAN = "BOOLEAN"
    COMBO   = "COMBO"


class ComposeWidget(str, Enum):
    TEXT_FIELD          = "TextField"
    OUTLINED_TEXT_FIELD = "OutlinedTextField"
    PASSWORD_FIELD      = "TextField(visualTransformation=PasswordVisualTransformation())"
    SEARCH_FIELD        = "SearchBar"
    COLOR_PICKER        = "ColorPicker"
    DATE_PICKER         = "DatePicker"
    TIME_PICKER         = "TimePicker"
    DATETIME_PICKER     = "DateTimePicker"
    MONTH_PICKER        = "MonthPicker"
    WEEK_PICKER         = "WeekPicker"
    FILE_PICKER         = "FilePicker"
    MAP_PICKER          = "MapPicker"
    SLIDER              = "Slider"
    RANGE_SLIDER        = "RangeSlider"
    SWITCH              = "Switch"
    CHECKBOX            = "Checkbox"
    CHECKBOX_GROUP      = "CheckboxGroup"
    RADIO_GROUP         = "RadioGroup"
    DROPDOWN_MENU       = "DropdownMenu"
    HIDDEN_FIELD        = "HiddenField"


# ---- mapping + enum ----------------------------------------------------
@dataclass(frozen=True)
class FormatMapping:
    json_type:   JsonType
    json_format: JsonFormat
    sql_type:    SqlTypes
    kclass:      str                # Kotlin KClass FQN
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
    # Boolean rendering variants (BOOL = Switch; CHECKBOX = native checkbox)
    BOOL          = FormatMapping(T.BOOLEAN, F.NONE,         S.BOOLEAN,     "kotlin.Boolean",                        C.SWITCH,              H.CHECKBOX,       Y.BOOLEAN)
    CHECKBOX      = FormatMapping(T.BOOLEAN, F.NONE,         S.BOOLEAN,     "kotlin.Boolean",                        C.CHECKBOX,            H.CHECKBOX,       Y.BOOLEAN)
    # Enum presentation variants
    ENUM          = FormatMapping(T.STRING,  F.ENUM,         S.VARCHAR,     "kotlin.String",                         C.DROPDOWN_MENU,       H.SELECT,         Y.COMBO)
    RADIO         = FormatMapping(T.STRING,  F.ENUM,         S.VARCHAR,     "kotlin.String",                         C.RADIO_GROUP,         H.RADIO,          Y.COMBO)
    MULTI_SELECT  = FormatMapping(T.ARRAY,   F.ENUM,         S.ARRAY,       "kotlin.collections.List",               C.CHECKBOX_GROUP,      H.SELECT_MULTI,   Y.COMBO)


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
    # STRING / NULL — match on format; prefer the first defined row
    # for that format.
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
