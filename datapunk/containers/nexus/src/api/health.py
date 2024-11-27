"""
Nexus Gateway Health Check Module

This module implements the health monitoring system for the Nexus Gateway service,
which acts as the central routing and authentication layer for the Datapunk platform.
It monitors critical infrastructure dependencies and reports their status.

NOTE: This endpoint is used by container orchestration systems and the service mesh
for service discovery and load balancing decisions.
"""

from fastapi import APIRouter, Response
from datapunk_shared.monitoring.health import HealthCheck, HealthStatus

router = APIRouter()
health_checker = HealthCheck("nexus")

# Register critical infrastructure dependencies
# TODO: Add timeout configurations for each service check
# TODO: Add custom health check logic for each service
health_checker.add_check("redis", "http://redis:6379/health")  # Cache layer status
health_checker.add_check("postgres", "http://postgres:5432/health")  # Storage layer status
health_checker.add_check("rabbitmq", "http://rabbitmq:15672/health")  # Message queue status

@router.get("/health")
async def health_check(response: Response):
    """
    Performs comprehensive health check of the Nexus Gateway and its dependencies.
    
    Returns a detailed health status that influences load balancing and failover decisions.
    Uses HTTP status codes to indicate service health:
    - 200: Healthy or Degraded (allows traffic but may need attention)
    - 503: Unhealthy (service should not receive traffic)
    
    NOTE: Degraded status returns 200 to maintain partial system availability
    while alerting monitoring systems of potential issues.
    """
    result = await health_checker.check_health()
    
    # Set response status based on service health state
    # FIXME: Consider if degraded services should use 207 Multi-Status instead
    if result["status"] == HealthStatus.UNHEALTHY.value:
        response.status_code = 503  # Service Unavailable
    elif result["status"] == HealthStatus.DEGRADED.value:
        response.status_code = 200  # OK, but needs attention
    else:
        response.status_code = 200  # Fully healthy
        
    return result 