// Mirror of comfyui_openapi_node/component_tables.py — JSON Schema →
// SQLite DDL, and PRAGMA → JSON Schema. Same algorithm on both sides;
// the Python test fixture `tests/fixtures/ddl-cases.json` (future)
// drives a parity check.

import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

fun sqlTypeFor(schema: JsonObject?): String {
    if (schema == null) return "TEXT"
    return when ((schema["type"] as? JsonPrimitive)?.contentOrNull) {
        "integer" -> "INTEGER"
        "number"  -> "REAL"
        "boolean" -> "INTEGER"
        "string"  -> when ((schema["format"] as? JsonPrimitive)?.contentOrNull) {
            "binary", "byte" -> "BLOB"
            else             -> "TEXT"
        }
        else      -> "TEXT"     // array / object / oneOf → JSON TEXT
    }
}

private val IDENT = Regex("[A-Za-z_][A-Za-z0-9_]*")

fun safeIdent(name: String): String =
    if (IDENT.matches(name)) name else "\"${name.replace("\"", "\"\"")}\""

/** Pick the primary key the same way Python does. */
fun primaryKey(schema: JsonObject): List<String> {
    (schema["x-primary-key"] as? JsonArray)?.let { arr ->
        val xs = arr.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }
        if (xs.isNotEmpty()) return xs
    }
    val required = (schema["required"] as? JsonArray)
        ?.mapNotNull { (it as? JsonPrimitive)?.contentOrNull } ?: emptyList()
    val props = schema["properties"] as? JsonObject
    if (props != null && "id" in props.keys && "id" in required) return listOf("id")
    return required.take(1)
}

data class Column(
    val name: String,
    val sqlType: String,
    val notNull: Boolean,
    val default: JsonElement?,
    val check: String?,
    val json: Boolean,
)

private fun checkFor(prop: JsonObject): String? {
    val type = (prop["type"] as? JsonPrimitive)?.contentOrNull ?: return null
    return when (type) {
        "boolean" -> "{col} IN (0, 1)"
        "integer" -> {
            val clauses = mutableListOf<String>()
            (prop["minimum"] as? JsonPrimitive)?.intOrNull?.let { clauses += "{col} >= $it" }
            (prop["maximum"] as? JsonPrimitive)?.intOrNull?.let { clauses += "{col} <= $it" }
            clauses.joinToString(" AND ").ifEmpty { null }
        }
        "number" -> {
            val clauses = mutableListOf<String>()
            (prop["minimum"] as? JsonPrimitive)?.doubleOrNull?.let { clauses += "{col} >= $it" }
            (prop["maximum"] as? JsonPrimitive)?.doubleOrNull?.let { clauses += "{col} <= $it" }
            clauses.joinToString(" AND ").ifEmpty { null }
        }
        "string" -> {
            val clauses = mutableListOf<String>()
            (prop["minLength"] as? JsonPrimitive)?.intOrNull?.let { clauses += "length({col}) >= $it" }
            (prop["maxLength"] as? JsonPrimitive)?.intOrNull?.let { clauses += "length({col}) <= $it" }
            (prop["pattern"]   as? JsonPrimitive)?.contentOrNull?.let {
                val safe = it.replace("*/", "*_/")
                clauses += "1 = 1 /* pattern: $safe */"
            }
            clauses.joinToString(" AND ").ifEmpty { null }
        }
        "array", "object" -> "json_valid({col})"
        else -> null
    }
}

fun columnsFromSchema(schema: JsonObject): List<Column> {
    val required = (schema["required"] as? JsonArray)
        ?.mapNotNull { (it as? JsonPrimitive)?.contentOrNull }?.toSet() ?: emptySet()
    val props = (schema["properties"] as? JsonObject) ?: return emptyList()
    return props.entries.map { (name, raw) ->
        val prop = (raw as? JsonObject) ?: JsonObject(emptyMap())
        val hasDefault = "default" in prop.keys
        Column(
            name      = name,
            sqlType   = sqlTypeFor(prop),
            notNull   = name in required && !hasDefault,
            default   = prop["default"],
            check     = checkFor(prop),
            json      = (prop["type"] as? JsonPrimitive)?.contentOrNull in setOf("array", "object"),
        )
    }
}
