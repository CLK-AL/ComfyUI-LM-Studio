"""Pytest fixtures for WireMock-backed tests of the LM Studio node.

The session-scoped `wiremock_base` fixture:
 1. Ensures SDKMAN + jbang are installed (see tests/bootstrap.py).
 2. Resolves the LM Studio OpenAPI spec: online first, local fallback.
 3. Launches api/api.mock.jbang.kt (openapi start) and waits for readiness.
 4. Yields the base URL; tears the facade down at session end.

Override knobs:
  WIREMOCK_URL       default http://127.0.0.1:8089
  SKIP_BOOTSTRAP=1   use a WireMock that's already running; skip if absent
  SDKMAN_DIR         non-default SDKMAN location
  LMS_API_VERSION_PREFIX  enforce info.version prefix on the OpenAPI spec
"""
from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest
import requests
from wiremock.constants import Config

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
API_ROOT = REPO / "api"
SCRIPT = API_ROOT / "api.mock.jbang.kt"
LOCAL_SPEC = API_ROOT / "openapi" / "spec" / "lm-studio.yaml"

WIREMOCK_URL = os.environ.get("WIREMOCK_URL", "http://127.0.0.1:8089")
SKIP_BOOTSTRAP = os.environ.get("SKIP_BOOTSTRAP") == "1"

sys.path.insert(0, str(REPO))  # so `from node import ...` works


def _reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        requests.get(f"{url}/__admin/mappings", timeout=timeout).raise_for_status()
        return True
    except Exception:
        return False


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) != 0


def _wait_ready(url: str, timeout_s: float = 60.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout_s:
        if _reachable(url, 1.0):
            return
        time.sleep(0.5)
    raise TimeoutError(f"WireMock never came up at {url}")


def _launch_jbang(url: str, jbang_bin: Path, spec: Path) -> subprocess.Popen:
    u = urlparse(url)
    host, port = u.hostname or "127.0.0.1", u.port or 8089
    if not _port_free(host, port):
        raise RuntimeError(f"{host}:{port} in use but not serving WireMock")
    # Nested subcommand tree: `api-mock openapi start …`
    cmd = [str(jbang_bin), str(SCRIPT), "openapi", "start",
           "--spec", str(spec), "--host", host, "--port", str(port)]
    logf = open("/tmp/wiremock.log", "wb")
    proc = subprocess.Popen(
        cmd, cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    try:
        _wait_ready(url)
    except Exception:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass
        raise
    return proc


@pytest.fixture(scope="session")
def wiremock_base():
    if _reachable(WIREMOCK_URL):
        Config.base_url = f"{WIREMOCK_URL}/__admin"
        yield WIREMOCK_URL
        return

    if SKIP_BOOTSTRAP:
        pytest.skip(
            f"WireMock not reachable at {WIREMOCK_URL} and SKIP_BOOTSTRAP=1"
        )

    # Full bootstrap: SDKMAN + jbang + OpenAPI spec + facade.
    sys.path.insert(0, str(HERE))
    import bootstrap  # type: ignore[import-not-found]  # noqa: WPS433
    pins = bootstrap._read_sdkmanrc()
    if not pins.jbang:
        pytest.skip("no jbang pin in .sdkmanrc; cannot auto-bootstrap")
    jbang_bin = bootstrap.ensure_jbang(pins.jbang)
    spec = bootstrap.fetch_openapi()

    proc = _launch_jbang(WIREMOCK_URL, jbang_bin, spec)
    Config.base_url = f"{WIREMOCK_URL}/__admin"
    try:
        yield WIREMOCK_URL
    finally:
        if proc.poll() is None:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


_API_HITS: set[tuple[str, str]] = set()  # session-wide (method, path) pairs


@pytest.fixture(autouse=True)
def _record_and_reset(wiremock_base):
    # Run the test, then harvest the request journal into the session-wide
    # hit set, then reset mappings + journal for the next test.
    yield
    try:
        j = requests.get(f"{wiremock_base}/__admin/requests", timeout=5).json()
        for rq in j.get("requests", []):
            url = rq["request"].get("url", "")
            path = url.split("?", 1)[0]
            if path.startswith("/__admin"):
                continue
            _API_HITS.add((rq["request"].get("method", "").upper(), path))
    except Exception:
        pass
    requests.post(f"{wiremock_base}/__admin/reset", timeout=5)


@pytest.fixture
def server_address(wiremock_base):
    return wiremock_base


@pytest.fixture
def node():
    from node import LMStudioNode
    return LMStudioNode()


# --- Spec-driven endpoints -----------------------------------------------
# Single source of truth for paths: api/openapi/spec/lm-studio.yaml. Parse once per
# session. Tests reference paths by semantic key so endpoint renames
# (e.g. /api/v0/… → /v1/…) only need one edit — the spec file itself.
_SPEC_PATH = LOCAL_SPEC


def _parse_openapi_paths(text: str) -> dict:
    """Return a dict of {path: [methods]} from an OpenAPI YAML document.

    Intentionally small — avoids a PyYAML dep. Only handles the shape we
    care about: top-level `paths:` block with `  /path:` children and
    per-method keys (`get:`, `post:`, …) one level deeper.
    """
    out: dict[str, list[str]] = {}
    in_paths = False
    current: str | None = None
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith("paths:"):
            in_paths = True
            continue
        if in_paths and raw and not raw.startswith((" ", "\t")):
            break  # left the paths block
        if not in_paths:
            continue
        # path entries: 2-space indent, starts with '/', ends with ':'
        if raw.startswith("  /") and raw.rstrip().endswith(":"):
            current = raw.strip().rstrip(":").strip()
            out[current] = []
            continue
        # method entries: 4-space indent under a path
        stripped = raw.strip()
        if current and raw.startswith("    ") and stripped.endswith(":"):
            m = stripped.rstrip(":").strip().lower()
            if m in {"get", "post", "put", "delete", "patch", "options", "head"}:
                out[current].append(m)
    return out


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print API coverage: OpenAPI spec vs. WireMock request journal.

    If $API_COVERAGE_MARKDOWN is set, also writes a markdown summary
    there — used by CI to feed $GITHUB_STEP_SUMMARY.
    """
    text = _SPEC_PATH.read_text() if _SPEC_PATH.exists() else ""
    if not text:
        return
    paths = _parse_openapi_paths(text)
    expected = {(m.upper(), p) for p, ms in paths.items() for m in ms}
    if not expected:
        return
    covered = {k for k in expected if k in _API_HITS}
    extra = {k for k in _API_HITS if k not in expected}
    pct = 100.0 * len(covered) / len(expected)

    tr = terminalreporter
    tr.write_sep("=", "API coverage (LM Studio OpenAPI vs. WireMock hits)")
    tr.write_line(f"covered: {len(covered)}/{len(expected)} ({pct:.0f}%)")
    for method, path in sorted(expected):
        mark = "OK" if (method, path) in covered else "--"
        tr.write_line(f"  [{mark}] {method:<6} {path}")
    if extra:
        tr.write_line("requests to paths not in spec:")
        for method, path in sorted(extra):
            tr.write_line(f"  [+ ] {method:<6} {path}")

    md_path = os.environ.get("API_COVERAGE_MARKDOWN")
    if md_path:
        try:
            from pathlib import Path as _P
            ref = os.environ.get("COVERAGE_LABEL", "tests")
            lines = [
                f"### API coverage — {ref}",
                "",
                f"**{len(covered)}/{len(expected)} ({pct:.0f}%)** of "
                f"`api/openapi/spec/lm-studio.yaml` paths hit.",
                "",
                "| status | method | path |",
                "| :----: | :----- | :--- |",
            ]
            for m, p in sorted(expected):
                ok = (m, p) in covered
                lines.append(f"| {'✅' if ok else '—'} | `{m}` | `{p}` |")
            if extra:
                lines += ["", "**Requests to paths not in spec:**", ""]
                for m, p in sorted(extra):
                    lines.append(f"- `{m} {p}`")
            _P(md_path).write_text("\n".join(lines) + "\n")
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture(scope="session")
def spec_paths() -> dict:
    """Semantic-key → path map, read from the LM Studio OpenAPI spec.

    Keys we care about:
      - "chat_completions" : first POST path containing 'chat' + 'completions'
      - "models"           : first GET path containing 'models'
      - "all"              : full {path: [methods]} mapping
    """
    text = _SPEC_PATH.read_text() if _SPEC_PATH.exists() else ""
    paths = _parse_openapi_paths(text)
    chat = next(
        (p for p, ms in paths.items()
         if "post" in ms and "chat" in p and "completions" in p),
        "/api/v0/chat/completions",  # safe default if spec is empty
    )
    models = next(
        (p for p, ms in paths.items()
         if "get" in ms and "models" in p),
        "/api/v0/models",
    )
    return {"chat_completions": chat, "models": models, "all": paths}
