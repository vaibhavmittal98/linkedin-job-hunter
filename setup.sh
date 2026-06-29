#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== Job Application Automator - Setup ==="

# Python backend
echo "[1/4] Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "[2/4] Installing Python dependencies..."
pip install -r requirements.txt -q

echo "[3/4] Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  Created .env from .env.example — fill in your API tokens later."
else
    echo "  .env already exists, skipping."
fi

echo "[4/4] Installing frontend dependencies..."
cd frontend
npm install --silent

cd ..
echo ""
echo "=== Setup complete! ==="
echo ""
echo "To start the app, run:"
echo "  ./run.sh"
