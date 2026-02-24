# --- Optimized Runtime ---
# Inherits from the local base containing heavy ML libs in /opt/venv
FROM interview-base:latest

# Runtime environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/venv/bin:$PATH"
ENV CUDA_VISIBLE_DEVICES=-1
ENV TF_CPP_MIN_LOG_LEVEL=2

# Clean inherited /app bloat from base image before copying fresh code
WORKDIR /app
RUN rm -rf /app/*

# Only install application-level changes
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Install Redis server for Celery
USER root
RUN apt-get update && apt-get install -y redis-server && rm -rf /var/lib/apt/lists/*
USER user

# Copy clean application code (filtered by .dockerignore)
COPY . .

# Ensure start script is executable
RUN chmod +x start.sh

# Expose API Port
EXPOSE 7860

# Default Command
CMD ["./start.sh"]
