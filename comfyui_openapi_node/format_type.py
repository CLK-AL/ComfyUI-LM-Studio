"""The five-way bridge: one `FormatType` tying together

    JSON Schema  (type + format)
    SQL / JDBC   (java.sql.Types affinity)
    Kotlin KClass (the type a Kotlin Table column would expose)
    Composable   (Compose Multiplatform widget hint)
    HTML         (`<input type="...">` family)
    ComfyUI      (the INPUT_TYPES primitive: STRING / INT / FLOAT /
                  BOOLEAN or a combo tuple)

Whenever two of those need to agree (and they all do, constantly), go
through this enum instead of writing a new bespoke map. The Kotlin
mirror lives at `api/common/FormatType.kt` — the parity test under
`tests/fixtures/format-type-bridge.json` proves both sides agree.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .sql_types import SqlTypes


@dataclass(frozen=True)
class FormatMapping:
    json_type: str            # "string" | "integer" | "number" | "boolean" | "object" | "array"
    json_format: str | None   # e.g. "email", "date-time", "uuid", None for plain
    sql_type: SqlTypes        # JDBC enum (matches api/common/SqlTypes.kt)
    kclass: str               # Kotlin KClass FQN — the real `KClass<*>` lives on the Kt side
    composable: str           # Compose fn name
    html_input: str           # HTML <input type="…"> value
    comfy: str                # INPUT_TYPES primitive ("STRING" | "INT" | "FLOAT" | "BOOLEAN" | "COMBO")
    placeholder: str = ""


class FormatType(Enum):
    TEXT            = FormatMapping("string",   None,         SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING")
    TEXTAREA        = FormatMapping("string",   "textarea",   SqlTypes.LONGVARCHAR,"kotlin.String",                "OutlinedTextField","text",     "STRING")
    PASSWORD        = FormatMapping("string",   "password",   SqlTypes.VARCHAR,   "kotlin.String",                 "TextField(visualTransformation=PasswordVisualTransformation())", "password", "STRING")
    EMAIL           = FormatMapping("string",   "email",      SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "email",    "STRING", "user@example.com")
    TEL             = FormatMapping("string",   "tel",        SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "tel",      "STRING", "+1 555 0100")
    URL             = FormatMapping("string",   "uri",        SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "url",      "STRING", "https://…")
    UUID            = FormatMapping("string",   "uuid",       SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING", "00000000-0000-0000-0000-000000000000")
    COLOR           = FormatMapping("string",   "color",      SqlTypes.VARCHAR,   "kotlin.String",                 "ColorPicker",      "color",    "STRING", "#RRGGBB")
    DATE            = FormatMapping("string",   "date",       SqlTypes.DATE,      "kotlinx.datetime.LocalDate",    "DatePicker",       "date",     "STRING", "YYYY-MM-DD")
    TIME            = FormatMapping("string",   "time",       SqlTypes.TIME,      "kotlinx.datetime.LocalTime",    "TimePicker",       "time",     "STRING", "HH:MM:SS")
    DATETIME        = FormatMapping("string",   "date-time",  SqlTypes.TIMESTAMP, "kotlinx.datetime.Instant",      "DateTimePicker",   "datetime-local", "STRING", "YYYY-MM-DDTHH:MM:SSZ")
    DURATION        = FormatMapping("string",   "duration",   SqlTypes.VARCHAR,   "kotlin.time.Duration",          "TextField",        "text",     "STRING", "P1DT2H")
    IPV4            = FormatMapping("string",   "ipv4",       SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING", "0.0.0.0")
    IPV6            = FormatMapping("string",   "ipv6",       SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING", "::1")
    HOSTNAME        = FormatMapping("string",   "hostname",   SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING", "example.com")
    REGEX           = FormatMapping("string",   "regex",      SqlTypes.VARCHAR,   "kotlin.String",                 "TextField",        "text",     "STRING", "^.*$")
    JSON_POINTER    = FormatMapping("string",   "json-pointer",SqlTypes.VARCHAR,  "kotlin.String",                 "TextField",        "text",     "STRING", "/foo/bar")
    BYTE            = FormatMapping("string",   "byte",       SqlTypes.VARBINARY, "kotlin.ByteArray",              "FilePicker",       "file",     "STRING")
    BINARY          = FormatMapping("string",   "binary",     SqlTypes.BLOB,      "kotlin.ByteArray",              "FilePicker",       "file",     "STRING")
    GEOJSON         = FormatMapping("object",   "geojson",    SqlTypes.OTHER,     "kotlinx.serialization.json.JsonObject", "MapPicker", "text",     "STRING", '{"type":"Point","coordinates":[0,0]}')
    JSON_OBJECT     = FormatMapping("object",   "json",       SqlTypes.OTHER,     "kotlinx.serialization.json.JsonObject", "OutlinedTextField", "text", "STRING")
    JSON_ARRAY      = FormatMapping("array",    "json",       SqlTypes.ARRAY,     "kotlinx.serialization.json.JsonArray",  "OutlinedTextField", "text", "STRING")
    INT32           = FormatMapping("integer",  "int32",      SqlTypes.INTEGER,   "kotlin.Int",                    "Slider",           "number",   "INT")
    INT64           = FormatMapping("integer",  "int64",      SqlTypes.BIGINT,    "kotlin.Long",                   "Slider",           "number",   "INT")
    FLOAT           = FormatMapping("number",   "float",      SqlTypes.REAL,      "kotlin.Float",                  "Slider",           "number",   "FLOAT")
    DOUBLE          = FormatMapping("number",   "double",     SqlTypes.DOUBLE,    "kotlin.Double",                 "Slider",           "number",   "FLOAT")
    BOOL            = FormatMapping("boolean",  None,         SqlTypes.BOOLEAN, "kotlin.Boolean",            "Switch",           "checkbox", "BOOLEAN")
    ENUM            = FormatMapping("string",   "enum",       SqlTypes.VARCHAR,   "kotlin.String",                 "DropdownMenu",     "text",     "COMBO")


# --- dispatch helpers ---------------------------------------------------
def _from_json_schema(schema: dict) -> FormatType:
    """Pick the best FormatType for a JSON Schema fragment."""
    if not isinstance(schema, dict):
        return FormatType.TEXT
    if "enum" in schema:
        return FormatType.ENUM
    t = schema.get("type")
    f = schema.get("format") or ""
    if t == "boolean":
        return FormatType.BOOL
    if t == "integer":
        return FormatType.INT64 if f == "int64" else FormatType.INT32
    if t == "number":
        return FormatType.DOUBLE if f == "double" else FormatType.FLOAT
    if t == "array":
        return FormatType.JSON_ARRAY
    if t == "object":
        if f == "geojson":
            return FormatType.GEOJSON
        return FormatType.JSON_OBJECT
    # t == "string" (or unspecified)
    for ft in FormatType:
        if ft.value.json_type == "string" and (ft.value.json_format or "") == f:
            return ft
    return FormatType.TEXT


def _from_sql(sql_type) -> FormatType:
    """Pick a FormatType from a java.sql.Types name, int, or
    `SqlTypes` enum value."""
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
        if ft.value.sql_type == resolved:
            return ft
    return FormatType.TEXT


# Attach the classmethod-style lookups as plain callables so the enum's
# value objects stay light (no methods required on FormatMapping).
FormatType.from_json_schema = staticmethod(_from_json_schema)       # type: ignore[attr-defined]
FormatType.from_sql         = staticmethod(_from_sql)               # type: ignore[attr-defined]
