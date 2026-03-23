#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

bash "$SCRIPT_DIR/install_resumai.sh"

PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"

show_help=false
for arg in "$@"; do
  if [[ "$arg" == "-h" || "$arg" == "--help" ]]; then
    show_help=true
    break
  fi
done

if [[ "$show_help" == false ]]; then
  if [[ -f "$SCRIPT_DIR/.env" ]] && ! grep -Eq '^ANTHROPIC_API_KEY=.+$' "$SCRIPT_DIR/.env"; then
    echo "ERROR: ANTHROPIC_API_KEY is missing in .env"
    echo "Set it in $SCRIPT_DIR/.env and rerun."
    exit 1
  fi
fi

exec "$PYTHON_BIN" "$SCRIPT_DIR/main.py" --no-notify "$@"