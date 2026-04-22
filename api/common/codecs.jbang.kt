///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.7.3
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-cbor:1.7.3
//DEPS io.github.pdvrieze.xmlutil:serialization-jvm:0.90.3
//DEPS org.msgpack:msgpack-core:0.9.8
//SOURCES codecs.kt

// Keep this file as the single place where *every* protocol handler in
// /api/ reads its negotiation dependencies from. //SOURCES pulls the
// actual Codec interface + registry from codecs.kt so subprojects can
//     //SOURCES ../common/codecs.kt
// and get the same implementation.
//
// Run:  jbang api/common/codecs.jbang.kt <negotiate|encode|decode> …
//
// This CLI is intentionally a tiny demo — the point is to keep the
// dependency list + SOURCES pointer in one place.
import kotlin.system.exitProcess

fun main(args: Array<String>) {
    println("Kotlinx codecs registered. Use this file via //SOURCES from another jbang script.")
    exitProcess(0)
}
