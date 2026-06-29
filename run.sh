#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Kill any existing instances
pkill -f "uvicorn app.main:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
sleep 1

source venv/bin/activate

echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:5173"
echo "Press Ctrl+C to stop both."
echo ""

# Start backend in background, frontend in foreground
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

cd frontend
npm run dev &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
