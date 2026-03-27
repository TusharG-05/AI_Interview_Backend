#!/bin/bash
set -e

# ── Start Redis ───────────────────────────────────────────────────────────────
echo "Starting Redis server..."
redis-server \
    --daemonize yes \
    --port 6379 \
    --bind 127.0.0.1 \
    --pidfile /tmp/redis.pid \
    --dir /tmp \
    --protected-mode no

# Wait for Redis to be ready (max 30 s)
MAX_WAIT=30
WAITED=0
until redis-cli ping 2>/dev/null | grep -q PONG; do
    if [ "$WAITED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: Redis did not start within ${MAX_WAIT}s. Exiting."
        exit 1
    fi
    echo "Waiting for Redis... (${WAITED}s)"
    sleep 1
    WAITED=$((WAITED + 1))
done
echo "Redis is up and running!"

# ── Start Celery worker ───────────────────────────────────────────────────────
echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info &
CELERY_PID=$!
echo "Celery worker started (PID: $CELERY_PID)"

# ── Start FastAPI ─────────────────────────────────────────────────────────────
echo "Starting FastAPI application (ENV: ${ENV:-production})..."
if [ "${ENV}" = "development" ]; then
    echo "Running in development mode with live reload!"
    exec uvicorn app.server:app --host 0.0.0.0 --port 7860 --reload
else
    exec uvicorn app.server:app --host 0.0.0.0 --port 7860 --workers 1
fi
