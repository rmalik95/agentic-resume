#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SKIP_INSTALL=false
SHOW_HELP=false
PASSTHROUGH_ARGS=()

for arg in "$@"; do
  case "$arg" in
    --skip-install)
      SKIP_INSTALL=true
      ;;
    -h|--help)
      SHOW_HELP=true
      PASSTHROUGH_ARGS+=("$arg")
      ;;
    *)
      PASSTHROUGH_ARGS+=("$arg")
      ;;
  esac
done

if [[ "$SKIP_INSTALL" == false ]]; then
  bash "$SCRIPT_DIR/install_resumai.sh"
fi

PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "ERROR: Python environment is missing at .venv. Run ./install_resumai.sh first."
  exit 1
fi

if [[ "$SHOW_HELP" == false ]]; then
  if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
    echo "ERROR: .env file not found."
    echo "Create it with: cp .env.example .env"
    echo "Then set ANTHROPIC_API_KEY in .env and rerun."
    exit 1
  fi

  if ! grep -Eq '^ANTHROPIC_API_KEY=.+$' "$SCRIPT_DIR/.env"; then
    echo "ERROR: ANTHROPIC_API_KEY is missing in .env"
    echo "Set it in $SCRIPT_DIR/.env and rerun."
    exit 1
  fi
fi

if [[ "$SHOW_HELP" == true ]]; then
  exec "$PYTHON_BIN" "$SCRIPT_DIR/main.py" "${PASSTHROUGH_ARGS[@]}"
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/main.py" --no-notify "${PASSTHROUGH_ARGS[@]}"