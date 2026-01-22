#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

echo "Installing dependencies..."
. .venv/bin/activate
python -m pip install -r requirements.txt

echo "Starting app..."
python -m app
