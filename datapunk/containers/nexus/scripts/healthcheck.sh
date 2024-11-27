#!/bin/sh

# Docker health check script for Nexus service
# Used by container orchestration to monitor service health
# NOTE: Requires curl to be installed in the container
# TODO: Add timeout configuration
# FIXME: Add retry logic for transient failures

# Check Nexus service health endpoint
# -f: Fail silently (no output) on HTTP errors
# Exit code 1 signals unhealthy state to Docker
curl -f http://localhost:8002/health || exit 1 