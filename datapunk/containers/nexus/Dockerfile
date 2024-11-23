FROM datapunk-base-python:latest as builder

WORKDIR /app

# Copy service-specific files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY config/ ./config/

# Install dependencies
RUN poetry install --no-dev

# Runtime stage
FROM datapunk-base-python:latest as runtime

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/src ./src
COPY --from=builder /app/config ./config
COPY --from=builder ${PYSETUP_PATH}/.venv ${PYSETUP_PATH}/.venv

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Create non-root user
RUN addgroup --system --gid 1003 datapunk && \
    adduser --system --uid 1003 nexus && \
    chown -R nexus:datapunk /app

USER nexus

EXPOSE 8002

CMD ["poetry", "run", "python", "-m", "src.main"]
