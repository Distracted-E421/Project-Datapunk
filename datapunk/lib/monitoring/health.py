from typing import Dict, List, Optional
from enum import Enum
import asyncio
import aiohttp
import structlog
from ..tracing import trace_method

logger = structlog.get_logger()

"""
Health Check System for Datapunk's Microservices Architecture

This module implements a flexible health check system designed to monitor
the status of various dependencies and services within the Datapunk ecosystem.
It provides real-time insights into system health, enabling proactive
maintenance and rapid issue resolution.

Key Features:
- Configurable dependency checks
- Aggregated health status reporting
- Integration with tracing for detailed diagnostics
- Support for degraded states

Design Philosophy:
- Prioritize early detection of issues
- Provide granular health information
- Support graceful degradation of services
- Enable easy integration with monitoring systems

NOTE: This implementation assumes HTTP-based health checks
TODO: Add support for custom health check protocols
"""

class HealthStatus(Enum):
    """
    Possible health states for services and dependencies.
    
    Why Three States:
    HEALTHY: Fully operational
    DEGRADED: Functioning with reduced capabilities
    UNHEALTHY: Critical failure, immediate attention required
    
    NOTE: DEGRADED allows for nuanced reporting of partial failures
    """
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    """
    Manages health checks for a service and its dependencies.
    
    Key Capabilities:
    - Configurable dependency checks
    - Aggregated health status calculation
    - Detailed health reporting
    - Integration with tracing for diagnostics
    
    FIXME: Consider adding support for async health check execution
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: List[Dict] = []
        self._status = HealthStatus.HEALTHY
        
    async def check_dependency(self, name: str, url: str, timeout: float = 5.0) -> Dict:
        """
        Performs health check on a single dependency.
        
        Design Decisions:
        - Uses HTTP GET for simplicity and broad compatibility
        - Implements timeout to prevent hanging on unresponsive services
        - Logs errors for debugging without exposing details in response
        
        NOTE: Assumes 2xx status codes indicate health
        TODO: Add support for custom health criteria per dependency
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    is_healthy = 200 <= response.status < 300
                    return {
                        "name": name,
                        "status": HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
                        "message": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error("health_check_failed", 
                        service=self.service_name,
                        dependency=name,
                        error=str(e))
            return {
                "name": name,
                "status": HealthStatus.UNHEALTHY,
                "message": str(e)
            }

    @trace_method("check_health")
    async def check_health(self) -> Dict:
        """
        Executes all configured health checks and aggregates results.
        
        Aggregation Logic:
        - Any UNHEALTHY dependency results in overall UNHEALTHY status
        - Any DEGRADED dependency (with no UNHEALTHY) results in DEGRADED status
        - All HEALTHY dependencies required for overall HEALTHY status
        
        NOTE: This method is traced for performance monitoring
        """
        with self.tracer.start_span("run_health_checks") as span:
            span.set_attribute("total_checks", len(self.checks))
            
            results = await asyncio.gather(*[
                self.check_dependency(**check) for check in self.checks
            ])
            
            # Determine overall status
            unhealthy = sum(1 for r in results if r["status"] == HealthStatus.UNHEALTHY)
            degraded = sum(1 for r in results if r["status"] == HealthStatus.DEGRADED)
            
            span.set_attribute("unhealthy_count", unhealthy)
            span.set_attribute("degraded_count", degraded)
            
            if unhealthy > 0:
                status = HealthStatus.UNHEALTHY
            elif degraded > 0:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.HEALTHY
                
            self._status = status
            span.set_attribute("final_status", status.value)
            
            return {
                "service": self.service_name,
                "status": status.value,
                "checks": results,
                "timestamp": structlog.get_timestamp()
            }

    def add_check(self, name: str, url: str):
        """
        Adds a new dependency to the health check system.
        
        Why This Matters:
        - Allows dynamic configuration of health checks
        - Enables easy addition of new dependencies as system evolves
        
        WARNING: Adding too many checks may impact performance
        """
        self.checks.append({"name": name, "url": url})

    @property
    def status(self) -> HealthStatus:
        """
        Provides current overall health status.
        
        Why a Property:
        - Offers a simple interface for quick status checks
        - Reflects the most recent health check result
        
        NOTE: This does not trigger a new health check
        """
        return self._status 