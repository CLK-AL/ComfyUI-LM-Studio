package al.clk.api

// OpenAPI WireMock handler, consumed by api/api.mock.jbang.kt via //SOURCES.
// No jbang header here — deps come from the entry point.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.flag
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int
import com.github.tomakehurst.wiremock.WireMockServer
import com.github.tomakehurst.wiremock.client.WireMock.okJson
import com.github.tomakehurst.wiremock.client.WireMock.request
import com.github.tomakehurst.wiremock.client.WireMock.urlPathEqualTo
import com.github.tomakehurst.wiremock.core.WireMockConfiguration.options
import io.swagger.v3.oas.models.OpenAPI
import io.swagger.v3.parser.OpenAPIV3Parser

private const val DEFAULT_OPENAPI_SPEC = "https://lmstudio.ai/docs/openapi.yaml"

class OpenApiGroup : CliktCommand(name = "openapi") {
    override fun help(context: Context) = "OpenAPI / WireMock subcommands."
    override fun run() = Unit
}

class OpenApiStart : CliktCommand(name = "start") {
    override fun help(context: Context) =
        "Start embedded WireMock seeded from an OpenAPI document."

    private val port by option("-p", "--port").int().default(8089)
    private val host by option("--host").default("127.0.0.1")
    private val spec by option(
        "--spec",
        help = "URL or path to the OpenAPI document (default: $DEFAULT_OPENAPI_SPEC)"
    ).default(DEFAULT_OPENAPI_SPEC)
    private val verbose by option("-v", "--verbose").flag()

    override fun run() {
        val api = OpenAPIV3Parser().read(spec)
            ?: error("Could not parse OpenAPI spec at: $spec")
        val server = WireMockServer(
            options().bindAddress(host).port(port).notifier(
                com.github.tomakehurst.wiremock.common.ConsoleNotifier(verbose)
            )
        )
        server.start()
        val count = seed(server, api)
        Runtime.getRuntime().addShutdownHook(Thread {
            if (verbose) println("Stopping WireMock…")
            server.stop()
        })
        println("WireMock listening on http://$host:$port ($count stubs from $spec)")
        Thread.currentThread().join()
    }

    private fun seed(server: WireMockServer, api: OpenAPI): Int {
        var count = 0
        api.paths.orEmpty().forEach { (path, item) ->
            item.readOperationsMap().forEach { (method, op) ->
                val body = op.responses
                    ?.entries
                    ?.firstOrNull { it.key.startsWith("2") }
                    ?.value
                    ?.content
                    ?.get("application/json")
                    ?.example
                    ?.toString()
                    ?: """{"stubbed": true, "path": "$path"}"""
                server.stubFor(
                    request(method.name, urlPathEqualTo(path))
                        .willReturn(okJson(body))
                )
                count++
            }
        }
        return count
    }
}
