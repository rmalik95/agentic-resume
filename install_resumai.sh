#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/4] Checking prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 is required but was not found on PATH."
  exit 1
fi

echo "[2/4] Preparing virtual environment..."
if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

echo "[3/4] Installing Python dependencies..."
"$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
"$PYTHON_BIN" -m pip install -r "$SCRIPT_DIR/requirements.txt" >/dev/null

echo "[4/4] Preparing local config..."
if [[ ! -f "$SCRIPT_DIR/.env" && -f "$SCRIPT_DIR/.env.example" ]]; then
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "Created .env from .env.example"
fi

if [[ -f "$SCRIPT_DIR/package.json" ]] && command -v npm >/dev/null 2>&1; then
  echo "Installing Context Hub tooling (npm install)..."
  npm install >/dev/null
fi

echo "Install complete."
