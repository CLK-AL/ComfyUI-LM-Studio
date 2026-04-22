// Shared naming convention mirror of comfyui_openapi_node/naming.py.
//
// Keeping this in Kotlin lets the Ktor mock and Spring JDBC mock
// derive table names, message names, and SSE payload shapes the same
// way the Python ComfyUI side does. The test fixture at
// tests/fixtures/naming-cases.json is consumed by tests on both
// sides to prove the two implementations agree case-for-case.

import kotlin.text.Regex

private val PASCAL_SPLIT = Regex("(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
private val NON_IDENT    = Regex("[^A-Za-z0-9]+")

fun tokenise(s: String): List<String> =
    s.split(PASCAL_SPLIT).flatMap { it.split(NON_IDENT) }.filter { it.isNotEmpty() }

fun snake(name: String): String =
    tokenise(name).joinToString("_") { it.lowercase() }

fun pascal(name: String): String =
    tokenise(name).joinToString("") {
        it.lowercase().replaceFirstChar { c -> c.uppercase() }
    }

fun camel(name: String): String {
    val p = pascal(name)
    return if (p.isEmpty()) p else p.replaceFirstChar { it.lowercase() }
}

/** Canonical JSON Schema component name (PascalCase). */
fun componentName(anyCase: String): String = pascal(anyCase)

/** SQLite / JDBC table name (snake_case). */
fun tableName(anyCase: String): String = snake(anyCase)

/** AsyncAPI message name for a mutation on [component]. */
fun messageName(component: String, verb: String = "Updated"): String =
    pascal(component) + pascal(verb)

/** Stable name for a JSON Patch applied to a component (snake). */
fun patchName(component: String): String = "${snake(component)}.patch"

/** ComfyUI canvas title for an auto-generated node. */
fun nodeDisplay(api: String, operationId: String): String =
    "API · $api · $operationId"

/** Python class name registered in NODE_CLASS_MAPPINGS. */
fun nodeClass(api: String, operationId: String): String =
    "API_${api.replace('-', '_')}_$operationId"

private val OP_TO_VERB = mapOf(
    "put"     to "Created",
    "add"     to "Created",
    "replace" to "Updated",
    "remove"  to "Deleted",
)

/** Translate an audit event into the SSE `data:` payload with
 *  before/after, matching patch_op_to_sse in Python. */
fun patchOpToSse(event: Map<String, Any?>): Map<String, Any?> {
    val component = (event["component"] ?: event["type"]) as? String ?: ""
    val pk        = (event["pk"] ?: event["id"])
    val op        = (event["op"] as? String) ?: ""
    return mapOf(
        "component" to component,
        "pk"        to pk,
        "op"        to op,
        "path"      to (event["path"] ?: ""),
        "before"    to (event["old"] ?: event["old_value"]),
        "after"     to (event["new"] ?: event["new_value"]),
        "message"   to messageName(component, OP_TO_VERB[op] ?: "Patched"),
        "api"       to event["api"],
        "ts"        to event["ts"],
    )
}
