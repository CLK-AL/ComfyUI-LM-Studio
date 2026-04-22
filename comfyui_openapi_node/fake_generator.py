"""Python mirror of `api/common/FakeGenerator.kt`.

Seeded, per-request atomic counter, `FormatType`-aware realistic data.
Backed by the `Faker` pip package (RFC-coverage-grade — same surface
the JVM side gets from kotlin-faker).

    pip install Faker

Used both by tests and by the Python mock handlers to serve infinite
random rows that actually look like their declared types.
"""
from __future__ import annotations

import itertools
import threading
import uuid
from random import Random
from typing import Any

from .format_type import FormatType

try:
    from faker import Faker as _Faker
    HAVE_FAKER = True
except ImportError:
    _Faker = None
    HAVE_FAKER = False


class _AtomicCounter:
    """Thread-safe monotonic counter (mirrors Kotlin AtomicLong)."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._n = itertools.count(1)

    def next(self) -> int:
        with self._lock:
            return next(self._n)

    def reset(self) -> None:
        with self._lock:
            self._n = itertools.count(1)


class FakeGenerator:
    def __init__(self, seed: int = 0, locale: str = "en_US") -> None:
        self._rng = Random(seed)
        self._counter = _AtomicCounter()
        if HAVE_FAKER:
            self._faker = _Faker(locale)
            self._faker.seed_instance(seed)
        else:
            self._faker = None

    def next_id(self) -> int:
        return self._counter.next()

    def reset(self) -> None:
        self._counter.reset()

    # ------------------------------------------------------------------
    def for_format(self, fmt: FormatType) -> str:
        """Return a fake value suited to `fmt`, rendered as a string."""
        f = self._faker
        r = self._rng
        if fmt is FormatType.TEXT:
            return f.sentence() if f else "lorem ipsum"
        if fmt in (FormatType.TEXTAREA, FormatType.MARKDOWN,
                   FormatType.DYNAMIC_PROMPT):
            return f.paragraph() if f else "paragraph"
        if fmt is FormatType.PASSWORD:
            return f.password(length=12) if f else "p4ssword"
        if fmt in (FormatType.EMAIL, FormatType.VCARD_EMAIL):
            return f.email() if f else "user@example.com"
        if fmt in (FormatType.URL, FormatType.VCARD_URL):
            return f.url() if f else "https://example.com"
        if fmt is FormatType.SEARCH:
            return f.word() if f else "query"
        if fmt in (FormatType.TEL, FormatType.VCARD_TEL):
            return f.phone_number() if f else "+1 555 0100"
        if fmt in (FormatType.UUID, FormatType.VCARD_UID, FormatType.ICAL_UID):
            return str(uuid.UUID(int=r.getrandbits(128)))
        if fmt is FormatType.COLOR:
            return f"#{r.randrange(0x1000000):06x}"
        if fmt in (FormatType.DATE, FormatType.VCARD_BDAY,
                   FormatType.VCARD_ANNIVERSARY):
            return (f.date_of_birth().isoformat()
                    if f else "1970-01-01")
        if fmt is FormatType.TIME:
            return f"{r.randrange(0,24):02d}:{r.randrange(0,60):02d}:{r.randrange(0,60):02d}"
        if fmt in (FormatType.DATETIME, FormatType.VCARD_REV,
                   FormatType.ICAL_DTSTART, FormatType.ICAL_DTEND,
                   FormatType.ICAL_DTSTAMP, FormatType.ICAL_DUE,
                   FormatType.ICAL_COMPLETED, FormatType.ICAL_RECUR_ID):
            if f:
                return f.date_time().replace(microsecond=0).isoformat() + "Z"
            return "2026-04-22T12:00:00Z"
        if fmt is FormatType.MONTH:
            return f"{r.randrange(2000,2030):04d}-{r.randrange(1,13):02d}"
        if fmt is FormatType.WEEK:
            return f"{r.randrange(2000,2030):04d}-W{r.randrange(1,54):02d}"
        if fmt is FormatType.YEAR:
            return str(r.randrange(1900, 2100))
        if fmt is FormatType.QUARTER:
            return str(r.randrange(1, 5))
        if fmt is FormatType.MONTH_OF_YEAR:
            return str(r.randrange(1, 13))
        if fmt is FormatType.DAY:
            return str(r.randrange(1, 32))
        if fmt is FormatType.DAY_OF_WEEK:
            return str(r.randrange(1, 8))
        if fmt is FormatType.DAY_OF_YEAR:
            return str(r.randrange(1, 367))
        if fmt is FormatType.ISO_WEEK_NUM:
            return str(r.randrange(1, 54))
        if fmt is FormatType.HOUR:
            return str(r.randrange(0, 24))
        if fmt in (FormatType.MINUTE, FormatType.SECOND):
            return str(r.randrange(0, 60))
        if fmt is FormatType.MILLISECOND:
            return str(r.randrange(0, 1000))
        if fmt in (FormatType.TIMEZONE, FormatType.VCARD_TZ,
                   FormatType.ICAL_TZID):
            return "Europe/" + (f.city().replace(" ", "_") if f else "London")
        if fmt is FormatType.OFFSET:
            return f"+{r.randrange(0,13):02d}:00"
        if fmt in (FormatType.DURATION, FormatType.ICAL_DURATION):
            return f"PT{r.randrange(1,25)}H"
        if fmt is FormatType.IPV4:
            return f.ipv4() if f else "0.0.0.0"
        if fmt is FormatType.IPV6:
            return f.ipv6() if f else "::1"
        if fmt is FormatType.HOSTNAME:
            return f.domain_name() if f else "example.com"
        if fmt is FormatType.REGEX:
            return "^.*$"
        if fmt is FormatType.JSON_POINTER:
            return "/" + (f.word() if f else "x")
        if fmt in (FormatType.BYTE, FormatType.BINARY):
            return f"/tmp/{f.file_name() if f else 'blob'}"
        if fmt is FormatType.HIDDEN:
            return f"hidden:{self.next_id()}"
        if fmt in (FormatType.GEOJSON, FormatType.ICAL_GEO):
            lat, lon = (float(f.latitude()), float(f.longitude())) if f else (0.0, 0.0)
            if fmt is FormatType.GEOJSON:
                return f'{{"type":"Point","coordinates":[{lon},{lat}]}}'
            return f"{lat};{lon}"
        if fmt is FormatType.VCARD_GEO:
            lat, lon = (float(f.latitude()), float(f.longitude())) if f else (0.0, 0.0)
            return f"geo:{lat},{lon}"
        if fmt is FormatType.JSON_OBJECT:
            return f'{{"id":{self.next_id()}}}'
        if fmt is FormatType.JSON_ARRAY:
            return "[]"
        if fmt is FormatType.INT32:
            return str(r.randrange(0, 2**31 - 1))
        if fmt is FormatType.INT64:
            return str(self.next_id())
        if fmt in (FormatType.FLOAT_ if hasattr(FormatType, "FLOAT_") else FormatType.FLOAT,
                   FormatType.DOUBLE if hasattr(FormatType, "DOUBLE") else FormatType.DOUBLE,
                   FormatType.RANGE, FormatType.KNOB, FormatType.NUMBER_FIELD):
            return f"{r.random() * 100:.4f}"
        if fmt in (FormatType.BOOL, FormatType.CHECKBOX):
            return str(r.choice([True, False]))
        if fmt is FormatType.ENUM:
            return f"option_{r.randrange(1, 6)}"
        if fmt is FormatType.RADIO:
            return f"radio_{r.randrange(1, 4)}"
        if fmt is FormatType.MULTI_SELECT:
            return '["a","b"]'
        if fmt in (FormatType.IMAGE, FormatType.MASK, FormatType.WEBCAM):
            return f"/images/{f.file_name(extension='png') if f else 'img.png'}"
        if fmt is FormatType.AUDIO:
            return f"/audio/{f.file_name(extension='wav') if f else 'a.wav'}"
        if fmt is FormatType.VIDEO:
            return f"/video/{f.file_name(extension='mp4') if f else 'v.mp4'}"
        if fmt in (FormatType.LATENT, FormatType.CONDITIONING,
                   FormatType.CLIP_VISION_OUTPUT):
            return '{"shape":[1,4,64,64]}'
        if fmt in (FormatType.MODEL, FormatType.CLIP, FormatType.VAE,
                   FormatType.CONTROL_NET, FormatType.STYLE_MODEL,
                   FormatType.CLIP_VISION, FormatType.UPSCALE_MODEL):
            return (f.word().replace(" ", "_") if f else "model") + ".safetensors"
        if fmt is FormatType.VCARD_FN:
            return f.name() if f else "Ada Lovelace"
        if fmt is FormatType.VCARD_N:
            if f:
                return f"{f.last_name()};{f.first_name()};;;"
            return "Lovelace;Ada;;;"
        if fmt is FormatType.VCARD_NICKNAME:
            return f.first_name() if f else "Ada"
        if fmt is FormatType.VCARD_GENDER:
            return r.choice(["M", "F", "O", "N", "U"])
        if fmt is FormatType.VCARD_ADR:
            if f:
                return f";;{f.street_address()};{f.city()};{f.state()};{f.postcode()};{f.country()}"
            return ";;;;;;"
        if fmt in (FormatType.VCARD_TITLE, FormatType.VCARD_ROLE):
            return f.job() if f else "Mathematician"
        if fmt is FormatType.VCARD_ORG:
            return f.company() if f else "Analytical Engine"
        if fmt is FormatType.VCARD_NOTE:
            return f.sentence() if f else "note"
        if fmt is FormatType.VCARD_CATEGORIES:
            return ",".join([f.word() if f else w for w in ("a", "b", "c")])
        if fmt is FormatType.ICAL_LOCATION:
            return f.address() if f else "1 Infinite Loop"
        if fmt is FormatType.ICAL_SUMMARY:
            return f.sentence(nb_words=5) if f else "Team sync"
        if fmt in (FormatType.ICAL_DESCRIPTION, FormatType.ICAL_COMMENT):
            return f.paragraph() if f else "desc"
        if fmt is FormatType.ICAL_STATUS:    return "CONFIRMED"
        if fmt is FormatType.ICAL_CLASS:     return "PUBLIC"
        if fmt is FormatType.ICAL_TRANSP:    return "OPAQUE"
        if fmt is FormatType.ICAL_PRIORITY:  return str(r.randrange(0, 10))
        if fmt is FormatType.ICAL_SEQUENCE:  return str(self.next_id())
        if fmt is FormatType.ICAL_RRULE:     return "FREQ=WEEKLY;BYDAY=MO;COUNT=10"
        if fmt in (FormatType.ICAL_RDATE, FormatType.ICAL_EXDATE):
            # RDATE / EXDATE values are comma-separated DATE-TIME
            # strings. A seeded single-point value is a valid example.
            if f:
                return f.date_time().replace(microsecond=0).isoformat() + "Z"
            return "20260422T120000Z"
        if fmt in (FormatType.ICAL_ATTENDEE, FormatType.ICAL_ORGANIZER):
            return f"mailto:{f.email() if f else 'u@e.com'}"
        if fmt is FormatType.ICAL_CATEGORIES: return "BUSINESS,PERSONAL"
        if fmt is FormatType.ICAL_METHOD:     return "PUBLISH"
        if fmt is FormatType.ICAL_CALSCALE:   return "GREGORIAN"
        if fmt is FormatType.ICAL_RELATED_TO: return f"uid-{self.next_id()}@example.com"
        if fmt is FormatType.SEMI_DELIMITED:
            return ";".join([f.word() if f else w for w in ("a", "b", "c")])
        if fmt is FormatType.CSV_ROW:
            return ",".join([f.word() if f else w for w in ("a", "b", "c")])
        if fmt is FormatType.TSV_ROW:
            return "\t".join([f.word() if f else w for w in ("a", "b", "c")])
        if fmt is FormatType.LOCALE:
            return "en-" + (f.country_code() if f else "US")
        if fmt is FormatType.CALENDAR_SYSTEM:
            return "gregorian"
        # ICU formatter outputs — locale-insensitive stand-ins so test
        # parity holds across providers.
        if fmt is FormatType.PERSON_NAME:
            return f.name() if f else "Ada Lovelace"
        if fmt is FormatType.NUMBER_FMT:
            return f"{r.random() * 1_000_000:,.2f}"
        if fmt is FormatType.DECIMAL:
            return f"{r.random() * 1_000:.2f}"
        if fmt is FormatType.CURRENCY:
            code = f.currency_code() if f else "USD"
            return f"{code} {r.random() * 10_000:,.2f}"
        if fmt is FormatType.MEASURE:
            return f"{1 + r.randrange(100)} kg"
        if fmt is FormatType.UNIT:
            return r.choice([
                "length-meter", "length-kilometer", "mass-kilogram",
                "volume-liter", "temperature-celsius", "duration-hour",
                "speed-kilometer-per-hour", "digital-megabyte"])
        if fmt is FormatType.ORDINAL:
            return f"{1 + r.randrange(100)}th"
        if fmt is FormatType.PLURAL:
            return r.choice(["zero", "one", "two", "few", "many", "other"])
        # Fallback for any not-yet-handled enum value.
        return f"fake:{fmt.name}:{self.next_id()}"
