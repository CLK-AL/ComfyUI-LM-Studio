// AsyncAPI Ktor handler, consumed by api/api.mock.jbang.kt via //SOURCES.

import com.github.ajalt.clikt.core.CliktCommand
import com.github.ajalt.clikt.core.Context
import com.github.ajalt.clikt.parameters.options.default
import com.github.ajalt.clikt.parameters.options.option
import com.github.ajalt.clikt.parameters.types.int
import io.ktor.serialization.kotlinx.json.json
import io.ktor.server.application.install
import io.ktor.server.engine.embeddedServer
import io.ktor.server.netty.Netty
import io.ktor.server.plugins.contentnegotiation.ContentNegotiation
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.routing
import io.ktor.server.sse.SSE
import io.ktor.server.sse.sse
import io.ktor.server.websocket.WebSockets
import io.ktor.server.websocket.webSocket
import io.ktor.sse.ServerSentEvent
import io.ktor.websocket.Frame
import io.ktor.websocket.readText
import java.util.concurrent.atomic.AtomicLong
import kotlinx.coroutines.delay

private val asyncLog = org.slf4j.LoggerFactory.getLogger("asyncapi")
private val asyncSeq = AtomicLong(0)

class AsyncApiGroup : CliktCommand(name = "asyncapi") {
    override fun help(context: Context) = "AsyncAPI / Ktor WS+SSE subcommands."
    override fun run() = Unit
}

class AsyncApiEcho : CliktCommand(name = "echo") {
    override fun help(context: Context) = "Echo server for WS / SSE (no spec)."
    val port by option("-p", "--port").int().default(8090)
    val host by option("--host").default("127.0.0.1")

    override fun run() {
        asyncLog.info("asyncapi echo on ws://{}:{}", host, port)
        embeddedServer(Netty, host = host, port = port) {
            install(WebSockets)
            install(SSE)
            install(ContentNegotiation) { json() }
            routing {
                webSocket("/ws/{channel...}") {
                    for (frame in incoming) {
                        if (frame is Frame.Text) {
                            val txt = frame.readText()
                            asyncLog.info("ws recv: {}", txt)
                            send(Frame.Text(txt))
                        }
                    }
                }
                sse("/sse/{channel...}") {
                    repeat(3) { i ->
                        val id = asyncSeq.incrementAndGet().toString()
                        val payload = """{"id":"$id","seq":$i}"""
                        send(ServerSentEvent(data = payload, id = id))
                        delay(100)
                    }
                }
                get("/healthz") { call.respondText("ok") }
            }
        }.start(wait = true)
    }
}
