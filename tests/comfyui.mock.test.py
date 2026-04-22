#!/usr/bin/env python3
"""End-to-end harness for LMStudioNode against the jbang WireMock facade.

Boots tests/lm-studio.wiremock.jbang.kt as a subprocess, waits for the
admin endpoint, invokes LMStudioNode.get_response in API mode against
the mock, prints a pass/fail table, and tears down.

Run:
    python tests/comfyui.mock.test.py
    python tests/comfyui.mock.test.py --spec tests/lms-openapi.yaml --port 8089
    python tests/comfyui.mock.test.py --keep   # leave facade running
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

import requests

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
SCRIPT = HERE / "lm-studio.wiremock.jbang.kt"
DEFAULT_SPEC = HERE / "lms-openapi.yaml"


def _port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex((host, port)) != 0


def _wait_ready(url: str, timeout_s: float = 60.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout_s:
        try:
            r = requests.get(url, timeout=2)
            if r.ok:
                return
        except requests.RequestException:
            pass
        time.sleep(0.5)
    raise TimeoutError(f"WireMock never came up at {url}")


@contextmanager
def jbang_facade(spec: Path, host: str, port: int, log_path: Path):
    """Start the jbang facade; kill it on exit."""
    if not _port_free(host, port):
        raise RuntimeError(f"{host}:{port} is already in use")
    cmd = [
        "jbang", str(SCRIPT),
        "start",
        "--spec", str(spec),
        "--host", host,
        "--port", str(port),
    ]
    print(f"[harness] launching: {' '.join(cmd)}")
    with log_path.open("wb") as logf:
        proc = subprocess.Popen(
            cmd, cwd=str(REPO), stdout=logf, stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )
    try:
        _wait_ready(f"http://{host}:{port}/__admin/mappings")
        print(f"[harness] facade ready at http://{host}:{port}")
        yield proc
    finally:
        if proc.poll() is None:
            print("[harness] stopping facade")
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


# --- WireMock helpers ----------------------------------------------------
def wm_reset(base: str) -> None:
    # Clears mappings and request journal. In WireMock 3.x
    # /__admin/requests/reset is gone; /__admin/reset is the global reset.
    requests.post(f"{base}/__admin/reset", timeout=5).raise_for_status()


def wm_stub(base: str, body: dict | str, status: int = 200,
            method: str = "POST",
            url_path: str = "/api/v0/chat/completions") -> None:
    mapping = {
        "request": {"method": method, "urlPath": url_path},
        "response": {
            "status": status,
            "headers": {"Content-Type": "application/json"},
            "body": body if isinstance(body, str) else json.dumps(body),
        },
    }
    requests.post(f"{base}/__admin/mappings", json=mapping, timeout=5).raise_for_status()


def wm_seed_default(base: str) -> None:
    """Re-install the default happy-path stub after a reset."""
    wm_stub(base, {
        "choices": [{"message": {"role": "assistant",
                                 "content": "stubbed reply from wiremock-lms"}}],
        "usage": {"prompt_tokens": 4, "completion_tokens": 6},
        "stats": {"tokens_per_second": 10.0},
    })


# --- Test scenarios ------------------------------------------------------
def _import_node():
    sys.path.insert(0, str(REPO))
    from node import LMStudioNode  # noqa: WPS433
    return LMStudioNode()


def scenario_happy_path(node, base: str) -> None:
    wm_reset(base); wm_seed_default(base)
    out, stats = node.get_response(
        system_prompt="sys", user_message="hi",
        model_id="m1", server_address=base,
        temperature=0.7, max_tokens=64,
        thinking_tokens=True, use_sdk=False, image=None, debug=False,
    )
    assert out == "stubbed reply from wiremock-lms", f"unexpected output: {out!r}"
    assert "Tokens per Second: 10.00" in stats, stats
    assert "Input Tokens: 4" in stats
    assert "Output Tokens: 6" in stats


def scenario_thinking_stripped(node, base: str) -> None:
    wm_reset(base)
    wm_stub(base, {
        "choices": [{"message": {"content": "<think>secret</think>visible"}}],
        "usage": {}, "stats": {},
    })
    out, _ = node.get_response(
        system_prompt="s", user_message="u", model_id="m",
        server_address=base, temperature=0.0, max_tokens=16,
        thinking_tokens=False, use_sdk=False, image=None, debug=False,
    )
    assert out == "visible", f"expected 'visible', got {out!r}"


def scenario_http_500(node, base: str) -> None:
    wm_reset(base)
    wm_stub(base, {"error": "boom"}, status=500)
    out, stats = node.get_response(
        system_prompt="s", user_message="u", model_id="m",
        server_address=base, temperature=0.0, max_tokens=16,
        thinking_tokens=True, use_sdk=False, image=None, debug=False,
    )
    assert out.startswith("Error:"), f"expected error string, got {out!r}"
    assert stats == node.default_stats


def scenario_connection_refused(node) -> None:
    out, stats = node.get_response(
        system_prompt="s", user_message="u", model_id="m",
        server_address="http://127.0.0.1:1", temperature=0.0, max_tokens=16,
        thinking_tokens=True, use_sdk=False, image=None, debug=False,
    )
    assert "Connection error" in out, f"expected connection error, got {out!r}"
    assert stats == node.default_stats


def scenario_request_shape(node, base: str) -> None:
    wm_reset(base); wm_seed_default(base)
    node.get_response(
        system_prompt="SYS", user_message="USR", model_id="mX",
        server_address=base, temperature=0.33, max_tokens=16,
        thinking_tokens=True, use_sdk=False, image=None, debug=False,
    )
    r = requests.get(f"{base}/__admin/requests", timeout=5).json()
    reqs = r.get("requests", [])
    assert len(reqs) >= 1, "no requests recorded"
    body = json.loads(reqs[0]["request"]["body"])
    assert body["model"] == "mX"
    assert body["temperature"] == 0.33
    assert body["stream"] is False
    assert body["messages"] == [
        {"role": "system", "content": "SYS"},
        {"role": "user",   "content": "USR"},
    ]


SCENARIOS: list[tuple[str, Callable[..., Any], bool]] = [
    ("happy_path",          scenario_happy_path,          True),
    ("thinking_stripped",   scenario_thinking_stripped,   True),
    ("http_500",            scenario_http_500,            True),
    ("request_shape",       scenario_request_shape,       True),
    ("connection_refused",  scenario_connection_refused,  False),  # no base
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8089)
    ap.add_argument("--log",  type=Path, default=Path("/tmp/wiremock.log"))
    ap.add_argument("--keep", action="store_true",
                    help="leave facade running after tests")
    args = ap.parse_args()

    if not SCRIPT.exists():
        print(f"[harness] missing {SCRIPT}", file=sys.stderr); return 2
    if not args.spec.exists():
        print(f"[harness] missing spec {args.spec}", file=sys.stderr); return 2

    base = f"http://{args.host}:{args.port}"
    node = _import_node()
    results: list[tuple[str, str, str]] = []

    cm = jbang_facade(args.spec, args.host, args.port, args.log)
    try:
        proc = cm.__enter__()
        for name, fn, needs_base in SCENARIOS:
            try:
                fn(node, base) if needs_base else fn(node)
                results.append((name, "PASS", ""))
            except AssertionError as e:
                results.append((name, "FAIL", str(e)))
            except Exception as e:  # noqa: BLE001
                results.append((name, "ERROR", f"{type(e).__name__}: {e}"))
        if args.keep:
            print(f"[harness] --keep set: facade left running at {base}")
            print(f"[harness] stop with: kill -TERM -{os.getpgid(proc.pid)}")
            # don't invoke __exit__; detach
            return _print_report(results)
    finally:
        if not args.keep:
            cm.__exit__(None, None, None)

    return _print_report(results)


def _print_report(results) -> int:
    width = max(len(n) for n, *_ in results)
    print("\n" + "=" * (width + 30))
    for name, status, detail in results:
        print(f"  {name.ljust(width)}  {status:<5}  {detail}")
    print("=" * (width + 30))
    failed = sum(1 for _, s, _ in results if s != "PASS")
    print(f"{len(results) - failed}/{len(results)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
