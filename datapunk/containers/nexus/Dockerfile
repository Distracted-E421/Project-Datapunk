# Base builder stage for compiling dependencies
FROM datapunk-base-python:dev as builder

WORKDIR /app

# Run as non-root user for security
USER app

# NOTE: Files are copied with specific ownership to maintain least privilege principle
# Copy only necessary files for dependency installation
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install production dependencies only
# TODO: Consider using poetry.lock hash verification for supply chain security
RUN poetry install --no-dev

# Development stage with additional tooling and debug capabilities
FROM datapunk-base-python:dev as development

WORKDIR /app

USER app

# Copy all files needed for development environment
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install all dependencies including development tools
RUN poetry install

# Configure development environment
# NOTE: PYTHONPATH ensures proper module resolution for local development
ENV PYTHONPATH=/app/src
ENV DEBUG=1
ENV ENVIRONMENT=development

# Expose port for remote debugging
# FIXME: Consider making debug port configurable via environment variable
EXPOSE 5680

# Production runtime stage optimized for minimal size
FROM datapunk-base-python:dev as runtime

WORKDIR /app

USER app

# Copy only necessary files from builder stage
# This reduces the final image size by excluding development dependencies
COPY --chown=app:datapunk --from=builder /app/src ./src
COPY --chown=app:datapunk --from=builder /app/scripts ./scripts
COPY --chown=app:datapunk --from=builder ${PYSETUP_PATH}/.venv ${PYSETUP_PATH}/.venv

# Configure health monitoring
# NOTE: Interval and timeout values chosen based on expected response times
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ./scripts/healthcheck.sh

# Expose API gateway port
# TODO: Make port configurable via environment variable
EXPOSE 8002

# Start the Nexus Gateway service
CMD ["poetry", "run", "python", "-m", "src.main"]
