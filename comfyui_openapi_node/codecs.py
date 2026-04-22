"""Content-type negotiation: serialize request / deserialize response.

MVP codecs (all stdlib-only by default):
  - application/json                  (json)
  - application/x-www-form-urlencoded (urllib.parse)
  - application/xml, text/xml         (xml.etree)
  - application/octet-stream          (pass-through bytes)
  - text/plain                        (pass-through str)

Opt-in codecs (imported lazily; missing pkg raises on use):
  - application/x-msgpack             (msgpack)
  - application/x-protobuf            (protobuf, needs a compiled message class)

The executor picks a codec by matching Content-Type against the keys;
wildcards like `*/json` match any suffix. Unknown types fall back to
bytes in and string out with a warning in the Response.headers dict.
"""
from __future__ import annotations

import json
import urllib.parse
from typing import Any, Callable


class Codec:
    name: str
    media: tuple[str, ...] = ()

    def encode(self, value: Any) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> Any:
        raise NotImplementedError


class JSONCodec(Codec):
    name = "json"
    media = ("application/json", "text/json", "+json")

    def encode(self, value):
        if isinstance(value, (bytes, str)):
            # Accept pre-serialized JSON too.
            return value.encode() if isinstance(value, str) else value
        return json.dumps(value, separators=(",", ":")).encode()

    def decode(self, data):
        return json.loads(data.decode("utf-8")) if data else None


class FormCodec(Codec):
    name = "form"
    media = ("application/x-www-form-urlencoded",)

    def encode(self, value):
        if isinstance(value, (bytes, str)):
            return value.encode() if isinstance(value, str) else value
        return urllib.parse.urlencode(value, doseq=True).encode()

    def decode(self, data):
        return dict(urllib.parse.parse_qsl(data.decode("utf-8")))


class XMLCodec(Codec):
    name = "xml"
    media = ("application/xml", "text/xml", "+xml")

    def encode(self, value):
        from xml.etree import ElementTree as ET
        if isinstance(value, (bytes, str)):
            return value.encode() if isinstance(value, str) else value
        if isinstance(value, ET.Element):
            return ET.tostring(value, encoding="utf-8")
        # dict → <root>...</root> — shallow best-effort
        root = ET.Element("root")
        for k, v in (value or {}).items():
            child = ET.SubElement(root, str(k))
            child.text = str(v)
        return ET.tostring(root, encoding="utf-8")

    def decode(self, data):
        from xml.etree import ElementTree as ET
        return ET.fromstring(data) if data else None


class BinaryCodec(Codec):
    name = "binary"
    media = ("application/octet-stream",)

    def encode(self, value):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            return value.encode()
        raise TypeError(f"binary codec needs bytes/str, got {type(value).__name__}")

    def decode(self, data):
        return data or b""


class TextCodec(Codec):
    name = "text"
    media = ("text/plain", "text/")

    def encode(self, value):
        return str(value).encode() if not isinstance(value, bytes) else value

    def decode(self, data):
        return data.decode("utf-8", errors="replace") if data else ""


class MessagePackCodec(Codec):
    name = "msgpack"
    media = ("application/x-msgpack", "application/msgpack", "+msgpack")

    def _mod(self):
        import msgpack  # type: ignore
        return msgpack

    def encode(self, value):
        if isinstance(value, bytes):
            return value
        return self._mod().packb(value, use_bin_type=True)

    def decode(self, data):
        return self._mod().unpackb(data, raw=False) if data else None


class ProtobufCodec(Codec):
    """Requires a pre-imported generated message class passed via
    ctx['protobuf_message_class']. Without it, raises on first use."""
    name = "protobuf"
    media = ("application/x-protobuf", "application/protobuf", "+proto")

    def encode(self, value, ctx=None):  # noqa: D401
        msg_cls = (ctx or {}).get("protobuf_message_class")
        if msg_cls is None:
            raise RuntimeError(
                "Protobuf codec needs a generated message class — pass "
                "ctx={'protobuf_message_class': YourMessage}."
            )
        if isinstance(value, msg_cls):
            return value.SerializeToString()
        msg = msg_cls(**(value if isinstance(value, dict) else {}))
        return msg.SerializeToString()

    def decode(self, data, ctx=None):
        msg_cls = (ctx or {}).get("protobuf_message_class")
        if msg_cls is None:
            raise RuntimeError(
                "Protobuf codec needs a generated message class — pass "
                "ctx={'protobuf_message_class': YourMessage}."
            )
        m = msg_cls()
        m.ParseFromString(data or b"")
        return m


_REGISTRY: list[Codec] = [
    JSONCodec(),
    FormCodec(),
    XMLCodec(),
    MessagePackCodec(),
    ProtobufCodec(),
    BinaryCodec(),
    TextCodec(),
]


def pick(content_type: str) -> Codec:
    if not content_type:
        return JSONCodec()
    ct = content_type.split(";", 1)[0].strip().lower()
    for c in _REGISTRY:
        for m in c.media:
            if m.startswith("+"):
                if ct.endswith(m):
                    return c
            elif m.endswith("/"):
                if ct.startswith(m):
                    return c
            else:
                if ct == m:
                    return c
    return BinaryCodec()
