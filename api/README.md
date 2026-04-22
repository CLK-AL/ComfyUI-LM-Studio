# /api — protocol mocks & spec bodies

This directory is the Kotlin side of the project: one subfolder per API
kind, each carrying (a) its spec bodies for presets and (b) a jbang
Kotlin script that mocks that protocol. The Python `comfyui_openapi_node`
package consumes the same spec files as its first source of truth.

| Folder        | Status       | Stack                                           |
| ------------- | ------------ | ----------------------------------------------- |
| `openapi/`    | **working**  | WireMock 3 + Clikt; spec driven by swagger-parser |
| `asyncapi/`   | skeleton     | Ktor server (SSE + WebSocket)                   |
| `mcp/`        | skeleton     | **Kotlin MCP SDK** (`io.modelcontextprotocol:kotlin-sdk`) |
| `grpc/`       | skeleton     | grpc-kotlin + kotlinx.serialization.protobuf    |
| `rsocket/`    | skeleton     | rsocket-kotlin + kotlinx.serialization          |
| `common/`     | shared utils | kotlinx codecs (json/cbor/protobuf/xml/msgpack) |

Each folder's script is self-contained and jbang-runnable; you don't
need a Gradle build. The top-level dispatcher is `api/server.jbang.kt`
(TBD) which will mount all protocols under one Ktor Netty process.

Dependencies common to several scripts are pinned together:
- Ktor 3.0.3 (server-core, netty, content-negotiation, websockets, sse)
- kotlinx.serialization 1.7.3 (json / cbor / protobuf)
- xmlutil 0.90.3 (xml)
- msgpack-core 0.9.8
- Kotlin 2.3.20, JDK 25 (GraalVM), jbang 0.138.0 — see `.sdkmanrc`.
