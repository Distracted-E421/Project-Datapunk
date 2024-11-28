# Lake Service Container
# Part of Core Services layer (see sys-arch.mmd)
# Handles data sovereignty and storage management

# Build stage for optimized dependencies
# NOTE: Using multi-stage build to minimize final image size
FROM datapunk-base-python:dev as builder

WORKDIR /app

# Run as non-root user for security
# NOTE: User 'app' is created in base image
USER app

# Copy only necessary files for dependency installation
# FIXME: Consider using .dockerignore for better control
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install production dependencies only
# TODO: Add dependency audit step
RUN poetry install --no-dev

# Development stage with additional tools
# NOTE: Separate from production for debugging capabilities
FROM datapunk-base-python:dev as development

WORKDIR /app

USER app

# Copy service files
# TODO: Add file integrity checks
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install all dependencies including development tools
# TODO: Add development-specific health checks
# TODO: Add debugging tools configuration
# TODO: Add profiling tools setup
# TODO: Add local development SSL certificates
# TODO: Add development-specific logging
# TODO: Add hot reload capability

# Set up development environment
ENV PYTHONPATH=/app/src
ENV DEBUG=1
ENV ENVIRONMENT=development

# Set up debugger port
EXPOSE 5678

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

EXPOSE 8000

CMD ["poetry", "run", "python", "-m", "src.main"]