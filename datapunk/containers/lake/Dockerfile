FROM datapunk-base-python:latest as builder

WORKDIR /app

# Copy service-specific files
COPY pyproject.toml poetry.lock ./
COPY src/ ./src/
COPY scripts/ ./scripts/

# Install dependencies
RUN poetry install --no-dev

# Runtime stage
FROM datapunk-base-python:latest as runtime

WORKDIR /app

# Copy built files from builder
COPY --from=builder /app/src ./src
COPY --from=builder /app/scripts ./scripts
COPY --from=builder ${PYSETUP_PATH}/.venv ${PYSETUP_PATH}/.venv

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./scripts/healthcheck.sh

# Create non-root user
RUN addgroup --system --gid 1001 datapunk && \
    adduser --system --uid 1001 lake && \
    chown -R lake:datapunk /app

USER lake

EXPOSE 8000

CMD ["poetry", "run", "python", "-m", "src.main"]