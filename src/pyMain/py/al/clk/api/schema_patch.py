"""JSON Patch (RFC 6902 subset) + cross-API schema merging.

Used by the registry to:
  * resolve a `$ref` — either a local JSON Pointer or a
    `registry://<kind>/<api>/<category>/<name>` URI that looks the
    component up in the SQLite-indexed schema tree;
  * compute a **diff** between two JSON-Schema dicts (add / remove /
    replace at any depth);
  * apply one;
  * merge all the similar-named components across APIs into a
    single "union" schema — the thing the registry hands to downstream
    binding/UI code so `User` means one ComfyUI slot regardless of
    which upstream API you picked.

The subset is intentionally small (add / remove / replace — no
test / move / copy) because that covers schema harmonization without
pulling a jsonpatch dependency.
"""
from __future__ import annotations

from typing import Any, Mapping


# ---- JSON Pointer (RFC 6901) -------------------------------------------
def _unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def _escape(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def _split_pointer(ptr: str) -> list[str]:
    if ptr in ("", "/"):
        return [] if ptr == "" else [""]
    if not ptr.startswith("/"):
        raise ValueError(f"invalid JSON pointer: {ptr!r}")
    return [_unescape(p) for p in ptr.split("/")[1:]]


def _get_by_pointer(doc: Any, tokens: list[str]) -> Any:
    cur = doc
    for tok in tokens:
        if isinstance(cur, list):
            cur = cur[int(tok)]
        elif isinstance(cur, Mapping):
            cur = cur[tok]
        else:
            raise KeyError(tok)
    return cur


def _set_by_pointer(doc: Any, tokens: list[str], value: Any) -> None:
    if not tokens:
        raise ValueError("cannot set document root via pointer here")
    parent = _get_by_pointer(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, list):
        idx = len(parent) if last == "-" else int(last)
        if idx == len(parent):
            parent.append(value)
        else:
            parent[idx] = value
    else:
        parent[last] = value


def _del_by_pointer(doc: Any, tokens: list[str]) -> None:
    parent = _get_by_pointer(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, list):
        parent.pop(int(last))
    else:
        parent.pop(last, None)


# ---- RFC 6902 (subset) --------------------------------------------------
def apply_patch(doc: Any, patch: list[dict]) -> Any:
    """Apply add / remove / replace ops. Returns the (mutated) doc."""
    for op in patch:
        kind = op["op"]
        tokens = _split_pointer(op["path"])
        if kind == "add":
            if not tokens:
                return op["value"]
            _set_by_pointer(doc, tokens, op["value"])
        elif kind == "remove":
            _del_by_pointer(doc, tokens)
        elif kind == "replace":
            if not tokens:
                return op["value"]
            _set_by_pointer(doc, tokens, op["value"])
        else:
            raise ValueError(f"unsupported patch op: {kind!r}")
    return doc


def diff(a: Any, b: Any, *, base: str = "") -> list[dict]:
    """Return the minimal list of add/remove/replace ops that turns
    `a` into `b`. Recurses into dicts; treats lists atomically (whole-
    list replace) — schema-authoring rarely benefits from per-item
    list diffs."""
    patch: list[dict] = []
    if isinstance(a, Mapping) and isinstance(b, Mapping):
        for k in a.keys() | b.keys():
            path = f"{base}/{_escape(str(k))}"
            if k in a and k not in b:
                patch.append({"op": "remove", "path": path})
            elif k not in a and k in b:
                patch.append({"op": "add", "path": path, "value": b[k]})
            elif a[k] != b[k]:
                if isinstance(a[k], Mapping) and isinstance(b[k], Mapping):
                    patch.extend(diff(a[k], b[k], base=path))
                else:
                    patch.append({"op": "replace", "path": path, "value": b[k]})
        return patch
    if a != b:
        if base == "":
            patch.append({"op": "replace", "path": "", "value": b})
        else:
            patch.append({"op": "replace", "path": base, "value": b})
    return patch


# ---- Schema merging -----------------------------------------------------
def _widest_type(ts: list) -> str | list:
    uniq = []
    for t in ts:
        if t and t not in uniq:
            uniq.append(t)
    if len(uniq) == 1:
        return uniq[0]
    return uniq


def merge_schemas(schemas: list[dict]) -> dict:
    """Return a "union" JSON Schema covering every input.

    - type → single type if they agree, else list-of-types
    - required → intersection (only fields required *everywhere*)
    - properties → union; property merged recursively
    - enum → union
    - format → kept if they all agree, dropped otherwise
    - other primitives: last one wins when identical, dropped when not
    - adds `x-sources` → list of the source schemas' `$id` or a
      stable ordinal when they lack one, for auditability.
    """
    if not schemas:
        return {}
    if len(schemas) == 1:
        return dict(schemas[0])

    out: dict = {}

    # type
    types = [s.get("type") for s in schemas if s.get("type") is not None]
    if types:
        out["type"] = _widest_type(types)

    # format
    formats = {s.get("format") for s in schemas if s.get("format")}
    if len(formats) == 1:
        out["format"] = next(iter(formats))

    # required — intersection
    reqs = [set(s.get("required") or ()) for s in schemas if "required" in s]
    if reqs:
        inter = set.intersection(*reqs)
        out["required"] = sorted(inter)

    # properties — union with recursive merge
    prop_names: set[str] = set()
    for s in schemas:
        prop_names |= set((s.get("properties") or {}).keys())
    if prop_names:
        out["properties"] = {}
        for name in sorted(prop_names):
            variants = [
                (s.get("properties") or {}).get(name)
                for s in schemas
                if name in (s.get("properties") or {})
            ]
            out["properties"][name] = merge_schemas(
                [v for v in variants if isinstance(v, Mapping)]
            )

    # enum — union, stable order
    enum_vals: list = []
    for s in schemas:
        for v in s.get("enum") or []:
            if v not in enum_vals:
                enum_vals.append(v)
    if enum_vals:
        out["enum"] = enum_vals

    # bounds: widest window
    for k_min in ("minimum", "minLength", "minItems"):
        vals = [s[k_min] for s in schemas if k_min in s]
        if vals:
            out[k_min] = min(vals)
    for k_max in ("maximum", "maxLength", "maxItems"):
        vals = [s[k_max] for s in schemas if k_max in s]
        if vals:
            out[k_max] = max(vals)

    # provenance
    sources: list = []
    for i, s in enumerate(schemas):
        sources.append(s.get("$id") or f"variant-{i}")
    out["x-sources"] = sources
    return out
