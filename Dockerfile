# Render Orchestrator Dockerfile (High Performance, Low Memory)
# This container runs the FastAPI app WITHOUT heavy ML libraries.

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    git \
    wget \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Environment variables
ENV PYTHONUNBUFFERED=TRUE \
    PYTHONPATH=/app \
    ENV=production \
    RENDER=true \
    ENV_MODE=orchestrator

# ── Install Python dependencies (Orchestrator Mode) ─────────────────────────
# Use requirements-render.txt directly (keeps logs/source of truth explicit).
COPY requirements-render.txt /app/requirements-render.txt
RUN set -eux; \
    if [ -f /app/requirements.txt ]; then \
        echo "ERROR: unexpected /app/requirements.txt found during orchestrator dependency install"; \
        exit 1; \
    fi; \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-render.txt

# ── Copy application code ────────────────────────────────────────────────────
COPY . /app

# ── Skip ML model pre-download ──────────────────────────────────────────────
# In orchestrator mode, models are offloaded to Modal/HF API.
RUN chmod +x /app/start.sh

# Expose port (Render will provide PORT env var)
# Note: Render provides PORT env var dynamically, this is just documentation
EXPOSE 7860

CMD ["/app/start.sh"]
