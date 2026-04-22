"""Verify the unified jbang facade (api/api.mock.jbang.kt) resolves deps
and compiles.

`jbang info classpath <file>` runs the full resolve + compile pipeline
without invoking main(). It's our fail-loudly smoke test for the
multi-stack mock server (WireMock + Ktor + rsocket-kotlin) and every
//SOURCES-included Kotlin file under /api/*/.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[6]
SCRIPT = REPO / "api" / "api.mock.jbang.kt"


def _jbang():
    p = shutil.which("jbang")
    if p:
        return p
    home = os.environ.get("SDKMAN_DIR", str(Path.home() / ".sdkman"))
    guess = Path(home) / "candidates" / "jbang" / "current" / "bin" / "jbang"
    return str(guess) if guess.is_file() else None


def test_api_mock_jbang_compiles():
    jbang = _jbang()
    if jbang is None:
        pytest.skip("jbang not installed (SKIP_BOOTSTRAP=1?)")
    assert SCRIPT.is_file()
    r = subprocess.run(
        [jbang, "info", "classpath", str(SCRIPT)],
        cwd=str(REPO),
        capture_output=True, text=True, timeout=600,
    )
    if r.returncode != 0:
        print("STDOUT:", r.stdout[:2000])
        print("STDERR:", r.stderr[:2000])
    assert r.returncode == 0, "api.mock.jbang.kt failed to compile"
    cp = r.stdout
    # Every per-protocol dep should be on the classpath.
    assert "wiremock" in cp and "swagger-parser" in cp
    assert "ktor-server-netty" in cp
    assert "ktor-server-websockets" in cp and "ktor-server-sse" in cp
    assert "rsocket-core-jvm" in cp
    assert "clikt" in cp
    # JDBC stack — Spring + local SQLite + SQLDelight + Postgres + PostGIS.
    assert "spring-jdbc" in cp
    assert "HikariCP" in cp
    assert "sqlite-jdbc" in cp
    assert "sqldelight" in cp
    assert "postgresql" in cp and "postgis" in cp


def test_subcommand_tree_runs():
    jbang = _jbang()
    if jbang is None:
        pytest.skip("jbang not installed")
    r = subprocess.run(
        [jbang, str(SCRIPT), "--help"],
        cwd=str(REPO),
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0
    out = r.stdout
    for sub in ("openapi", "asyncapi", "mcp", "rsocket"):
        assert sub in out, f"missing subcommand {sub!r} in --help output"
