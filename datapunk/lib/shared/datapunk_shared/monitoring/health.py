from typing import Dict, List, Optional
from enum import Enum
import asyncio
import aiohttp
import structlog

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

    async def check_health(self) -> Dict:
        """Run all health checks and return aggregated status."""
        results = await asyncio.gather(*[
            self.check_dependency(**check) for check in self.checks
        ])
        
        # Determine overall status
        if any(r["status"] == HealthStatus.UNHEALTHY for r in results):
            status = HealthStatus.UNHEALTHY
        elif any(r["status"] == HealthStatus.DEGRADED for r in results):
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
            
        self._status = status
        
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