#!/bin/sh
# entrypoint.sh — waits for Postgres, runs Alembic migrations, starts Uvicorn.
# Using /bin/sh (not bash) for Alpine/Debian-slim compatibility.

set -e

echo "=== Student Academic Tracker — Startup ==="

# ---------------------------------------------------------------------------
# 1. Wait for PostgreSQL to be ready
#    Uses Python's urllib.parse to robustly extract hostname and port
#    for both local Postgres (localhost:5432) and Neon pooled URLs.
# ---------------------------------------------------------------------------
DB_URL="${DATABASE_URL:-}"

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL is not set. Aborting."
  exit 1
fi

echo "Waiting for PostgreSQL connection..."

MAX_RETRIES=30
RETRY_INTERVAL=2
retries=0

until python -c "
import sys, socket
from urllib.parse import urlparse

url = '''${DB_URL}'''
try:
    parsed = urlparse(url)
    host = parsed.hostname or 'localhost'
    port = parsed.port or 5432
    s = socket.create_connection((host, port), timeout=3)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  retries=$((retries + 1))
  if [ "$retries" -ge "$MAX_RETRIES" ]; then
    echo "ERROR: PostgreSQL did not become available after $((MAX_RETRIES * RETRY_INTERVAL))s. Aborting."
    exit 1
  fi
  echo "  Still waiting... (attempt ${retries}/${MAX_RETRIES})"
  sleep "$RETRY_INTERVAL"
done

echo "PostgreSQL is ready."

# ---------------------------------------------------------------------------
# 2. Run Alembic migrations
# ---------------------------------------------------------------------------
echo "Running database migrations ..."
alembic upgrade head
echo "Migrations complete."

# ---------------------------------------------------------------------------
# 3. Start Uvicorn
# ---------------------------------------------------------------------------
HOST="${APP_HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${UVICORN_WORKERS:-1}"

echo "Starting Uvicorn on ${HOST}:${PORT} (workers=${WORKERS}) ..."
exec uvicorn app.main:app \
  --host "$HOST" \
  --port "$PORT" \
  --workers "$WORKERS" \
  --proxy-headers \
  --forwarded-allow-ips='*'
