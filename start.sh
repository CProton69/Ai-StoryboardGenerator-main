#!/bin/bash

# Get the absolute path of the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =====================================================================
# OPTION 1: Open in separate Kitty terminal windows (Recommended)
# If you prefer separate windows, uncomment the two lines below and 
# comment out the "Single Terminal" section further down.
# =====================================================================
# kitty --title "Backend" --directory "$SCRIPT_DIR/backend" bash -c "source venv/bin/activate 2>/dev/null; uvicorn server:app --reload --port 8001; exec bash"
# kitty --title "Frontend" --directory "$SCRIPT_DIR/frontend" bash -c "yarn dev; exec bash"
# exit 0

# =====================================================================
# OPTION 2: Single Terminal Mode (Default)
# =====================================================================

# --- Start Backend ---
echo "🚀 Starting Backend..."
cd "$SCRIPT_DIR/backend"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run backend in the background
uvicorn server:app --reload --port 8001 &
BACKEND_PID=$!

# --- Start Frontend ---
echo "🎨 Starting Frontend..."
cd "$SCRIPT_DIR/frontend"

# React CRA dev server is pinned to PORT=3010 so it never collides
# with a separately-managed app that may already hold port 3000.
# This script manages ONLY:
#   - the React+CRA frontend on :3010
#   - the FastAPI backend on :8001
# Any other app on this host (e.g. the standalone vanilla Storyboard
# Studio app on :3000) is intentionally NOT touched here -- it runs
# independently via its own start command.
# Note: If your frontend uses 'start' instead of 'dev' in package.json,
# change 'yarn dev' to 'yarn start'.
PORT=3010 yarn dev &
FRONTEND_PID=$!

# --- Process Management ---
# This function ensures both processes are killed when you press Ctrl+C
cleanup() {
    echo -e "\n🛑 Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C (SIGINT) and SIGTERM to trigger the cleanup function
trap cleanup SIGINT SIGTERM

echo "✅ Both services are running. Press Ctrl+C to stop them."
wait