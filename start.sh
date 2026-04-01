#!/bin/bash
set -e

# --- Internal Infrastructure ---
export PYTHONUNBUFFERED=TRUE
export PYTHONPATH=$PYTHONPATH:.

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# ── Start Redis (Only if not provided externally) ───────────────────────────
# On Render/Managed environments, REDIS_URL is provided. On HF, we start local.
if [ -z "$REDIS_URL" ] || [[ "$REDIS_URL" == *"127.0.0.1"* ]] || [[ "$REDIS_URL" == *"localhost"* ]]; then
    echo "🚀 Starting local Redis server..."
    redis-server \
        --daemonize yes \
        --port 6379 \
        --bind 127.0.0.1 \
        --pidfile /tmp/redis.pid \
        --dir /tmp \
        --maxmemory 256mb \
        --maxmemory-policy allkeys-lru \
        --protected-mode no || { echo "❌ Redis failed to start"; exit 1; }

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
    echo "Local Redis is up and running!"
fi

# ── Start Celery worker and Beat (Only for environments that support background processes) ───────────────────────────────────────────────────────
if [ -z "$RENDER" ] && [ -z "$SPACE_ID" ]; then
    echo "Starting Celery worker..."
    celery -A app.core.celery_app worker --loglevel=info > /tmp/celery.log 2>&1 &
    CELERY_WORKER_PID=$!
    echo "Celery worker started (PID: $CELERY_WORKER_PID)"

    echo "Starting Celery Beat scheduler..."
    celery -A app.core.celery_app beat --loglevel=info > /tmp/celery-beat.log 2>&1 &
    CELERY_BEAT_PID=$!
    echo "Celery Beat started (PID: $CELERY_BEAT_PID)"
else
    echo "Cloud environment detected (RENDER or SPACE_ID). Skipping Celery background processes."
    echo "Use external cron services to call /api/admin/system/expire-interviews endpoint for expiration."
fi

# ── Start FastAPI ─────────────────────────────────────────────────────────────
echo "Starting FastAPI application (ENV: ${ENV:-production})..."
if [ "${ENV}" = "development" ]; then
    echo "Running in development mode with live reload!"
    exec uvicorn app.server:app --host 0.0.0.0 --port "${PORT:-7860}" --reload
else
    exec uvicorn app.server:app --host 0.0.0.0 --port "${PORT:-7860}" --workers 1
fi
