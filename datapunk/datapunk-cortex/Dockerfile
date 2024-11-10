FROM python:3.11-slim AS datapunk-cortex-builder

# Install build dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        git \
        curl \
        gcc \
        python3-dev \
        libpq-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS datapunk-cortex

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built packages from builder
COPY --from=datapunk-cortex-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=datapunk-cortex-builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app
COPY ./src /app/src

# Create necessary directories
RUN mkdir -p /models /cache /var/log/datapunk/cortex

# Environment configuration
ENV PYTHONPATH=/app \
    MODEL_CACHE_SIZE=2GB \
    MAX_BATCH_SIZE=32

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]