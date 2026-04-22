package al.clk.api

// Clikt root + subcommand wiring for the api-mock process. Lives
// under `common/` so the same tree compiles into a KMP Compose
// Multiplatform module (Clikt 5.x has commonMain publications); the
// jbang entry at `api/api.mock.jbang.kt` is a thin shell that just
// declares the //DEPS / //SOURCES set and hands args to `apiMockMain`.
//
// The subcommand classes themselves live in the protocol folders —
// `openapi/Wiremock.kt`, `asyncapi/AsyncApiServer.kt`,
// `mcp/McpServer.kt`, `rsocket/RSocketServer.kt`, `jdbc/JdbcServer.kt`
// — and carry their own JVM-only deps (WireMock, Ktor, Spring JDBC,
// Jackson, …). This file stays KMP-portable at the wiring level: any
// downstream KMP target can swap the `SubcommandSet` implementation
// for a platform-specific one without retouching the root.
//
// Subcommand tree:
//   openapi  start — WireMock from an OpenAPI document
//   asyncapi echo  — Ktor WS + SSE echo server
//   mcp      serve — JSON-RPC MCP mock over SSE
//   rsocket  serve — RSocket (skeleton)
//   jdbc     serve — EntityStore over a SQLite / Postgres pool
//
// Each subcommand defaults to its own port so they can run side by
// side: openapi 8089, asyncapi 8090, mcp 8091, rsocket 8094.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.main
import com.github.ajalt.clikt.core.subcommands
import io.github.cdimascio.dotenv.dotenv

/** Root of the api-mock Clikt tree. */
class APIMock : CliktCommand(name = "api-mock") {
    override fun run() = Unit
}

/** Load `api.env` if present (shared with the Python side's
 *  `python-dotenv` call in conftest.py). Values are pushed into the
 *  JVM system properties so downstream code can `System.getenv` /
 *  `System.getProperty` without direct dotenv coupling. Safe to call
 *  multiple times — `ignoreIfMissing` keeps us quiet when the file
 *  isn't there. */
fun loadApiEnv() {
    val env = dotenv {
        ignoreIfMissing = true
        ignoreIfMalformed = true
        filename = "api.env"
        // Walk up until we find it so `jbang run …` from any subdir works.
        directory = System.getProperty("user.dir")
    }
    env.entries().forEach { e ->
        if (System.getenv(e.key) == null)
            System.setProperty(e.key, e.value)
    }
}

/** Assemble the full subcommand tree. Factored out so KMP targets
 *  can plug in platform-specific groups (e.g. a Compose-UI runner
 *  that opens a dashboard instead of a Netty port). */
fun buildApiMockTree(): APIMock = APIMock().subcommands(
    OpenApiGroup().subcommands(OpenApiStart()),
    AsyncApiGroup().subcommands(AsyncApiEcho()),
    McpGroup().subcommands(McpServe()),
    RSocketGroup().subcommands(RSocketServe()),
    JdbcGroup().subcommands(JdbcServe()),
)

/** Canonical entry point — called both from the jbang shell and
 *  from any KMP host that wants to reuse the same CLI surface. */
fun apiMockMain(args: Array<String>) {
    loadApiEnv()
    buildApiMockTree().main(args)
}
