///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//RUNTIME_OPTIONS -Xmx512m

// --- OpenAPI / WireMock ---
//DEPS org.wiremock:wiremock:3.9.1
//DEPS io.swagger.parser.v3:swagger-parser:2.1.22

// --- Ktor (AsyncAPI + MCP) ---
//DEPS io.ktor:ktor-server-core-jvm:3.0.3
//DEPS io.ktor:ktor-server-netty-jvm:3.0.3
//DEPS io.ktor:ktor-server-websockets-jvm:3.0.3
//DEPS io.ktor:ktor-server-sse-jvm:3.0.3
//DEPS io.ktor:ktor-server-content-negotiation-jvm:3.0.3
//DEPS io.ktor:ktor-serialization-kotlinx-json-jvm:3.0.3

// --- kotlinx serialization (shared codecs) ---
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3

// --- RSocket ---
//DEPS io.rsocket.kotlin:rsocket-core-jvm:0.20.0
//DEPS io.rsocket.kotlin:rsocket-transport-ktor-websocket-server-jvm:0.20.0

// --- JDBC (Spring + Postgres + PostGIS) ---
//DEPS org.springframework:spring-jdbc:6.1.12
//DEPS org.springframework:spring-tx:6.1.12
//DEPS com.zaxxer:HikariCP:5.1.0
//DEPS org.postgresql:postgresql:42.7.4
//DEPS net.postgis:postgis-jdbc:2024.1.0

// --- CLI + logging ---
//DEPS com.github.ajalt.clikt:clikt-jvm:5.0.3
//DEPS org.slf4j:slf4j-simple:2.0.13

//SOURCES openapi/Wiremock.kt
//SOURCES asyncapi/AsyncApiServer.kt
//SOURCES mcp/McpServer.kt
//SOURCES rsocket/RSocketServer.kt
//SOURCES jdbc/JdbcServer.kt

// One facade to mock every protocol an app ever speaks. A single
// `jbang api/api.mock.jbang.kt` process can host WireMock stubs
// alongside Ktor WS + SSE + MCP + RSocket so you trace a multi-
// protocol target (LM Studio REST + SSE streaming, for example)
// in one log file.
//
// Subcommand tree:
//   openapi  start   — WireMock from an OpenAPI document
//   asyncapi echo    — Ktor WS + SSE echo server
//   mcp      serve   — JSON-RPC MCP mock over SSE
//   rsocket  serve   — RSocket (skeleton)
//
// Each subcommand defaults to its own port so they can run side by
// side: openapi 8089, asyncapi 8090, mcp 8091, rsocket 8094.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.main
import com.github.ajalt.clikt.core.subcommands

class ApiMockRoot : CliktCommand(name = "api-mock") {
    override fun run() = Unit
}

fun main(args: Array<String>) = ApiMockRoot().subcommands(
    OpenApiGroup().subcommands(OpenApiStart()),
    AsyncApiGroup().subcommands(AsyncApiEcho()),
    McpGroup().subcommands(McpServe()),
    RSocketGroup().subcommands(RSocketServe()),
    JdbcGroup().subcommands(JdbcServe()),
).main(args)
