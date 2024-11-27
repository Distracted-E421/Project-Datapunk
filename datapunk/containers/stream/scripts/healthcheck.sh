#!/bin/sh

# Stream Service Health Check Script
#
# This script performs a basic health check for the Stream service container.
# It is used by Docker's HEALTHCHECK instruction to monitor container health
# and trigger orchestration decisions.
#
# NOTE: Exit codes are used by Docker to determine container health:
# - 0: healthy
# - 1: unhealthy
#
# TODO: Add additional checks for dependent services
# TODO: Implement more sophisticated health metrics
# FIXME: Consider adding timeout parameter

# Check Stream service's HTTP health endpoint
# Uses -f flag to fail on HTTP errors (4xx/5xx)
curl -f http://localhost:8001/health || exit 1 