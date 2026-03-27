# ============================================================
# AI Interview Backend - Render Optimized Dockerfile
# Optimized for cloud deployment (CPU-only, stable builds)
# ============================================================

# Use official Python slim image as base
FROM python:3.11-slim-bookworm

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (Native libs for CV, ML and Audio)
# Replaced libgl1-mesa-glx with libgl1 (modern Debian replacement)
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

# Set working directory
WORKDIR /app

# Ensure /app/models exists and is writable for model downloads
RUN mkdir -p /app/models && chmod 777 /app/models

# Use the stabilized production requirements established for Hugging Face
# This prevents build timeouts and native dependency failures on Render
COPY requirements-hf-final.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-hf-final.txt

# Copy application code
COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# Render usually uses port 10000, but we'll stick to 7860 to match HF 
# and the user can map it in Render's dashboard.
EXPOSE 7860

# Default Command
CMD ["./start.sh"]
