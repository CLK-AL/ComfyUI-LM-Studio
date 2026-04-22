///usr/bin/env jbang "$0" "$@" ; exit $?
//KOTLIN 2.3.20
//JAVA 25
//RUNTIME_OPTIONS -Xmx256m
//DEPS org.wiremock:wiremock:3.9.1
//DEPS com.github.ajalt.clikt:clikt-jvm:5.0.3
//DEPS io.swagger.parser.v3:swagger-parser:2.1.22
//DEPS org.slf4j:slf4j-simple:2.0.13
//NATIVE_OPTIONS --no-fallback
//NATIVE_OPTIONS --enable-url-protocols=http,https
//NATIVE_OPTIONS -H:+UnlockExperimentalVMOptions
//NATIVE_OPTIONS -H:IncludeResources=.*\\.(yaml|json)

// Embedded WireMock seeded from the LM Studio official OpenAPI document.
// No Docker required. Runs on GraalVM 25 via jbang; can be compiled to a
// native image with:  jbang --native tests/lm-studio.wiremock.jbang.kt
//
// Usage:
//   jbang tests/lm-studio.wiremock.jbang.kt start
//   jbang tests/lm-studio.wiremock.jbang.kt start --spec tests/lms-openapi.yaml
//   jbang tests/lm-studio.wiremock.jbang.kt start --port 8089 --host 127.0.0.1

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.core.main
import com.github.ajalt.clikt.core.subcommands
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

private const val DEFAULT_SPEC =
    "https://lmstudio.ai/docs/openapi.yaml" // LM Studio official OpenAPI

class Root : CliktCommand(name = "wiremock-lms") {
    override fun run() = Unit
}

class Start : CliktCommand(name = "start") {
    override fun help(context: Context) =
        "Start embedded WireMock seeded from the LM Studio OpenAPI."

    private val port by option("-p", "--port").int().default(8089)
    private val host by option("--host").default("127.0.0.1")
    private val spec by option(
        "--spec",
        help = "URL or file path to LM Studio OpenAPI (default: $DEFAULT_SPEC)"
    ).default(DEFAULT_SPEC)
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

        val stubbed = seed(server, api)

        Runtime.getRuntime().addShutdownHook(Thread {
            if (verbose) println("Stopping WireMock…")
            server.stop()
        })

        println("WireMock listening on http://$host:$port  ($stubbed stubs from $spec)")
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

fun main(args: Array<String>) = Root().subcommands(Start()).main(args)
