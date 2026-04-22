///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//DEPS io.modelcontextprotocol:kotlin-sdk:0.6.0
//DEPS io.ktor:ktor-server-core:3.0.3
//DEPS io.ktor:ktor-server-netty:3.0.3
//DEPS io.ktor:ktor-server-sse:3.0.3
//DEPS io.ktor:ktor-server-websockets:3.0.3
//DEPS io.ktor:ktor-server-content-negotiation:3.0.3
//DEPS io.ktor:ktor-serialization-kotlinx-json:3.0.3
//DEPS org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1
//DEPS org.slf4j:slf4j-simple:2.0.13
//SOURCES ../common/codecs.kt

// Minimal MCP (Model Context Protocol) mock server using the official
// Kotlin SDK. Starts a JSON-RPC server over either stdio or SSE.
// The Kotlin MCP SDK handles the handshake + tools/list + tools/call
// mechanics; we register a single "echo" tool that returns whatever
// input payload it gets (useful for verifying the transport from
// ComfyUI-OpenAPI-Node).
//
// Run:
//   jbang api/mcp/mcp.jbang.kt --transport sse --port 8091
//   jbang api/mcp/mcp.jbang.kt --transport stdio   # pipe-based
//
// TODO
// - Replace the placeholder main() once the SDK API stabilizes.
//   The current SDK version pin needs to be bumped; the shape of this
//   script is the important part: `jbang api/mcp/mcp.jbang.kt …` is
//   the contract the Python side calls.

fun main(args: Array<String>) {
    println("MCP mock (skeleton). Install Kotlin MCP SDK and wire a server here.")
    println("args=${args.joinToString(" ")}")
}
