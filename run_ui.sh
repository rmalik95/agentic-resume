#!/usr/bin/env bash
# Launch the ResumAI web UI — builds the frontend if needed, then starts FastAPI.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Build frontend if dist/ is missing or older than src/
UI_DIR="$SCRIPT_DIR/ui"
if [ ! -d "$UI_DIR/dist" ] || [ "$UI_DIR/src" -nt "$UI_DIR/dist" ]; then
  echo "Building frontend..."
  (cd "$UI_DIR" && npm install --silent && npm run build)
  echo "Frontend build complete."
fi

# Activate Python venv if present
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

echo "Starting ResumAI server at http://127.0.0.1:8000"
exec uvicorn ui_server:app --host 127.0.0.1 --port 8000 --reload
