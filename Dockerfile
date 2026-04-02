# Hugging Face Spaces Dockerfile (v1 & v2)
# Uses unified requirements.txt — includes core ML + app dependencies

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
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

# Create a non-root user (Hugging Face requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONPATH=/app \
    ENV=production

# ── Install Python dependencies ──────────────────────────────────────────────
# Copy unified requirements first to leverage Docker layer cache
COPY --chown=user requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application code ────────────────────────────────────────────────────
COPY --chown=user . /app

# ── Pre-download ML models at build time (avoids cold-start latency) ─────────
RUN chmod +x /app/start.sh && \
    mkdir -p /app/app/assets && \
    wget -q -O /app/app/assets/face_landmarker.task \
        https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task && \
    python3 -c "from deepface import DeepFace; DeepFace.build_model('SFace')" || true

# Expose port (Hugging Face Spaces default)
EXPOSE 7860

CMD ["/app/start.sh"]
