package al.clk.api

// MCP Ktor handler, consumed by api/api.mock.jbang.kt via //SOURCES.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int
import io.ktor.http.ContentType
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.request.receiveText
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import io.ktor.server.sse.SSE
import io.ktor.server.sse.sse
import io.ktor.sse.ServerSentEvent
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import kotlinx.serialization.json.putJsonObject

private val mcpLog = org.slf4j.LoggerFactory.getLogger("mcp")
private val MCP_JSON = Json { ignoreUnknownKeys = true }

class McpGroup : CliktCommand(name = "mcp") {
    override fun help(context: Context) = "Model Context Protocol mock over SSE."
    override fun run() = Unit
}

class McpServe : CliktCommand(name = "serve") {
    override fun help(context: Context) =
        "JSON-RPC MCP mock: initialize / tools/list / tools/call."
    val port by option("-p", "--port").int().default(8091)
    val host by option("--host").default("127.0.0.1")

    override fun run() {
        mcpLog.info("MCP mock on http://{}:{}/mcp", host, port)
        embeddedServer(Netty, host = host, port = port) {
            install(SSE)
            routing {
                get("/healthz") { call.respondText("ok") }
                sse("/mcp") {
                    val hello = buildJsonObject {
                        put("jsonrpc", "2.0")
                        put("method", "initialized")
                        putJsonObject("params") { }
                    }
                    send(ServerSentEvent(data = hello.toString()))
                }
                post("/mcp") {
                    val body = call.receiveText()
                    mcpLog.info("mcp recv: {}", body)
                    val req = MCP_JSON.parseToJsonElement(body).jsonObject
                    val id = req["id"]
                    val method = req["method"]?.jsonPrimitive?.content
                    val resp = when (method) {
                        "initialize" -> buildJsonObject {
                            put("jsonrpc", "2.0"); if (id != null) put("id", id)
                            putJsonObject("result") {
                                put("protocolVersion", "2024-11-05")
                                putJsonObject("capabilities") { putJsonObject("tools") {} }
                                putJsonObject("serverInfo") {
                                    put("name", "mcp-mock"); put("version", "0.1.0")
                                }
                            }
                        }
                        "tools/list" -> buildJsonObject {
                            put("jsonrpc", "2.0"); if (id != null) put("id", id)
                            putJsonObject("result") {
                                putJsonArray("tools") {
                                    addJsonObject {
                                        put("name", "echo")
                                        put("description", "Echo the `text` input.")
                                        putJsonObject("inputSchema") {
                                            put("type", "object")
                                            putJsonArray("required") { add(JsonPrimitive("text")) }
                                            putJsonObject("properties") {
                                                putJsonObject("text") { put("type", "string") }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        "tools/call" -> buildJsonObject {
                            put("jsonrpc", "2.0"); if (id != null) put("id", id)
                            putJsonObject("result") {
                                putJsonArray("content") {
                                    addJsonObject { put("type", "text"); put("text", "ok") }
                                }
                            }
                        }
                        else -> buildJsonObject {
                            put("jsonrpc", "2.0"); if (id != null) put("id", id)
                            putJsonObject("error") {
                                put("code", -32601)
                                put("message", "Method not found: $method")
                            }
                        }
                    }
                    mcpLog.info("mcp send: {}", resp)
                    call.respondText(resp.toString(), ContentType.Application.Json)
                }
            }
        }.start(wait = true)
    }
}
