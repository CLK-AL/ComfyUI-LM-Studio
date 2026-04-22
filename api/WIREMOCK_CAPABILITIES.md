# WireMock surface coverage (2026-04)

Notes compiled while choosing Kotlin mocks for each protocol subfolder.
If an entry is in the "covered" column, we can seed stubs from a spec
file in `/api/<kind>/spec/` and the jbang facade will honor them.

## Out of the box (WireMock 3.x standalone)

| Protocol / feature     | Coverage | Notes                                                         |
| ---------------------- | -------- | ------------------------------------------------------------- |
| HTTP / HTTPS (REST)    | **full** | Status / body / headers / URL & body matching / templating     |
| WebDAV verbs           | **full** | PROPFIND, MKCOL, COPY, MOVE, etc. — any custom method accepted |
| Request journal        | **full** | `GET /__admin/requests` — what we use for coverage reporting   |
| Stateful scenarios     | **full** | `Scenario.STARTED` → state machine across requests             |
| Request matching       | **full** | `equalToJson` / `matchingJsonPath` / `matchingXPath` /
                          regex                                                           |
| Response templating    | **full** | Handlebars in body/headers (request echo, randoms, UUIDs)      |
| Multipart form-data    | **full** | Match on form parts; binary echo works                         |
| Proxying + record      | **full** | `proxyAllTo` + `record` → capture real traffic as mappings      |
| Fault injection        | **full** | delays, MALFORMED_RESPONSE_CHUNK, CONNECTION_RESET_BY_PEER     |
| HTTP/2 + TLS           | **full** | ALPN on by default in 3.x                                       |
| OpenAPI spec loading   | partial  | **not native** — we parse the spec in Kotlin (`swagger-parser`) and programmatically stub each path. That's the job of `/api/api.mock.jbang.kt (openapi start)`. |
| SSE (text/event-stream)| partial  | Works as a plain HTTP stream when the stub response is a long body — but no first-class `event:` / `data:` framing helpers. Usually we write a small chunked handler. |

## Extensions (separate jars / repos)

| Protocol | Extension                                              | Status         |
| -------- | ------------------------------------------------------ | -------------- |
| gRPC     | [`wiremock-grpc-extension`](https://github.com/wiremock/wiremock-grpc-extension) | **solid** — stubs `.proto` services, handles unary + server-streaming; protobuf wire format is first-class. |
| GraphQL  | No dedicated extension                                  | Use REST stubs: match on JSON body path `$.query`, respond with fixtures. |
| WebSocket| [`wiremock-extension-websocket`](https://github.com/wiremock/wiremock-extension-websocket) | **beta** — declarative send/receive scripts; auth through headers; good enough for LM-Studio-style streaming. |
| MCP      | None                                                    | MCP speaks JSON-RPC over stdio/SSE/HTTP. SSE transport: WireMock HTTP stub with chunked body works. stdio transport: use the Kotlin MCP SDK directly, not WireMock. |
| RSocket  | None                                                    | Binary framed protocol — need `rsocket-kotlin` as a standalone responder. |
| AsyncAPI | No dedicated extension                                  | Each AsyncAPI binding maps to a WireMock-addressable protocol above: `ws` → websocket extension; `http` → core; `kafka`/`amqp` → dedicated testcontainers/brokers. |

## What this means for `/api/<kind>/*.jbang.kt`

- **openapi/** — 100% WireMock with programmatic stubs seeded from the
  spec (already done).
- **asyncapi/** — WireMock only if the binding is `ws` or `sse`; else
  drop to Ktor websocket or a broker client. Current skeleton uses
  Ktor server directly, which is the clean path.
- **grpc/** — Either `wiremock-grpc-extension` *or* `grpc-kotlin`
  server. The skeleton picks grpc-kotlin because we want dynamic
  descriptor loading; the extension assumes compile-time protos.
- **rsocket/** — Ktor + `rsocket-kotlin`. No WireMock path.
- **mcp/** — Kotlin MCP SDK over whichever transport the test wants
  (SSE is easiest through Ktor).

## Summary

WireMock is the right hammer for OpenAPI + SSE(HTTP chunked) + WebDAV +
GraphQL-as-REST. For gRPC we'll want either the WireMock extension or a
standalone grpc-kotlin responder. RSocket needs its own thing. MCP is
covered by the official Kotlin SDK.
