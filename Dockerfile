# Base Image: Python 3.11 Slim (Debian Bookworm)
FROM python:3.11-slim-bookworm

# System Dependencies
# libav* -> For PyAV/aiortc header compilation (if wheel missing) or linking
# libgl1/libglib2.0 -> For OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependency Layer
COPY requirements.txt .
# Install without cache to avoid corrupted wheels
# Note: We can now use strict av versions if we want, or let aiortc decide
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application Layer
COPY . .

# Expose API Port
EXPOSE 8000

# Force TensorFlow to use CPU (Prevents CUDA/Driver Segfaults)
ENV CUDA_VISIBLE_DEVICES=-1
ENV TF_CPP_MIN_LOG_LEVEL=2

# Default Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
