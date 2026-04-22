"""Symbolic contract checks on LMStudioNode.

These don't hit WireMock — they just assert the ComfyUI surface (class
attributes ComfyUI reads via introspection) stays intact. When upstream
renames something, these tests fail with a clear message instead of a
cryptic KeyError downstream.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))


@pytest.fixture
def Node():
    from node import LMStudioNode
    return LMStudioNode


def test_comfyui_class_mappings_present():
    import node as mod
    assert hasattr(mod, "NODE_CLASS_MAPPINGS")
    assert hasattr(mod, "NODE_DISPLAY_NAME_MAPPINGS")
    assert "LMStudioNode" in mod.NODE_CLASS_MAPPINGS
    assert mod.NODE_CLASS_MAPPINGS["LMStudioNode"].__name__ == "LMStudioNode"


def test_comfyui_class_attrs(Node):
    # ComfyUI looks for these exact names on the class.
    for attr in ("RETURN_TYPES", "RETURN_NAMES", "FUNCTION", "CATEGORY"):
        assert hasattr(Node, attr), f"missing class attr {attr!r}"
    assert isinstance(Node.RETURN_TYPES, tuple)
    assert isinstance(Node.RETURN_NAMES, tuple)
    # Arity can grow (e.g. upstream PR#1 adds available_models) but never
    # shrink below (response, stats).
    assert len(Node.RETURN_TYPES) >= 2
    assert Node.RETURN_TYPES[:2] == ("STRING", "STRING")
    assert Node.RETURN_NAMES[:2] == ("response", "stats")


def test_function_attr_points_at_callable(Node):
    fn_name = Node.FUNCTION
    fn = getattr(Node, fn_name, None)
    assert callable(fn), f"Node.{fn_name!r} must be callable"


def test_input_types_contract(Node):
    types = Node.INPUT_TYPES()
    assert "required" in types
    required = types["required"]
    # The required keys ComfyUI workflows wire into the node — tests
    # break loudly if any of them is removed or renamed.
    expected_keys = {
        "system_prompt", "user_message", "model_id", "server_address",
        "temperature", "max_tokens", "thinking_tokens", "use_sdk",
    }
    missing = expected_keys - set(required.keys())
    assert not missing, f"required INPUT_TYPES missing: {missing}"
    # Optional bucket: image is the key vision-enablement knob.
    optional = types.get("optional", {})
    assert "image" in optional


def test_get_response_signature_accepts_all_required_kwargs(Node):
    sig = inspect.signature(Node.get_response)
    params = sig.parameters
    for name in (
        "system_prompt", "user_message", "model_id", "server_address",
        "temperature", "max_tokens", "thinking_tokens", "use_sdk",
        "image", "debug",
    ):
        assert name in params, f"get_response is missing parameter {name!r}"
