///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//DEPS io.grpc:grpc-netty-shaded:1.66.0
//DEPS io.grpc:grpc-protobuf:1.66.0
//DEPS io.grpc:grpc-stub:1.66.0
//DEPS io.grpc:grpc-kotlin-stub:1.4.1
//DEPS org.jetbrains.kotlinx:kotlinx-serialization-protobuf:1.7.3
//DEPS org.jetbrains.kotlinx:kotlinx-coroutines-core:1.8.1

// gRPC mock server — stands up a grpc-kotlin Netty server on --port.
//
// Proto files live under api/grpc/proto/; the jbang script expects
// compiled descriptors. For ad-hoc schemas, we rely on
// kotlinx.serialization.protobuf with the @Serializable message class
// passed in at registration time (see common/codecs.kt).
//
// Run:
//   jbang api/grpc/grpc.jbang.kt --proto api/grpc/proto/echo.desc --port 8093
//
// TODO
// - Load a FileDescriptorSet at startup so *.proto messages show up as
//   dynamically-invocable methods (no compilation step needed).
// - Expose a /health endpoint via Ktor on a side port for liveness.

fun main(args: Array<String>) {
    println("gRPC mock (skeleton). args=${args.joinToString(" ")}")
}
