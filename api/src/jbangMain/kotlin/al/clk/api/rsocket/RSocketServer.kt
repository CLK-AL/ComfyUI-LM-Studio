package al.clk.api

// RSocket handler, consumed by api/api.mock.jbang.kt via //SOURCES.
// Skeleton — deps resolve; a real responder is a follow-up using
// RSocketRequestHandler from rsocket-kotlin.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int

private val rsocketLog = org.slf4j.LoggerFactory.getLogger("rsocket")

class RSocketGroup : CliktCommand(name = "rsocket") {
    override fun help(context: Context) = "RSocket mock subcommands."
    override fun run() = Unit
}

class RSocketServe : CliktCommand(name = "serve") {
    override fun help(context: Context) = "RSocket skeleton server (deps resolved)."
    val port by option("-p", "--port").int().default(8094)
    val host by option("--host").default("127.0.0.1")

    override fun run() {
        rsocketLog.info("rsocket skeleton ready on ws://{}:{}/rsocket", host, port)
        println("RSocket skeleton ready on $host:$port (deps resolved via jbang).")
    }
}
