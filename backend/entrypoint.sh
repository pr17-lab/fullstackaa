#!/bin/sh
# entrypoint.sh — waits for Postgres, runs Alembic migrations, starts Uvicorn.
# Using /bin/sh (not bash) for Alpine/Debian-slim compatibility.

set -e

echo "=== Student Academic Tracker — Startup ==="

# ---------------------------------------------------------------------------
# 1. Wait for PostgreSQL to be ready
#    We parse the DATABASE_URL to extract host and port.
# ---------------------------------------------------------------------------
DB_URL="${DATABASE_URL:-}"

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL is not set. Aborting."
  exit 1
fi

# Extract host (between @ and : or @)
DB_HOST=$(echo "$DB_URL" | sed -E 's|.*@([^:/]+)[:/].*|\1|')
DB_PORT=$(echo "$DB_URL" | sed -E 's|.*@[^:]+:([0-9]+)/.*|\1|')
DB_PORT="${DB_PORT:-5432}"

echo "Waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."

MAX_RETRIES=30
RETRY_INTERVAL=2
retries=0

until python -c "
import socket, sys
try:
    s = socket.create_connection(('${DB_HOST}', ${DB_PORT}), timeout=2)
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
