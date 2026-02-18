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

# Copy clean application code (filtered by .dockerignore)
COPY . .

# Expose API Port
EXPOSE 7860

# Default Command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
