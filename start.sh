#!/bin/bash

# Start Redis in the background
echo "Starting Redis server..."
redis-server --daemonize yes

# Wait for Redis to be ready
until redis-cli ping; do
  echo "Waiting for Redis..."
  sleep 1
done

echo "Redis is up and running!"

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A app.core.celery_app worker --loglevel=info &

# Start the FastAPI application
echo "Starting FastAPI application (ENV: ${ENV:-production})..."
if [ "$ENV" = "development" ]; then
    echo "Running in development mode with live reload!"
    exec uvicorn main:app --host 0.0.0.0 --port 7860 --reload
else
    exec uvicorn main:app --host 0.0.0.0 --port 7860
fi
