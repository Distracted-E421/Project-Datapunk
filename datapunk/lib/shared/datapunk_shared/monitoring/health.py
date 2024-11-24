from typing import Dict, List, Optional
from enum import Enum
import asyncio
import aiohttp
import structlog
from ..tracing import trace_method

logger = structlog.get_logger()

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheck:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: List[Dict] = []
        self._status = HealthStatus.HEALTHY
        
    async def check_dependency(self, name: str, url: str, timeout: float = 5.0) -> Dict:
        """Check health of a dependency service."""
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
        """Run all health checks and return aggregated status."""
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
        """Add a new dependency to check."""
        self.checks.append({"name": name, "url": url})

    @property
    def status(self) -> HealthStatus:
        return self._status 