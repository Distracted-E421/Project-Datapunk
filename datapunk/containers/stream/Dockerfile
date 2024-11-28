# Stream Service Container Configuration
# Handles real-time event processing and stream analytics
# See: sys-arch.mmd CoreServices->StreamService->EventProcessing

# NOTE: Base image provides core Python environment and security patches
# TODO: Add health check implementation
# TODO: Add resource limit configurations
# TODO: Add monitoring agent
# FIXME: Optimize layer caching strategy
FROM datapunk-base-python:dev as builder

WORKDIR /app

# Non-root user for security
# NOTE: User 'app' is created in base image
USER app

# Copy service-specific files
# NOTE: Ownership set to prevent permission issues
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install production dependencies only
# TODO: Add dependency audit step
RUN poetry install --no-dev

# Development stage with additional tools
# NOTE: Separate from production for smaller final image
FROM datapunk-base-python:dev as development

WORKDIR /app

USER app

# Copy service-specific files
# TODO: Add file integrity verification
COPY --chown=app:datapunk pyproject.toml poetry.lock ./
COPY --chown=app:datapunk src/ ./src/
COPY --chown=app:datapunk scripts/ ./scripts/

# Install all dependencies including development tools
RUN poetry install

# Set up development environment
ENV PYTHONPATH=/app/src
ENV DEBUG=1
ENV ENVIRONMENT=development

# Set up debugger port
EXPOSE 5679

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

EXPOSE 8001

CMD ["poetry", "run", "python", "-m", "src.main"]