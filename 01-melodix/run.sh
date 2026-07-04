#!/bin/bash
# 01-melodix startup script

set -e

cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "  ╔══════════════════════════════╗"
echo "  ║   melodix  ·  01             ║"
echo "  ║   http://localhost:8000      ║"
echo "  ╚══════════════════════════════╝"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
