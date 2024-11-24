FROM datapunk-base-python:dev as builder

WORKDIR /app

USER app

# Copy service-specific files
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install dependencies
RUN poetry install --no-dev

# Development stage
FROM datapunk-base-python:dev as development

WORKDIR /app

USER app

# Copy service-specific files
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install all dependencies including dev dependencies
RUN poetry install

# Set up development environment
ENV PYTHONPATH=/app/src
ENV DEBUG=1
ENV ENVIRONMENT=development

# Set up debugger port
EXPOSE 5680

# Runtime stage
FROM datapunk-base-python:dev as runtime

WORKDIR /app

USER app

# Copy built files from builder
COPY --chown=app:datapunk --from=builder /app/src ./src
COPY --chown=app:datapunk --from=builder /app/scripts ./scripts
COPY --chown=app:datapunk --from=builder ${PYSETUP_PATH}/.venv ${PYSETUP_PATH}/.venv

# Set up healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./scripts/healthcheck.sh

EXPOSE 8002

CMD ["poetry", "run", "python", "-m", "src.main"]
