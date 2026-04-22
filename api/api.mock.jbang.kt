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

// --- kotlinx serialization + datetime (shared codecs + FormatType) ---
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3
//DEPS org.jetbrains.kotlinx:kotlinx-datetime-jvm:0.6.1

// --- Wire + Moshi (proto-generated messages + JSON projection) ---
// `api/model/types.proto` is the source of truth. Wire generates KMP
// Kotlin classes into a Gradle Compose module; at runtime we pull the
// runtime + Moshi adapter so the already-generated classes (or the
// hand-written mirror in api/common/) can be wire-encoded and
// JSON-projected.
//DEPS com.squareup.wire:wire-runtime-jvm:5.1.0
//DEPS com.squareup.wire:wire-moshi-adapter:5.1.0
//DEPS com.squareup.moshi:moshi:1.15.1
//DEPS com.squareup.moshi:moshi-kotlin:1.15.1

// --- Jackson (idiomatic JVM JSON tree) ---
// `common/` stays KMP-portable by declaring kotlinx.serialization.json
// types in its KClassEnum rows. JVM consumers (Spring JDBC, servlet
// handlers, Jackson-native REST libs) resolve the paired JClassEnum
// entry to Jackson's `JsonNode` / `ObjectNode` / `ArrayNode` tree —
// the idiomatic Java JSON shape. Declared here so JVM-only call sites
// can cast through `kclass.jclass.jclass` at runtime.
//DEPS com.fasterxml.jackson.core:jackson-databind:2.17.2
//DEPS com.fasterxml.jackson.module:jackson-module-kotlin:2.17.2
//DEPS com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.17.2

// --- iCalendar + vCard parsing (string/file → jCal/jCard) ---
//DEPS org.mnode.ical4j:ical4j:4.0.5
//DEPS com.googlecode.ez-vcard:ez-vcard:0.12.1

// --- Fake data generator (seeded; atomic counter for IDs) ---
// Two providers registered in FakeProviderFactory — user picks via
// `--faker datafaker|kotlin-faker` on subcommands that generate rows.
// Since the stack is JVM + jbang + GraalVM 25 native we just ship
// both and let them co-exist.
//DEPS net.datafaker:datafaker:2.4.0
//DEPS io.github.serpro69:kotlin-faker:1.16.0

// --- RSocket ---
//DEPS io.rsocket.kotlin:rsocket-core-jvm:0.20.0
//DEPS io.rsocket.kotlin:rsocket-transport-ktor-websocket-server-jvm:0.20.0

// --- JDBC (JVM path: Spring + Postgres + PostGIS) ---
//DEPS org.springframework:spring-jdbc:6.1.12
//DEPS org.springframework:spring-tx:6.1.12
//DEPS com.zaxxer:HikariCP:5.1.0
//DEPS org.postgresql:postgresql:42.7.4
//DEPS net.postgis:postgis-jdbc:2024.1.0

// --- JDBC (KMP-portable path: SQLDelight + Exposed) ---
// Both libraries have Kotlin Multiplatform publications — the same
// CRUD code compiled here can move into a Compose Multiplatform
// module's commonMain without touching Spring. See
// docs/KMP_MIGRATION.md for the lift.
//DEPS org.xerial:sqlite-jdbc:3.46.1.0
//DEPS app.cash.sqldelight:jdbc-driver:2.0.2
//DEPS app.cash.sqldelight:runtime-jvm:2.0.2
//DEPS org.jetbrains.exposed:exposed-core:0.54.0
//DEPS org.jetbrains.exposed:exposed-dao:0.54.0
//DEPS org.jetbrains.exposed:exposed-jdbc:0.54.0
//DEPS org.jetbrains.exposed:exposed-json:0.54.0
//DEPS org.jetbrains.exposed:exposed-kotlin-datetime:0.54.0

// --- CLI + logging ---
//DEPS com.github.ajalt.clikt:clikt-jvm:5.0.3
//DEPS org.slf4j:slf4j-simple:2.0.13

//SOURCES common/Naming.kt
//SOURCES common/ComponentTables.kt
//SOURCES common/SqlTypes.kt
//SOURCES common/FormatType.kt
//SOURCES common/JClassKClass.kt
//SOURCES common/JdbcExposed.kt
//SOURCES common/IcsVcfParser.kt
//SOURCES common/FakeProvider.kt
//SOURCES common/DatafakerProvider.kt
//SOURCES common/APIMock.kt
//SOURCES openapi/Wiremock.kt
//SOURCES asyncapi/AsyncApiServer.kt
//SOURCES mcp/McpServer.kt
//SOURCES rsocket/RSocketServer.kt
//SOURCES jdbc/JdbcServer.kt

// Thin jbang shell around `common/APIMock.kt`. All Clikt wiring, the
// root command, and the subcommand tree live under `common/` so the
// same entry point can be reused from a KMP Compose Multiplatform
// module without copying the group/subcommand layout. This file only
// declares the JVM stack (jbang //DEPS + //SOURCES) and forwards
// process args to `apiMockMain`.

fun main(args: Array<String>) = apiMockMain(args)
