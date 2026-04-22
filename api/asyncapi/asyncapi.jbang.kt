///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//DEPS io.ktor:ktor-server-core:3.0.3
//DEPS io.ktor:ktor-server-netty:3.0.3
//DEPS io.ktor:ktor-server-sse:3.0.3
//DEPS io.ktor:ktor-server-websockets:3.0.3
//DEPS io.ktor:ktor-server-content-negotiation:3.0.3
//DEPS io.ktor:ktor-serialization-kotlinx-json:3.0.3
//SOURCES ../common/codecs.kt

// AsyncAPI mock server — Ktor Netty hosting SSE + WebSocket endpoints
// declared in an AsyncAPI YAML (channels + operations).
//
// Parses channels from an AsyncAPI spec passed via --spec and exposes:
//   ws://<host>:<port>/<channel>     — echo server, messages
//                                       encoded/decoded through
//                                       common/codecs.kt
//   GET /<channel>                    — SSE if the operation is
//                                       `subscribe` bound to sse
//
// Run:
//   jbang api/asyncapi/asyncapi.jbang.kt --spec api/asyncapi/spec/my.yaml --port 8092
//
// TODO
// - Wire kotlinx + xmlutil + msgpack via common/codecs.kt for each
//   channel's content-types.
// - AsyncAPI Kotlin parser — no official lib yet; the Ktor text plugin
//   is fine as a pass-through until then.

fun main(args: Array<String>) {
    println("AsyncAPI mock (skeleton). args=${args.joinToString(" ")}")
}
