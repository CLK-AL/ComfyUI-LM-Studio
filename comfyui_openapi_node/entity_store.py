"""SQLite-backed entity store.

One entity (e.g. a JDBC `users` row) lives once in SQLite as a JSON
blob. Each API that talks to it sees only its **projection** — the
subset of properties its JSON Schema declares. Mutations arrive as
RFC 7396 JSON Merge Patches (whole-object or per-property) applied by
SQLite's built-in `json_patch()`, and every property-level change is
written to an append-only audit log that can be fanned out over SSE.

Schema of the store (two tables, JSON1 throughout):

    CREATE TABLE entities (
        type        TEXT NOT NULL,
        id          TEXT NOT NULL,
        body        TEXT NOT NULL CHECK (json_valid(body)),
        version     INTEGER NOT NULL DEFAULT 1,
        updated_at  TEXT NOT NULL,
        PRIMARY KEY (type, id)
    );

    CREATE TABLE audit (
        audit_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        type       TEXT NOT NULL,
        id         TEXT NOT NULL,
        ts         TEXT NOT NULL,
        op         TEXT NOT NULL,     -- replace | add | remove | put
        path       TEXT NOT NULL,     -- RFC 6901 JSON pointer ('' = root)
        old_value  TEXT,              -- JSON
        new_value  TEXT,              -- JSON
        api        TEXT                -- optional "<kind>/<api>" tag
    );

Public API:
    EntityStore.open(path=None)
    store.put(type, id, body, *, api=None)           -- full replace
    store.patch(type, id, patch_dict, *, api=None)   -- RFC 7396 merge
    store.get(type, id)
    store.project(type, id, schema)                  -- filter to schema's props
    store.audit_since(audit_id=0)                    -> iterator[AuditEvent]
    store.sse_stream(since=0)                        -> iterator[str] (SSE frames)
    store.subscribe()                                -> Subscriber (push-style)
"""
from __future__ import annotations

import json
import os
import queue
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

from .schema_patch import diff, apply_patch


DEFAULT_ENV = "COMFYUI_ENTITY_STORE"


@dataclass(frozen=True)
class AuditEvent:
    audit_id: int
    type: str
    id: str
    ts: str
    op: str
    path: str
    old_value: Any
    new_value: Any
    api: str | None

    def to_sse(self) -> str:
        payload = {
            "type": self.type, "id": self.id,
            "op": self.op, "path": self.path,
            "old": self.old_value, "new": self.new_value,
            "api": self.api, "ts": self.ts,
        }
        return (
            f"id: {self.audit_id}\n"
            f"event: entity.{self.op}\n"
            f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        )


def _default_path() -> Path:
    env = os.environ.get(DEFAULT_ENV)
    if env:
        return Path(env)
    cache = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(cache) / "comfyui_openapi_node" / "entities.db"


class EntityStore:
    _DDL = (
        "CREATE TABLE IF NOT EXISTS entities ("
        "  type        TEXT NOT NULL,"
        "  id          TEXT NOT NULL,"
        "  body        TEXT NOT NULL CHECK (json_valid(body)),"
        "  version     INTEGER NOT NULL DEFAULT 1,"
        "  updated_at  TEXT NOT NULL,"
        "  PRIMARY KEY (type, id)"
        ");",
        "CREATE TABLE IF NOT EXISTS audit ("
        "  audit_id   INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  type       TEXT NOT NULL,"
        "  id         TEXT NOT NULL,"
        "  ts         TEXT NOT NULL,"
        "  op         TEXT NOT NULL,"
        "  path       TEXT NOT NULL,"
        "  old_value  TEXT,"
        "  new_value  TEXT,"
        "  api        TEXT"
        ");",
        "CREATE INDEX IF NOT EXISTS audit_by_entity ON audit(type, id, audit_id);",
    )

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._lock = threading.RLock()
        self._subscribers: list[queue.Queue] = []
        for stmt in self._DDL:
            conn.execute(stmt)
        conn.commit()

    @classmethod
    def open(cls, path: str | Path | None = None) -> "EntityStore":
        p = Path(path) if path else _default_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        return cls(sqlite3.connect(str(p), check_same_thread=False))

    def close(self) -> None:
        self._conn.close()

    # --- helpers --------------------------------------------------------
    @staticmethod
    def _now() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S.", time.gmtime()) + \
               f"{int((time.time() % 1) * 1000):03d}Z"

    def _log_event(self, type_: str, id_: str, op: str, path: str,
                   old: Any, new: Any, api: str | None) -> AuditEvent:
        ts = self._now()
        cur = self._conn.execute(
            "INSERT INTO audit (type, id, ts, op, path, old_value, new_value, api)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                type_, id_, ts, op, path,
                None if old is None else json.dumps(old, ensure_ascii=False),
                None if new is None else json.dumps(new, ensure_ascii=False),
                api,
            ),
        )
        ev = AuditEvent(
            audit_id=cur.lastrowid, type=type_, id=id_, ts=ts,
            op=op, path=path, old_value=old, new_value=new, api=api,
        )
        self._notify(ev)
        return ev

    def _notify(self, ev: AuditEvent) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(ev)
            except queue.Full:
                pass  # slow subscriber — drop

    # --- put / get / patch ---------------------------------------------
    def put(self, type_: str, id_: str, body: Mapping[str, Any],
            *, api: str | None = None) -> AuditEvent:
        """Full-replace the entity. Logs a single 'put' audit event
        carrying the entire old + new body (so downstream consumers
        can compute their own diffs if they want)."""
        with self._lock:
            old = self.get(type_, id_)
            new_json = json.dumps(dict(body), ensure_ascii=False)
            now = self._now()
            self._conn.execute(
                "INSERT OR REPLACE INTO entities (type, id, body, version, updated_at)"
                " VALUES (?, ?, ?, COALESCE("
                "  (SELECT version + 1 FROM entities WHERE type=? AND id=?), 1), ?)",
                (type_, id_, new_json, type_, id_, now),
            )
            ev = self._log_event(type_, id_, "put", "",
                                 old, dict(body), api)
            self._conn.commit()
            return ev

    def get(self, type_: str, id_: str) -> dict | None:
        row = self._conn.execute(
            "SELECT body FROM entities WHERE type=? AND id=?",
            (type_, id_),
        ).fetchone()
        return json.loads(row[0]) if row else None

    def patch(self, type_: str, id_: str, patch: Mapping[str, Any],
              *, api: str | None = None) -> list[AuditEvent]:
        """Apply an RFC 7396 JSON Merge Patch using SQLite's
        `json_patch` and log one audit row per property change."""
        with self._lock:
            old = self.get(type_, id_) or {}
            (merged_json,) = self._conn.execute(
                "SELECT json_patch(?, ?)",
                (json.dumps(old, ensure_ascii=False),
                 json.dumps(dict(patch), ensure_ascii=False)),
            ).fetchone()
            new = json.loads(merged_json) if merged_json else {}
            # Write the merged body.
            if self.get(type_, id_) is None:
                self._conn.execute(
                    "INSERT INTO entities (type, id, body, version, updated_at)"
                    " VALUES (?, ?, ?, 1, ?)",
                    (type_, id_, merged_json, self._now()),
                )
            else:
                self._conn.execute(
                    "UPDATE entities SET body=?, version=version+1, updated_at=?"
                    " WHERE type=? AND id=?",
                    (merged_json, self._now(), type_, id_),
                )
            # Property-level audit via our own `diff()` on the old→new bodies.
            events: list[AuditEvent] = []
            for op in diff(old, new):
                ev = self._log_event(
                    type_, id_, op["op"], op["path"],
                    _try_get(old, op["path"]),
                    op.get("value"),
                    api,
                )
                events.append(ev)
            self._conn.commit()
            return events

    # --- projection -----------------------------------------------------
    def project(self, type_: str, id_: str, schema: Mapping) -> dict | None:
        """Return a view containing only the properties the schema
        declares. Top-level `properties` of an `object` schema is
        honored; anything else returns the full body."""
        body = self.get(type_, id_)
        if body is None:
            return None
        if (schema.get("type") or "object") != "object":
            return body
        props = schema.get("properties") or {}
        if not props:
            return body
        return {k: body[k] for k in props if k in body}

    # --- audit + SSE ----------------------------------------------------
    def audit_since(self, audit_id: int = 0, *,
                    type_: str | None = None,
                    id_: str | None = None) -> Iterator[AuditEvent]:
        q = ("SELECT audit_id, type, id, ts, op, path, old_value, new_value, api "
             "FROM audit WHERE audit_id > ?")
        params: list = [audit_id]
        if type_ is not None:
            q += " AND type = ?"; params.append(type_)
        if id_ is not None:
            q += " AND id = ?";   params.append(id_)
        q += " ORDER BY audit_id"
        for row in self._conn.execute(q, params).fetchall():
            aid, t, i, ts, op, path, old_j, new_j, api = row
            yield AuditEvent(
                audit_id=aid, type=t, id=i, ts=ts, op=op, path=path,
                old_value=json.loads(old_j) if old_j is not None else None,
                new_value=json.loads(new_j) if new_j is not None else None,
                api=api,
            )

    def sse_stream(self, since: int = 0) -> Iterator[str]:
        """Replay audit as SSE frames."""
        for ev in self.audit_since(since):
            yield ev.to_sse()

    def subscribe(self, max_queued: int = 1024) -> "Subscriber":
        q: queue.Queue = queue.Queue(maxsize=max_queued)
        self._subscribers.append(q)
        return Subscriber(self, q)


class Subscriber:
    """Push-style subscriber for real-time SSE fan-out. Wrap with
    your server's streaming response handler (Flask / Ktor SSE /
    asyncio queue)."""
    def __init__(self, store: EntityStore, q: queue.Queue):
        self._store = store
        self._q = q

    def next(self, timeout: float | None = None) -> AuditEvent | None:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self) -> None:
        try:
            self._store._subscribers.remove(self._q)
        except ValueError:
            pass


def _try_get(doc: Any, pointer: str) -> Any:
    """Read the old value at a JSON pointer; return None on miss."""
    if not pointer:
        return doc
    try:
        from .schema_patch import _split_pointer, _get_by_pointer
        return _get_by_pointer(doc, _split_pointer(pointer))
    except Exception:  # noqa: BLE001
        return None
