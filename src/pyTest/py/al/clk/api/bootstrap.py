"""Install SDKMAN + jbang and resolve the LM Studio OpenAPI spec.

Callable from pytest (via conftest's wiremock_base fixture) or as a CLI:

    python -m al.clk.api.bootstrap --check           # report state, no install
    python -m al.clk.api.bootstrap --install-jbang   # install SDKMAN + jbang
    python -m al.clk.api.bootstrap --fetch-spec      # pull/refresh OpenAPI cache

All functions return Paths / strings and raise on hard failures. Network
and proxy hiccups are retried; "no network" degrades to the local stub.
"""
from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

log = logging.getLogger("bootstrap")

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
SDKMANRC = REPO / ".sdkmanrc"

# --- Defaults / pins -----------------------------------------------------
SDKMAN_DIR_DEFAULT = Path(os.environ.get("SDKMAN_DIR", str(Path.home() / ".sdkman")))
SDKMAN_CLI_VERSION = os.environ.get("SDKMAN_CLI_VERSION", "5.22.4")
SDKMAN_PLATFORM = os.environ.get("SDKMAN_PLATFORM", "linuxx64")

# LM Studio OpenAPI: try these in order before falling back to the local stub.
OPENAPI_URLS: tuple[str, ...] = (
    "https://lmstudio.ai/docs/openapi.yaml",
    "https://docs.lmstudio.ai/openapi.yaml",
)
API_ROOT = REPO / "api"
LOCAL_SPEC = API_ROOT / "openapi" / "spec" / "lm-studio.yaml"
SPEC_CACHE = REPO / "src" / "pyTest" / "py" / "al" / "clk" / "api" / ".cache" / "lm-studio-openapi.yaml"
# If set, require the spec's info.version to start with this string.
EXPECTED_API_VERSION_PREFIX = os.environ.get("LMS_API_VERSION_PREFIX", "")

MAX_RETRIES = int(os.environ.get("BOOTSTRAP_MAX_RETRIES", "5"))


@dataclass
class Pins:
    java: str | None = None
    kotlin: str | None = None
    jbang: str | None = None


def _read_sdkmanrc(path: Path = SDKMANRC) -> Pins:
    p = Pins()
    if not path.exists():
        return p
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        setattr(p, k.strip(), v.strip())
    return p


# --- Generic retry -------------------------------------------------------
def _retry(fn, *, what: str, retries: int = MAX_RETRIES, base_delay: float = 2.0):
    last: Exception | None = None
    for n in range(retries):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            delay = base_delay * (2 ** n)
            log.info("%s failed (try %d/%d): %s — retry in %.1fs",
                     what, n + 1, retries, e, delay)
            time.sleep(delay)
    raise RuntimeError(f"{what} failed after {retries} retries: {last}") from last


def _download(url: str, dest: Path, timeout: float = 30.0) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "bootstrap.py"})
    with urllib.request.urlopen(req, timeout=timeout) as r, dest.open("wb") as out:
        shutil.copyfileobj(r, out)


# --- SDKMAN --------------------------------------------------------------
def ensure_sdkman(sdkman_dir: Path = SDKMAN_DIR_DEFAULT) -> Path:
    init = sdkman_dir / "bin" / "sdkman-init.sh"
    if init.is_file():
        init.chmod(0o755)
        log.info("SDKMAN present at %s", sdkman_dir)
        return sdkman_dir

    log.info("installing SDKMAN %s -> %s", SDKMAN_CLI_VERSION, sdkman_dir)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        zip_path = tdp / "sdkman.zip"
        url = (
            f"https://github.com/sdkman/sdkman-cli/releases/download/"
            f"{SDKMAN_CLI_VERSION}/sdkman-cli-{SDKMAN_CLI_VERSION}.zip"
        )
        _retry(lambda: _download(url, zip_path), what=f"download {url}")
        import zipfile
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(tdp)
        extracted = next(tdp.glob("sdkman-*"))

        for sub in ("bin", "src", "etc", "var", "candidates", "tmp", "ext"):
            (sdkman_dir / sub).mkdir(parents=True, exist_ok=True)
        shutil.copy(extracted / "bin" / "sdkman-init.sh", sdkman_dir / "bin")
        for sh in (extracted / "src").glob("*.sh"):
            shutil.copy(sh, sdkman_dir / "src")
        (sdkman_dir / "bin" / "sdkman-init.sh").chmod(0o755)
        (sdkman_dir / "var" / "version").write_text(SDKMAN_CLI_VERSION + "\n")
        (sdkman_dir / "var" / "platform").write_text(SDKMAN_PLATFORM + "\n")
        (sdkman_dir / "etc" / "config").write_text(
            "sdkman_auto_answer=true\n"
            "sdkman_auto_selfupdate=false\n"
            "sdkman_insecure_ssl=false\n"
            "sdkman_curl_connect_timeout=7\n"
            "sdkman_curl_max_time=60\n"
            "sdkman_beta_channel=false\n"
            "sdkman_debug_mode=false\n"
            "sdkman_colour_enable=false\n"
            "sdkman_healthcheck_enable=false\n"
        )
    _seed_candidates(sdkman_dir)
    return sdkman_dir


def _seed_candidates(sdkman_dir: Path) -> None:
    cache = sdkman_dir / "var" / "candidates"
    if cache.exists() and cache.stat().st_size:
        return
    try:
        _retry(
            lambda: _download("https://api.sdkman.io/2/candidates/all", cache),
            what="seed candidate list", retries=3,
        )
    except Exception:
        log.warning("could not fetch candidate list; writing minimal fallback")
        cache.write_text("java,kotlin,jbang,gradle,maven,scala\n")


def _sdk(cmd: str, sdkman_dir: Path) -> subprocess.CompletedProcess:
    """Run `sdk <cmd>` via a bash subshell that sources sdkman-init.sh."""
    bash = f'set +u; source "{sdkman_dir}/bin/sdkman-init.sh"; sdk {cmd}'
    return subprocess.run(
        ["bash", "-c", bash], capture_output=True, text=True, check=False,
    )


def ensure_jbang(version: str, sdkman_dir: Path = SDKMAN_DIR_DEFAULT) -> Path:
    ensure_sdkman(sdkman_dir)
    binpath = sdkman_dir / "candidates" / "jbang" / version / "bin" / "jbang"
    if binpath.is_file():
        log.info("jbang %s already installed", version)
        return binpath

    def attempt():
        r = _sdk(f"install jbang {version}", sdkman_dir)
        if "Done installing" in r.stdout:
            return
        raise RuntimeError(r.stdout.splitlines()[-1] if r.stdout else r.stderr)

    _retry(attempt, what=f"sdk install jbang {version}")
    if not binpath.is_file():
        raise RuntimeError(f"jbang install reported success but {binpath} missing")
    return binpath


# --- OpenAPI spec --------------------------------------------------------
def _spec_version(path: Path) -> str | None:
    try:
        # Minimal YAML scan: grab the first `version:` under `info:`.
        in_info = False
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("info:"):
                in_info = True
                continue
            if in_info:
                if stripped and not line.startswith(" ") and not line.startswith("\t"):
                    in_info = False
                    continue
                if stripped.startswith("version:"):
                    return stripped.split(":", 1)[1].strip().strip('"\'')
    except Exception:  # noqa: BLE001
        return None
    return None


def _check_version(path: Path) -> None:
    if not EXPECTED_API_VERSION_PREFIX:
        return
    v = _spec_version(path)
    if v is None:
        log.warning("spec at %s has no info.version; skipping version check", path)
        return
    if not v.startswith(EXPECTED_API_VERSION_PREFIX):
        log.warning(
            "spec info.version=%r does not match expected prefix %r",
            v, EXPECTED_API_VERSION_PREFIX,
        )


def fetch_openapi(urls: Iterable[str] = OPENAPI_URLS,
                  cache: Path = SPEC_CACHE,
                  local_fallback: Path = LOCAL_SPEC,
                  force_refresh: bool = False) -> Path:
    """Return a path to a usable OpenAPI spec.

    Tries each URL in order with retries; on success, caches to `cache`
    and returns it. On total failure, returns the local stub so tests
    can run offline.
    """
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.is_file() and cache.stat().st_size and not force_refresh:
        log.info("using cached spec at %s", cache)
        _check_version(cache)
        return cache

    for url in urls:
        try:
            _retry(lambda u=url: _download(u, cache), what=f"GET {url}", retries=3)
            if cache.stat().st_size > 0:
                log.info("fetched spec from %s -> %s", url, cache)
                _check_version(cache)
                return cache
        except Exception as e:  # noqa: BLE001
            log.info("spec URL unavailable: %s (%s)", url, e)

    if local_fallback.is_file():
        log.warning("using local fallback spec: %s", local_fallback)
        _check_version(local_fallback)
        return local_fallback

    raise RuntimeError("no OpenAPI spec available (remote failed, no local fallback)")


# --- CLI -----------------------------------------------------------------
def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="[%(name)s] %(message)s",
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--install-jbang", action="store_true")
    ap.add_argument("--fetch-spec", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="report state without installing anything")
    ap.add_argument("--force-refresh", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)
    _configure_logging(args.verbose)

    pins = _read_sdkmanrc()
    print(f"pins: java={pins.java} kotlin={pins.kotlin} jbang={pins.jbang}")

    if args.check:
        init = SDKMAN_DIR_DEFAULT / "bin" / "sdkman-init.sh"
        print(f"sdkman: {'ok' if init.is_file() else 'missing'} ({init})")
        jb = SDKMAN_DIR_DEFAULT / "candidates" / "jbang" / (pins.jbang or "") / "bin" / "jbang"
        print(f"jbang : {'ok' if jb.is_file() else 'missing'} ({jb})")
        print(f"spec  : cache={SPEC_CACHE.exists()} local={LOCAL_SPEC.exists()}")
        return 0

    if args.install_jbang:
        if not pins.jbang:
            print("no jbang pin in .sdkmanrc", file=sys.stderr); return 2
        path = ensure_jbang(pins.jbang)
        print(f"jbang installed at {path}")

    if args.fetch_spec:
        path = fetch_openapi(force_refresh=args.force_refresh)
        print(f"spec: {path}")

    if not any([args.install_jbang, args.fetch_spec, args.check]):
        # Default: do both (pytest-equivalent bootstrap).
        if pins.jbang:
            ensure_jbang(pins.jbang)
        fetch_openapi(force_refresh=args.force_refresh)
        print("bootstrap complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
