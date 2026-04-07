#!/bin/bash
set -e

# --- Internal Infrastructure ---
export PYTHONUNBUFFERED=TRUE
export PYTHONPATH=$PYTHONPATH:.

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# ── Start Redis (Only if not provided externally and not disabled) ───────────
# On Render/Managed environments, REDIS_URL is provided. On HF, we start local.
if [[ "$DISABLE_REDIS" == "true" ]]; then
    echo "⭕ Redis is DISABLED via environment variable."
elif [ -z "$REDIS_URL" ] || [[ "$REDIS_URL" == *"127.0.0.1"* ]] || [[ "$REDIS_URL" == *"localhost"* ]]; then
    echo "🚀 Starting local Redis server..."
    # On very low RAM (Render 512MB), starting Redis can cause OOM.
    # We use aggressive memory limits for local Redis.
    redis-server \
        --daemonize yes \
        --port 6379 \
        --bind 127.0.0.1 \
        --pidfile /tmp/redis.pid \
        --dir /tmp \
        --maxmemory 16mb \
        --maxmemory-policy allkeys-lru \
        --protected-mode no || { echo "❌ Redis failed to start"; }

    # Wait for Redis to be ready (max 10 s - faster fail for Render)
    MAX_WAIT=10
    WAITED=0
    until redis-cli ping 2>/dev/null | grep -q PONG; do
        if [ "$WAITED" -ge "$MAX_WAIT" ]; then
            echo "WARNING: Redis did not start within ${MAX_WAIT}s. Continuing without Redis."
            break
        fi
        echo "Waiting for Redis... (${WAITED}s)"
        sleep 1
        WAITED=$((WAITED + 1))
    done
    echo "Local Redis status check complete."
else
    echo "🔗 Using external Redis at: $REDIS_URL"
fi

# ── Start Celery worker and Beat (Only if enabled and environment supports background processes) ─────────
# In Orchestrator mode (Render), we use FastAPI BackgroundTasks directly 
# to save memory. Disable celery worker by default on Render / Spaces.
if [[ "$DISABLE_CELERY" == "true" ]] || [[ "$ENV_MODE" == "orchestrator" ]] || [ -n "$RENDER" ] || [ -n "$SPACE_ID" ]; then
    echo "⭕ Celery worker and Beat are DISABLED/Skipped (Orchestrator Mode or Cloud Environment detected)."
    echo "Use external cron services to call /api/admin/system/expire-interviews endpoint for expiration."
else
    echo "Starting Celery worker..."
    celery -A app.core.celery_app worker --loglevel=info --concurrency=1 > /tmp/celery.log 2>&1 &
    CELERY_WORKER_PID=$!
    echo "Celery worker started (PID: $CELERY_WORKER_PID)"

    echo "Starting Celery Beat scheduler..."
    celery -A app.core.celery_app beat --loglevel=info > /tmp/celery-beat.log 2>&1 &
    CELERY_BEAT_PID=$!
    echo "Celery Beat started (PID: $CELERY_BEAT_PID)"
fi

# ── Start FastAPI ─────────────────────────────────────────────────────────────
echo "Starting FastAPI application (ENV: ${ENV:-production}, MODE: ${ENV_MODE:-Standard})..."
if [ "${ENV}" = "development" ]; then
    echo "Running in development mode with live reload!"
    exec uvicorn app.server:app --host 0.0.0.0 --port "${PORT:-7860}" --reload
else
    # For Render/Production: prioritize PORT env var (usually provided by platform)
    # Using --workers 1 is CRITICAL for 512MB RAM limits to avoid OOM
    exec uvicorn app.server:app --host 0.0.0.0 --port "${PORT:-7860}" --workers 1 --timeout-keep-alive 5
fi
