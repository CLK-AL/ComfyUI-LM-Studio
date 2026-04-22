"""Pytest fixtures for WireMock-backed tests of the LM Studio node.

The session-scoped `wiremock_base` fixture:
 1. Ensures SDKMAN + jbang are installed (see tests/bootstrap.py).
 2. Resolves the LM Studio OpenAPI spec: online first, local fallback.
 3. Launches tests/lm-studio.wiremock.jbang.kt and waits for readiness.
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
SCRIPT = HERE / "lm-studio.wiremock.jbang.kt"

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
    cmd = [str(jbang_bin), str(SCRIPT), "start",
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


@pytest.fixture(autouse=True)
def _reset_mappings(wiremock_base):
    # WireMock 3.x global reset (mappings + journal).
    requests.post(f"{wiremock_base}/__admin/reset", timeout=5)
    yield


@pytest.fixture
def server_address(wiremock_base):
    return wiremock_base


@pytest.fixture
def node():
    from node import LMStudioNode
    return LMStudioNode()
