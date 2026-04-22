#!/usr/bin/env bash
# Run the test suite against the ComfyUI virtualenv.
# Searches (in order):
#   ./venv, ./.venv                   — local to this custom node
#   ../venv, ../.venv                 — parent folder
#   ../../venv, ../../.venv           — ComfyUI root (typical layout)
# Override with COMFYUI_VENV=/path/to/venv.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

find_venv() {
  if [[ -n "${COMFYUI_VENV:-}" ]]; then
    echo "$COMFYUI_VENV"; return 0
  fi
  for c in ./venv ./.venv ../venv ../.venv ../../venv ../../.venv; do
    if [[ -x "$c/bin/python" || -x "$c/bin/python3" || -x "$c/Scripts/python.exe" ]]; then
      (cd "$c" && pwd); return 0
    fi
  done
  return 1
}

VENV="$(find_venv)" || {
  echo "error: no ComfyUI venv found. Set COMFYUI_VENV or create one of:" >&2
  echo "  ./venv, ./.venv, ../venv, ../.venv, ../../venv, ../../.venv" >&2
  exit 1
}
PY="$VENV/bin/python"
[[ -x "$PY" ]] || PY="$VENV/bin/python3"
[[ -x "$PY" ]] || PY="$VENV/Scripts/python.exe"
echo "[run-tests] using venv: $VENV"
echo "[run-tests] python   : $PY"

# Load SDKMAN (for jbang) if present; the conftest autostart needs it.
if [[ -f "$HOME/.sdkman/bin/sdkman-init.sh" ]]; then
  set +u
  # shellcheck disable=SC1091
  source "$HOME/.sdkman/bin/sdkman-init.sh"
  set -u
fi

# Install test-only deps if missing. Node runtime deps (requests, numpy,
# Pillow) should already be in the ComfyUI venv.
"$PY" -m pip install -q pytest wiremock 2>/dev/null || true

exec "$PY" -m pytest "$@"
