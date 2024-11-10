FROM python:3.11 AS datapunk-stream-builder

# Install build dependencies
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        git \
        libpq-dev \
        pkg-config \
        protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS datapunk-stream

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y \
        libpq5 \
        protobuf-compiler \
    && rm -rf /var/lib/apt/lists/*

# Copy built packages from builder
COPY --from=datapunk-stream-builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=datapunk-stream-builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app
COPY ./src /app/src

RUN mkdir -p /cache /var/log/datapunk/stream

ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]