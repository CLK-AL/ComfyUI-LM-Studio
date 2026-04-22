"""Prove AsyncAPI rides the same pipeline as OpenAPI (JSON Schema pivot).

No live WS server is required — these tests just inspect the classes
the registry auto-generates from api/asyncapi/spec/simple-chat.yaml.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))


def test_simple_chat_preset_registered():
    from al.clk.api import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    sc = [k for k in NODE_CLASS_MAPPINGS if k.startswith("API_simple_chat_")]
    assert sc, f"no simple-chat preset classes registered; have: {list(NODE_CLASS_MAPPINGS)[:6]}…"
    titles = [NODE_DISPLAY_NAME_MAPPINGS[k] for k in sc]
    assert all("simple-chat" in t for t in titles)


def test_send_message_typed_inputs():
    from al.clk.api import NODE_CLASS_MAPPINGS
    cls_name = next(k for k in NODE_CLASS_MAPPINGS
                    if k.endswith("_sendMessage"))
    it = NODE_CLASS_MAPPINGS[cls_name].INPUT_TYPES()
    # `text` is required per the AsyncAPI payload schema.
    assert it["required"]["text"][0] == "STRING"
    # `user` / `ts` are optional.
    assert it["optional"]["user"][0] == "STRING"
    assert it["optional"]["ts"][0]   == "INT"
    # Routing / infra inputs common to all API nodes.
    assert "server_url" in it["optional"]


def test_asyncapi_protocol_hint_is_ws():
    from al.clk.api.to_jsonschema import asyncapi as aas
    import yaml  # pyyaml is pulled in transitively via conftest's bootstrap
    from pathlib import Path as _P
    spec = yaml.safe_load(
        _P("api/asyncapi/spec/simple-chat.yaml").read_text()
    )
    canon = aas.convert(spec)
    # Both ops default to ws (the spec's server is ws:// and the
    # converter annotates each operation with protocol='ws').
    assert all(op["protocol"] == "ws" for op in canon["operations"])
    assert canon["server_url"].startswith("ws://")
