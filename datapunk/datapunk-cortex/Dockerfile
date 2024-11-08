FROM python:3.11-slim AS datapunk-cortex

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/cortex

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./src /app/cortex/src

# Create necessary directories
RUN mkdir -p /models /cache /var/log/datapunk/cortex

# Set environment variables
ENV PYTHONPATH=/app/cortex
ENV MODEL_CACHE_SIZE=2GB
ENV MAX_BATCH_SIZE=32

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]