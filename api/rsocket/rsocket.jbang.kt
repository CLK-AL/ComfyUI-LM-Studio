///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//DEPS io.rsocket.kotlin:rsocket-ktor-server-jvm:0.16.0
//DEPS io.rsocket.kotlin:rsocket-transport-ktor-websocket-server-jvm:0.16.0
//DEPS io.ktor:ktor-server-core:3.0.3
//DEPS io.ktor:ktor-server-netty:3.0.3
//DEPS io.ktor:ktor-server-websockets:3.0.3
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3
//DEPS org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1
//SOURCES ../common/codecs.kt

// RSocket mock server — rsocket-kotlin over Ktor WebSocket. Supports
// all four RSocket interaction models: requestResponse, requestStream,
// requestChannel, fireAndForget. Payload bodies go through
// common/codecs.kt for content negotiation.
//
// Run:
//   jbang api/rsocket/rsocket.jbang.kt --port 8094
//
// TODO
// - Declarative responder config from a YAML under api/rsocket/spec/
//   (one "route" per interaction).

fun main(args: Array<String>) {
    println("RSocket mock (skeleton). args=${args.joinToString(" ")}")
}
