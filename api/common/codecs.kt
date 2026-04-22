// Shared content-negotiation codecs used by every /api/*/* handler.
// Pulled in with //SOURCES ../common/codecs.kt from sibling jbang scripts.
//
// Covers: JSON, CBOR, Protobuf (via kotlinx.serialization), XML
// (xmlutil), MessagePack (msgpack-core), plain text, and
// application/octet-stream pass-through.

import kotlinx.serialization.cbor.Cbor
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.protobuf.ProtoBuf
import nl.adaptivity.xmlutil.serialization.XML
import org.msgpack.core.MessagePack

object Codecs {
    val json:  Json   = Json { ignoreUnknownKeys = true; prettyPrint = false }
    val cbor:  Cbor   = Cbor { ignoreUnknownKeys = true }
    val proto: ProtoBuf = ProtoBuf {}
    val xml:   XML    = XML {}

    fun decodeJson(bytes: ByteArray): JsonElement =
        json.parseToJsonElement(bytes.decodeToString())

    fun encodeJson(element: JsonElement): ByteArray =
        json.encodeToString(JsonElement.serializer(), element).encodeToByteArray()

    fun decodeCbor(bytes: ByteArray): JsonElement {
        // CBOR → kotlinx anywhere the type isn't statically known falls
        // back to hex inspection; callers that know the @Serializable
        // class should use cbor.decodeFromByteArray(serializer, bytes).
        return json.parseToJsonElement(
            "\"cbor[${bytes.size}B]=${bytes.joinToString("") { "%02x".format(it) }}\""
        )
    }

    fun decodeMsgpack(bytes: ByteArray): JsonElement {
        MessagePack.newDefaultUnpacker(bytes).use { unp ->
            // Walk the top-level value and stringify — generic decoder
            // for the echo server; real consumers supply a schema.
            val v = unp.unpackValue()
            return json.parseToJsonElement("\"msgpack:${v}\"")
        }
    }

    fun picKotlinx(contentType: String): String = when {
        contentType.contains("json")      -> "json"
        contentType.contains("cbor")      -> "cbor"
        contentType.contains("protobuf")  -> "protobuf"
        contentType.contains("xml")       -> "xml"
        contentType.contains("msgpack")   -> "msgpack"
        contentType.startsWith("text/")   -> "text"
        else                              -> "bytes"
    }
}
