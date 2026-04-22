"""Parse iCal (.ics) and vCard (.vcf) text into jCal (RFC 7265) and
jCard (RFC 7095) JSON.

Preferred backend: `vobject` (full RFC 2425 / 2426 / 5545 / 6350
coverage — folding, escaping, component nesting, structured values,
line length rules, parameter roundtrip).

    pip install vobject

Fallback: a dependency-free line-folding tokenizer. Covers the common
shapes the test suite touches (BEGIN/END nesting, structured N/ADR,
GEO, params) without requiring an extra install.

The Kotlin side uses ical4j + ez-vcard (see api/common/IcsVcfParser.kt).

## jCard / jCal shape

RFC 7095 / 7265 define a JSON projection of the same content:

    jCard  = ["vcard",    [property, ...]]
    jCal   = ["vcalendar",[property, ...], [component, ...]]

Each property is a 4-tuple:

    [name, params, value_type, value(s)]

Where:
    name       lower-case property name ("fn", "n", "adr", "dtstart",…)
    params     object of parameter name → value(s)
    value_type "text" | "uri" | "date" | "date-time" | "duration" | …
    value(s)   one string or an array (for structured properties
               like N = [family, given, additional, prefixes, suffixes])

Components nest: VEVENT inside VCALENDAR, VALARM inside VEVENT, etc.

## Public API

    parse_vcard_to_jcard(text)  -> list          (single vCard)
    parse_vcards_to_jcard(text) -> list[list]    (all vCards in text)
    parse_ical_to_jcal(text)    -> list          (single VCALENDAR)

    jcard_to_vcf(jcard)         -> str
    jcal_to_ics(jcal)           -> str
"""
from __future__ import annotations

import re
from typing import Iterator

try:
    import vobject as _vobject
    HAVE_VOBJECT = True
except ImportError:
    _vobject = None
    HAVE_VOBJECT = False

try:
    import icalendar as _icalendar       # official iCal backend
    HAVE_ICALENDAR = True
except ImportError:
    _icalendar = None
    HAVE_ICALENDAR = False


# ---- line unfolding (RFC 5545 §3.1 / RFC 6350 §3.2) --------------------
def _unfold(text: str) -> list[str]:
    """Join continuation lines (CRLF + space / tab). Strip trailing CR."""
    raw = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    for line in raw:
        if out and (line.startswith(" ") or line.startswith("\t")):
            out[-1] += line[1:]
        else:
            out.append(line)
    return [l for l in out if l]


# ---- property line parser ---------------------------------------------
_NAME_RE   = re.compile(r"^(?P<name>[A-Za-z][A-Za-z0-9\-.]*)")


def _parse_line(line: str) -> tuple[str, dict[str, list[str]], str] | None:
    m = _NAME_RE.match(line)
    if m is None:
        return None
    name = m.group("name")
    rest = line[m.end():]

    params: dict[str, list[str]] = {}
    while rest.startswith(";"):
        # ;PARAM=value[,value2]
        rest = rest[1:]
        eq = rest.find("=")
        if eq == -1:
            break
        pname = rest[:eq].upper()
        # scan value respecting quoted strings, stop at ':' or ';'
        i = eq + 1
        value_start = i
        in_quote = False
        while i < len(rest):
            c = rest[i]
            if c == '"':
                in_quote = not in_quote
            elif not in_quote and c in ":;":
                break
            i += 1
        raw_vals = rest[value_start:i]
        params[pname] = [v.strip('"') for v in raw_vals.split(",")]
        rest = rest[i:]

    if not rest.startswith(":"):
        return None
    value = rest[1:]  # everything after the colon (may contain escaped sequences)
    return name.lower(), params, value


def _unescape(v: str) -> str:
    # Unescape common escape sequences in iCal/vCard text values.
    return (v.replace("\\n", "\n").replace("\\N", "\n")
              .replace("\\,", ",").replace("\\;", ";")
              .replace("\\\\", "\\"))


def _split_structured(raw: str) -> list[str | list[str]]:
    """Split a structured property value on unescaped ';' then
    recursively on ',' inside each field."""
    parts: list[str | list[str]] = []
    for p in _split_unescaped(raw, ";"):
        if "," in p:
            unesc = p.replace("\\,", "\x00")
            sub = [s.replace("\x00", ",") for s in unesc.split(",")]
            parts.append([_unescape(s) for s in sub])
        else:
            parts.append(_unescape(p))
    return parts


def _split_unescaped(s: str, delim: str) -> list[str]:
    out: list[str] = []
    buf: list[str] = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            buf.append(s[i:i + 2])
            i += 2
            continue
        if c == delim:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(c)
        i += 1
    out.append("".join(buf))
    return out


# ---- property-name → (jCard, jCal) value-type resolution --------------
_TEXT_PROPS = {
    "fn", "n", "nickname", "gender", "adr", "title", "role", "org",
    "note", "categories", "kind", "xml",
    # iCal text-ish
    "summary", "description", "location", "comment", "status", "class",
    "transp", "method", "calscale", "resources",
}
_URI_PROPS = {"url", "photo", "logo", "sound", "source", "attach",
              "attendee", "organizer", "contact", "caladruri", "caluri"}
_DATE_TIME_PROPS = {"dtstart", "dtend", "dtstamp", "due", "completed",
                    "created", "last-modified", "rev", "bday",
                    "anniversary", "recurrence-id"}
_INTEGER_PROPS = {"priority", "sequence", "percent-complete", "repeat"}


def _value_type(name: str, params: dict[str, list[str]]) -> str:
    if "VALUE" in params and params["VALUE"]:
        return params["VALUE"][0].lower()
    if name in _URI_PROPS:
        return "uri"
    if name in _DATE_TIME_PROPS:
        return "date-time"
    if name in _INTEGER_PROPS:
        return "integer"
    return "text"


def _value_for(name: str, raw: str) -> object:
    """Render raw value text into the jCard/jCal JSON value shape."""
    if name in ("n", "adr", "gender", "org"):
        return _split_structured(raw)
    if name == "geo":
        # iCal: lat;lon.   vCard: geo:lat,lon (URI).  Both float tuples.
        sep = ";" if ";" in raw else ","
        parts = raw.split(sep, 1)
        if len(parts) == 2:
            try:
                return [float(parts[0].replace("geo:", "")),
                        float(parts[1])]
            except ValueError:
                pass
    return _unescape(raw)


def _params_json(params: dict[str, list[str]]) -> dict:
    """Parameters in jCard/jCal are a single object; single-value
    params become scalars, multi-value stay arrays. Names lower-case."""
    out: dict = {}
    for k, v in params.items():
        if k == "VALUE":
            continue     # value type is carried on the tuple itself
        key = k.lower()
        out[key] = v[0] if len(v) == 1 else v
    return out


# ---- stream tokenisation (BEGIN/END components) -----------------------
def _tokens(text: str) -> Iterator[tuple[str, str, dict, str, object]]:
    """Yield ('prop', name, params, value_type, value) or
    ('begin', kind, {}, '', '') / ('end', kind, {}, '', '') tuples."""
    for line in _unfold(text):
        p = _parse_line(line)
        if p is None:
            continue
        name, params, raw = p
        if name == "begin":
            yield ("begin", raw.lower(), {}, "", "")
        elif name == "end":
            yield ("end", raw.lower(), {}, "", "")
        else:
            yield ("prop", name, params, _value_type(name, params),
                   _value_for(name, raw))


# ---- jCard / jCal builders --------------------------------------------
def _build(tokens: list[tuple]) -> list:
    """Build one component from tokens. Recurses on nested BEGIN/END.

    Returns [name, [properties...], [sub_components...]].
    The jCard projection is the same shape with the sub-components
    list omitted for a solitary vCard."""
    it = iter(tokens)
    root_name = ""
    # Expect `begin:<kind>` first.
    first = next(it, None)
    if first is None:
        return []
    assert first[0] == "begin"
    root_name = first[1]
    props: list = []
    comps: list = []
    while True:
        tok = next(it, None)
        if tok is None:
            break
        kind = tok[0]
        if kind == "end" and tok[1] == root_name:
            break
        if kind == "prop":
            _, name, params, vtype, value = tok
            props.append([name, _params_json(params), vtype, value])
        elif kind == "begin":
            # collect until matching END, then recurse
            child = [tok]
            depth = 1
            while depth:
                n = next(it, None)
                if n is None:
                    break
                child.append(n)
                if n[0] == "begin":
                    depth += 1
                elif n[0] == "end":
                    depth -= 1
            comps.append(_build(child))
    if comps:
        return [root_name, props, comps]
    return [root_name, props]


# ---- vobject-backed walkers (preferred when available) ----------------
def _vobject_component_to_jcal(comp) -> list:
    """Walk a vobject Component into a jCard/jCal-shaped nested list."""
    name = (getattr(comp, "name", "") or "").lower()
    props: list = []
    subs: list = []
    for child_name in getattr(comp, "contents", {}) or {}:
        for child in comp.contents[child_name]:
            if hasattr(child, "contents"):
                # nested component
                subs.append(_vobject_component_to_jcal(child))
                continue
            params = getattr(child, "params", {}) or {}
            params_js: dict = {}
            for pk, pv in params.items():
                if pk.upper() == "VALUE":
                    continue
                params_js[pk.lower()] = pv[0] if isinstance(pv, list) and len(pv) == 1 else pv
            raw = getattr(child, "value", "")
            prop_name = child_name.lower()
            if prop_name == "n":
                # vobject Name object → [family, given, additional, prefixes, suffixes]
                value: object = [
                    str(getattr(raw, "family",     "") or ""),
                    str(getattr(raw, "given",      "") or ""),
                    str(getattr(raw, "additional", "") or ""),
                    str(getattr(raw, "prefix",     "") or ""),
                    str(getattr(raw, "suffix",     "") or ""),
                ]
            elif prop_name == "adr":
                # vobject Address → [po_box, extended, street, locality,
                #                   region, postal_code, country]
                value = [
                    str(getattr(raw, "box",      "") or ""),
                    str(getattr(raw, "extended", "") or ""),
                    str(getattr(raw, "street",   "") or ""),
                    str(getattr(raw, "city",     "") or ""),
                    str(getattr(raw, "region",   "") or ""),
                    str(getattr(raw, "code",     "") or ""),
                    str(getattr(raw, "country",  "") or ""),
                ]
            elif prop_name in ("gender", "org") and isinstance(raw, object):
                if hasattr(raw, "_fields"):
                    value = list(raw)
                elif isinstance(raw, list):
                    value = raw
                else:
                    value = _split_structured(str(raw))
            elif prop_name == "geo":
                if hasattr(raw, "latitude") and hasattr(raw, "longitude"):
                    value = [float(raw.latitude), float(raw.longitude)]
                else:
                    value = _value_for("geo", str(raw))
            else:
                value = str(raw)
            vtype = _value_type(prop_name, {
                k.upper(): ([v] if not isinstance(v, list) else v)
                for k, v in params.items()
            })
            props.append([prop_name, params_js, vtype, value])
    if subs:
        return [name, props, subs]
    return [name, props]


def parse_vcard_to_jcard(text: str) -> list:
    """Parse exactly one vCard; return `["vcard", [properties...]]`."""
    if HAVE_VOBJECT:
        try:
            comp = _vobject.readOne(text)
        except Exception:
            comp = None
        if comp is not None:
            return _vobject_component_to_jcal(comp)
    return _build(list(_tokens(text)))


def parse_vcards_to_jcard(text: str) -> list[list]:
    """Parse every VCARD in text, return a list of jCard arrays."""
    if HAVE_VOBJECT:
        out: list[list] = []
        try:
            for comp in _vobject.readComponents(text):
                out.append(_vobject_component_to_jcal(comp))
        except Exception:
            out = []
        if out:
            return out
    # fallback line parser
    fall: list[list] = []
    buf: list[tuple] = []
    depth = 0
    for tok in _tokens(text):
        if tok[0] == "begin" and tok[1] == "vcard":
            buf = [tok]
            depth = 1
            continue
        if depth:
            buf.append(tok)
            if tok[0] == "begin":
                depth += 1
            elif tok[0] == "end":
                depth -= 1
                if depth == 0 and tok[1] == "vcard":
                    fall.append(_build(buf))
                    buf = []
    return fall


def _icalendar_to_jcal(cal) -> list:
    """Walk an icalendar.Component tree → jCal list."""
    name = (getattr(cal, "name", "") or "").lower()
    props: list = []
    subs: list = []
    # icalendar.Component: properties are in `property_items()`;
    # sub-components are in `.subcomponents`.
    for prop_name, value in cal.property_items(recursive=False, sorted=False):
        if prop_name.upper() in ("BEGIN", "END"):
            continue
        prop_name_lc = prop_name.lower()
        # Parameters are on `value.params` (icalendar.prop.vProperty).
        params: dict = {}
        for pk, pv in (getattr(value, "params", {}) or {}).items():
            params[pk.lower()] = str(pv)
        vtype = _value_type(prop_name_lc, {
            k.upper(): [str(v)] for k, v in (getattr(value, "params", {}) or {}).items()
        })
        # Best-effort value extraction: icalendar exposes typed helpers
        # (.to_ical() gives the wire form; .dt / .latitude etc. give
        # structured parts when present).
        raw_value: object
        if prop_name_lc == "geo" and hasattr(value, "latitude") and hasattr(value, "longitude"):
            raw_value = [float(value.latitude), float(value.longitude)]
        elif prop_name_lc in ("n", "adr", "gender", "org"):
            wire = value.to_ical().decode() if hasattr(value, "to_ical") else str(value)
            raw_value = _split_structured(wire)
        else:
            wire = value.to_ical() if hasattr(value, "to_ical") else str(value)
            raw_value = wire.decode() if isinstance(wire, (bytes, bytearray)) else str(wire)
        props.append([prop_name_lc, params, vtype, raw_value])
    for sub in getattr(cal, "subcomponents", []) or []:
        subs.append(_icalendar_to_jcal(sub))
    return [name, props, subs] if subs else [name, props]


def parse_ical_to_jcal(text: str) -> list:
    """Parse a VCALENDAR into `["vcalendar", [props], [components]]`."""
    if HAVE_ICALENDAR:
        try:
            cal = _icalendar.Calendar.from_ical(text)
        except Exception:
            cal = None
        if cal is not None:
            return _icalendar_to_jcal(cal)
    if HAVE_VOBJECT:
        try:
            comp = _vobject.readOne(text)
        except Exception:
            comp = None
        if comp is not None:
            return _vobject_component_to_jcal(comp)
    return _build(list(_tokens(text)))


# ---- reverse: jCard / jCal → vcf / ics --------------------------------
def _escape(s: str) -> str:
    return (s.replace("\\", "\\\\")
             .replace(",", "\\,").replace(";", "\\;")
             .replace("\n", "\\n"))


def _render_value(name: str, value: object) -> str:
    if isinstance(value, list):
        if name == "geo" and len(value) == 2:
            sep = ";" if name in ("geo",) else ","
            return f"{value[0]}{sep}{value[1]}"
        out_parts: list[str] = []
        for v in value:
            if isinstance(v, list):
                out_parts.append(",".join(_escape(str(x)) for x in v))
            else:
                out_parts.append(_escape(str(v)))
        return ";".join(out_parts)
    return _escape(str(value))


def _render_params(params: dict) -> str:
    if not params:
        return ""
    out = []
    for k, v in params.items():
        if isinstance(v, list):
            out.append(f";{k.upper()}={','.join(v)}")
        else:
            out.append(f";{k.upper()}={v}")
    return "".join(out)


def _render(component: list) -> list[str]:
    name = component[0]
    props = component[1] if len(component) > 1 else []
    subs  = component[2] if len(component) > 2 else []
    lines: list[str] = [f"BEGIN:{name.upper()}"]
    for prop in props:
        p_name, p_params, _vtype, p_value = prop
        lines.append(
            f"{p_name.upper()}{_render_params(p_params)}:"
            f"{_render_value(p_name, p_value)}"
        )
    for sub in subs:
        lines.extend(_render(sub))
    lines.append(f"END:{name.upper()}")
    return lines


def jcard_to_vcf(jcard: list) -> str:
    return "\r\n".join(_render(jcard)) + "\r\n"


def jcal_to_ics(jcal: list) -> str:
    return "\r\n".join(_render(jcal)) + "\r\n"
