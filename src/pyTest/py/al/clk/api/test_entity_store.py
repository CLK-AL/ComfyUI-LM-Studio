"""One JDBC entity, many API projections, every mutation audited.

The entity stays in SQLite as a single JSON blob. Individual API
files (OpenAPI/AsyncAPI/gql) supply their own JSON Schema projections;
applying `.project()` returns the subset each API cares about. Mutations
arrive as RFC 7396 JSON Merge Patches and are applied in SQL via
json_patch(); property-level audit rows stream out via SSE.
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO / "src" / "pyMain" / "py"))

from al.clk.api.entity_store import EntityStore


_USER = {
    "id": "42",
    "email": "ada@example.com",
    "display": "Ada Lovelace",
    "role": "admin",
    "signup_ts": "2026-01-15T10:00:00Z",
    "pay_info": {"card_last4": "4242", "billing_zip": "10001"},
}

_OPENAPI_PUBLIC = {        # API 1: only the public fields
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "display": {"type": "string"},
        "role": {"type": "string"},
    },
}

_OPENAPI_BILLING = {       # API 2: just the money view
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "pay_info": {"type": "object"},
    },
}


@pytest.fixture
def store(tmp_path):
    return EntityStore.open(tmp_path / "ent.db")


# --- put / get + projections --------------------------------------------
def test_put_and_get_full_body(store):
    store.put("users", "42", _USER)
    assert store.get("users", "42") == _USER


def test_projection_returns_only_schema_properties(store):
    store.put("users", "42", _USER)
    pub = store.project("users", "42", _OPENAPI_PUBLIC)
    assert set(pub) == {"id", "display", "role"}
    assert "email" not in pub and "pay_info" not in pub
    bill = store.project("users", "42", _OPENAPI_BILLING)
    assert set(bill) == {"id", "pay_info"}


def test_projection_handles_missing_entity(store):
    assert store.project("users", "missing", _OPENAPI_PUBLIC) is None


def test_projection_passthrough_for_non_object_schemas(store):
    store.put("users", "42", _USER)
    got = store.project("users", "42", {"type": "string"})
    # Non-object schema → no filtering, body returned verbatim.
    assert got == _USER


# --- patch: RFC 7396 via SQLite json_patch ------------------------------
def test_patch_adds_and_replaces_properties(store):
    store.put("users", "42", _USER)
    store.patch("users", "42",
                {"display": "AL", "new_field": "hello"})
    got = store.get("users", "42")
    assert got["display"] == "AL"
    assert got["new_field"] == "hello"
    # Other fields untouched.
    assert got["email"] == _USER["email"]


def test_patch_with_null_removes_property(store):
    store.put("users", "42", _USER)
    store.patch("users", "42", {"role": None})
    got = store.get("users", "42")
    assert "role" not in got


def test_patch_on_missing_entity_creates_it(store):
    events = store.patch("users", "99", {"email": "new@e"})
    assert store.get("users", "99") == {"email": "new@e"}
    assert any(e.op == "add" for e in events)


# --- audit log ----------------------------------------------------------
def test_put_logs_single_put_event(store):
    ev = store.put("users", "42", _USER, api="openapi/identity")
    assert ev.op == "put" and ev.path == "" and ev.api == "openapi/identity"
    assert ev.old_value is None and ev.new_value == _USER


def test_patch_logs_one_event_per_property_change(store):
    store.put("users", "42", _USER)
    evs = store.patch("users", "42",
                      {"display": "AL", "role": None, "tier": "pro"},
                      api="openapi/identity")
    by_path = {e.path: e for e in evs}
    assert by_path["/display"].op == "replace"
    assert by_path["/display"].old_value == "Ada Lovelace"
    assert by_path["/display"].new_value == "AL"
    assert by_path["/role"].op == "remove"
    assert by_path["/tier"].op == "add"
    assert by_path["/tier"].new_value == "pro"


def test_audit_since_cursor_moves_forward(store):
    store.put("users", "42", _USER)
    first_cursor = list(store.audit_since(0))[-1].audit_id
    store.patch("users", "42", {"email": "c@d"})
    # Only the patch event(s) after the cursor.
    after = list(store.audit_since(first_cursor))
    assert after and all(a.audit_id > first_cursor for a in after)
    assert all(a.path == "/email" for a in after)


# --- SSE fan-out --------------------------------------------------------
def test_sse_stream_serialises_expected_frames(store):
    store.put("users", "42", _USER, api="openapi/identity")
    frames = list(store.sse_stream(since=0))
    joined = "\n".join(frames)
    # One frame per audit row; frames have id / event / data lines.
    assert "event: entity.put" in joined
    assert "data: " in joined
    # The id: <audit_id> + event: + data: + blank-line terminator.
    assert frames[0].endswith("\n\n")


def test_subscriber_pushes_new_events_realtime(store):
    sub = store.subscribe()
    store.put("users", "1", {"x": 1}, api="a")
    store.patch("users", "1", {"x": 2}, api="a")
    got = []
    for _ in range(3):
        ev = sub.next(timeout=0.2)
        if ev is None:
            break
        got.append(ev)
    sub.close()
    # Put (1) + per-property patch (1) = at least 2 events.
    ops = [e.op for e in got]
    assert "put" in ops
    assert any(o in ops for o in ("replace", "add"))


def test_multiple_subscribers_receive_same_events(store):
    s1 = store.subscribe()
    s2 = store.subscribe()
    store.put("users", "x", {"a": 1})
    e1 = s1.next(timeout=0.2)
    e2 = s2.next(timeout=0.2)
    assert e1 is not None and e2 is not None
    assert e1.audit_id == e2.audit_id
    s1.close(); s2.close()


# --- projection × patch: only the fields an API cares about mutate ------
def test_api_scoped_patch_surfaces_in_its_projection_only(store):
    store.put("users", "42", _USER)
    # Billing API patches pay_info — the public API's projection doesn't
    # change, but its audit stream still sees the event (governance).
    store.patch("users", "42",
                {"pay_info": {"card_last4": "0007"}},
                api="openapi/billing")
    public = store.project("users", "42", _OPENAPI_PUBLIC)
    billing = store.project("users", "42", _OPENAPI_BILLING)
    assert public == {
        "id": "42", "display": "Ada Lovelace", "role": "admin",
    }
    assert billing["pay_info"]["card_last4"] == "0007"
    # audit trail tagged with the api that caused the change
    evs = list(store.audit_since(0))
    billing_evs = [e for e in evs if e.api == "openapi/billing"]
    assert billing_evs and all(e.path.startswith("/pay_info") for e in billing_evs)
