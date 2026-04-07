#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

log() {
  echo "[ResumAI setup] $*"
}

warn() {
  echo "[ResumAI setup][WARN] $*"
}

fail() {
  echo "[ResumAI setup][ERROR] $*" >&2
  exit 1
}

check_python_version() {
  local pybin="$1"
  "$pybin" - <<'PY'
import sys
if sys.version_info < (3, 11):
    raise SystemExit(1)
PY
}

OS_NAME="$(uname -s || echo unknown)"
case "$OS_NAME" in
  Darwin|Linux) ;;
  *)
    warn "Detected OS '$OS_NAME'. This installer is validated on macOS/Linux."
    ;;
esac

log "Step 1/6: Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
  fail "python3 is required but was not found on PATH."
fi
if ! check_python_version python3; then
  fail "Python 3.11+ is required. Found: $(python3 --version 2>&1)"
fi

log "Step 2/6: Preparing virtual environment..."
if [[ ! -d ".venv" ]]; then
  log "Creating .venv"
  python3 -m venv .venv
fi

PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
PIP_BIN="$SCRIPT_DIR/.venv/bin/pip"

log "Step 3/6: Installing Python dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip
"$PIP_BIN" install -r "$SCRIPT_DIR/requirements.txt"

log "Step 4/6: Installing Context Hub tooling (optional but recommended)..."
if [[ -f "$SCRIPT_DIR/package.json" ]]; then
  if command -v npm >/dev/null 2>&1; then
    npm install
  else
    warn "npm not found. Skipping root npm install."
  fi
fi

log "Step 5/6: Installing UI dependencies (optional, needed for web UI only)..."
if [[ -f "$SCRIPT_DIR/ui/package.json" ]]; then
  if command -v npm >/dev/null 2>&1; then
    (
      cd "$SCRIPT_DIR/ui"
      npm install
    )
  else
    warn "npm not found. Skipping ui npm install."
  fi
fi

log "Step 6/6: Environment file check..."
if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
  warn ".env not found. Create it manually from .env.example before running pipeline:"
  warn "  cp .env.example .env"
  warn "Then set ANTHROPIC_API_KEY in .env"
else
  log ".env file found."
fi

log "Install complete."
