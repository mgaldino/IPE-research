#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$ROOT_DIR/.venv"

if [ ! -d "$VENV_PATH" ]; then
  echo "Virtualenv not found at $VENV_PATH"
  echo "Create it first: python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

# shellcheck disable=SC1091
. "$VENV_PATH/bin/activate"

python -m app --host 127.0.0.1 --port 8001 &
APP_PID=$!

sleep 1
open "http://127.0.0.1:8001/"

wait "$APP_PID"
