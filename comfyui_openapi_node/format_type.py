"""The five-way bridge: one `FormatType` tying together

    JsonType        (the JSON Schema primitive)
    JsonFormat      (the `format` keyword)
    SqlTypes        (JDBC enum — see sql_types.py)
    KClass (Kotlin) (as a FQN string on this side; real KClass<*> on Kt)
    ComposeWidget   (Compose Multiplatform widget)
    HtmlInputType   (HTML <input type="…">)
    ComfyType       (ComfyUI INPUT_TYPES primitive)

Every field on `FormatMapping` except the FQN string and placeholder is
now a proper enum. The Kotlin mirror in `api/common/FormatType.kt`
uses the matching Kt enum classes; the parity fixture under
`tests/fixtures/format-type-bridge.json` drives tests on both sides.
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


class HtmlInputType(str, Enum):
    TEXT           = "text"
    EMAIL          = "email"
    URL            = "url"
    TEL            = "tel"
    NUMBER         = "number"
    DATE           = "date"
    TIME           = "time"
    DATETIME_LOCAL = "datetime-local"
    COLOR          = "color"
    CHECKBOX       = "checkbox"
    FILE           = "file"
    PASSWORD       = "password"


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
    COLOR_PICKER        = "ColorPicker"
    DATE_PICKER         = "DatePicker"
    TIME_PICKER         = "TimePicker"
    DATETIME_PICKER     = "DateTimePicker"
    FILE_PICKER         = "FilePicker"
    MAP_PICKER          = "MapPicker"
    SLIDER              = "Slider"
    SWITCH              = "Switch"
    DROPDOWN_MENU       = "DropdownMenu"


# ---- mapping + enum ----------------------------------------------------
@dataclass(frozen=True)
class FormatMapping:
    json_type:   JsonType
    json_format: JsonFormat         # JsonFormat.NONE for "no format"
    sql_type:    SqlTypes
    kclass:      str                # Kotlin KClass FQN (real KClass<*> on the Kt side)
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
    TEXT         = FormatMapping(T.STRING,  F.NONE,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING)
    TEXTAREA     = FormatMapping(T.STRING,  F.TEXTAREA,     S.LONGVARCHAR, "kotlin.String",                         C.OUTLINED_TEXT_FIELD, H.TEXT,           Y.STRING)
    PASSWORD     = FormatMapping(T.STRING,  F.PASSWORD,     S.VARCHAR,     "kotlin.String",                         C.PASSWORD_FIELD,      H.PASSWORD,       Y.STRING)
    EMAIL        = FormatMapping(T.STRING,  F.EMAIL,        S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.EMAIL,          Y.STRING, "user@example.com")
    TEL          = FormatMapping(T.STRING,  F.TEL,          S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEL,            Y.STRING, "+1 555 0100")
    URL          = FormatMapping(T.STRING,  F.URI,          S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.URL,            Y.STRING, "https://…")
    UUID         = FormatMapping(T.STRING,  F.UUID,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "00000000-0000-0000-0000-000000000000")
    COLOR        = FormatMapping(T.STRING,  F.COLOR,        S.VARCHAR,     "kotlin.String",                         C.COLOR_PICKER,        H.COLOR,          Y.STRING, "#RRGGBB")
    DATE         = FormatMapping(T.STRING,  F.DATE,         S.DATE,        "kotlinx.datetime.LocalDate",            C.DATE_PICKER,         H.DATE,           Y.STRING, "YYYY-MM-DD")
    TIME         = FormatMapping(T.STRING,  F.TIME,         S.TIME,        "kotlinx.datetime.LocalTime",            C.TIME_PICKER,         H.TIME,           Y.STRING, "HH:MM:SS")
    DATETIME     = FormatMapping(T.STRING,  F.DATE_TIME,    S.TIMESTAMP,   "kotlinx.datetime.Instant",              C.DATETIME_PICKER,     H.DATETIME_LOCAL, Y.STRING, "YYYY-MM-DDTHH:MM:SSZ")
    DURATION     = FormatMapping(T.STRING,  F.DURATION,     S.VARCHAR,     "kotlin.time.Duration",                  C.TEXT_FIELD,          H.TEXT,           Y.STRING, "P1DT2H")
    IPV4         = FormatMapping(T.STRING,  F.IPV4,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "0.0.0.0")
    IPV6         = FormatMapping(T.STRING,  F.IPV6,         S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "::1")
    HOSTNAME     = FormatMapping(T.STRING,  F.HOSTNAME,     S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "example.com")
    REGEX        = FormatMapping(T.STRING,  F.REGEX,        S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "^.*$")
    JSON_POINTER = FormatMapping(T.STRING,  F.JSON_POINTER, S.VARCHAR,     "kotlin.String",                         C.TEXT_FIELD,          H.TEXT,           Y.STRING, "/foo/bar")
    BYTE         = FormatMapping(T.STRING,  F.BYTE,         S.VARBINARY,   "kotlin.ByteArray",                      C.FILE_PICKER,         H.FILE,           Y.STRING)
    BINARY       = FormatMapping(T.STRING,  F.BINARY,       S.BLOB,        "kotlin.ByteArray",                      C.FILE_PICKER,         H.FILE,           Y.STRING)
    GEOJSON      = FormatMapping(T.OBJECT,  F.GEOJSON,      S.OTHER,       "kotlinx.serialization.json.JsonObject", C.MAP_PICKER,          H.TEXT,           Y.STRING, '{"type":"Point","coordinates":[0,0]}')
    JSON_OBJECT  = FormatMapping(T.OBJECT,  F.JSON,         S.OTHER,       "kotlinx.serialization.json.JsonObject", C.OUTLINED_TEXT_FIELD, H.TEXT,           Y.STRING)
    JSON_ARRAY   = FormatMapping(T.ARRAY,   F.JSON,         S.ARRAY,       "kotlinx.serialization.json.JsonArray",  C.OUTLINED_TEXT_FIELD, H.TEXT,           Y.STRING)
    INT32        = FormatMapping(T.INTEGER, F.INT32,        S.INTEGER,     "kotlin.Int",                            C.SLIDER,              H.NUMBER,         Y.INT)
    INT64        = FormatMapping(T.INTEGER, F.INT64,        S.BIGINT,      "kotlin.Long",                           C.SLIDER,              H.NUMBER,         Y.INT)
    FLOAT        = FormatMapping(T.NUMBER,  F.FLOAT,        S.REAL,        "kotlin.Float",                          C.SLIDER,              H.NUMBER,         Y.FLOAT)
    DOUBLE       = FormatMapping(T.NUMBER,  F.DOUBLE,       S.DOUBLE,      "kotlin.Double",                         C.SLIDER,              H.NUMBER,         Y.FLOAT)
    BOOL         = FormatMapping(T.BOOLEAN, F.NONE,         S.BOOLEAN,     "kotlin.Boolean",                        C.SWITCH,              H.CHECKBOX,       Y.BOOLEAN)
    ENUM         = FormatMapping(T.STRING,  F.ENUM,         S.VARCHAR,     "kotlin.String",                         C.DROPDOWN_MENU,       H.TEXT,           Y.COMBO)


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
