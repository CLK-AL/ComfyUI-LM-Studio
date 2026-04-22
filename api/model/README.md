# `/api/model` — proto source of truth for the FormatType bridge

`types.proto` is the single source of truth for every enum on the
five-way bridge (`FormatType` / `FormatMapping`). It's consumed three
ways — Wire (Kotlin Multiplatform), Moshi (JSON round-trip), and
`protoc` + `protobuf` (Python).

## Generation pipelines

### Kotlin (Wire — KMP-portable)

Add to a Compose Multiplatform module's `build.gradle.kts`:

```kotlin
plugins {
    id("com.squareup.wire") version "5.1.0"
}

wire {
    sourcePath { srcDir("../api/model") }
    kotlin {
        out = "src/commonMain/kotlin"
        rpcRole = "none"          // we only generate messages, not gRPC stubs
        javaInterop = true
    }
}

dependencies {
    implementation("com.squareup.wire:wire-runtime:5.1.0")
    // Moshi for JSON projection of the same messages
    implementation("com.squareup.moshi:moshi:1.15.1")
    implementation("com.squareup.moshi:moshi-kotlin:1.15.1")
    implementation("com.squareup.wire:wire-moshi-adapter:5.1.0")
}
```

`commonMain` then has `api/model/FormatMapping.kt`, `FormatRow.kt`,
`FormatCatalog.kt` plus every enum — line-for-line equivalents of the
hand-written `api/common/FormatType.kt`. Once the generated classes
exist, switch `FormatType` to wrap them and delete the duplication.

### Python (`protoc` + `protobuf`)

```bash
python -m pip install grpcio-tools          # ships protoc
python -m grpc_tools.protoc \
    -I api/model \
    --python_out=comfyui_openapi_node/gen \
    --pyi_out=comfyui_openapi_node/gen \
    api/model/types.proto
```

Output: `comfyui_openapi_node/gen/types_pb2.py` (+ `.pyi` stubs).
The Python `FormatType` keeps its current Pythonic API; the proto
classes appear alongside as the wire-level contract.

### JSON via Moshi (Kotlin) / `protobuf.json_format` (Python)

Both runtimes can serialise/deserialise the same `FormatCatalog`
binary or JSON, so a single fixture file works for both Wire and
JSON tests.

## SqlType numbering

`java.sql.Types` mixes positive and negative ints; proto3 enum
numbers must be non-negative. We use `ST_*` ordinals (1, 2, 3, …) and
keep the JDBC int in a `java.sql.Types` lookup table (`SqlTypes` enum
on both sides). The mapping is documented inline in `types.proto`.

## Coverage assertion

`tests/test_format_type_coverage.py` asserts every `HtmlInputType` and
`ComfyType` enum value (Python) shows up in at least one
`FormatType` row. That's the contract: every input the bridge can
produce has somewhere to land.
