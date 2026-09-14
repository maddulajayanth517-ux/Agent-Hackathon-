#!/bin/sh
# Runs both halves of the combined single-container deployment:
#   - the built Next.js frontend, on an internal-only port (not exposed)
#   - the FastAPI backend, bound to $PORT, which proxies anything that
#     isn't one of its own API routes to the frontend above (see
#     FRONTEND_PROXY_URL / API_PREFIX in backend/app/main.py)
set -e

cd /app/web
PORT=3000 HOSTNAME=127.0.0.1 node server.js &
FRONTEND_PID=$!

trap 'kill $FRONTEND_PID 2>/dev/null' EXIT INT TERM

cd /app/backend
python -m alembic upgrade head

exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
