from typing import Dict, List, Optional
import structlog
import asyncio
from datetime import datetime, timedelta
from .health_check_types import (
    HealthStatus,
    HealthCheckResult,
    BaseHealthCheck
)

logger = structlog.get_logger()

class HealthAggregator:
    """Aggregates and manages multiple health checks."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.checks: Dict[str, BaseHealthCheck] = {}
        self.results_cache: Dict[str, HealthCheckResult] = {}
        self.cache_ttl = timedelta(seconds=30)
        self.logger = logger.bind(component="health_aggregator")
    
    def add_check(self, name: str, check: BaseHealthCheck) -> None:
        """Add a health check."""
        self.checks[name] = check
    
    def remove_check(self, name: str) -> None:
        """Remove a health check."""
        self.checks.pop(name, None)
        self.results_cache.pop(name, None)
    
    async def check_health(self, use_cache: bool = True) -> Dict:
        """Run all health checks and aggregate results."""
        results = {}
        overall_status = HealthStatus.HEALTHY
        
        try:
            # Run all checks concurrently
            check_tasks = []
            for name, check in self.checks.items():
                if use_cache and name in self.results_cache:
                    cached = self.results_cache[name]
                    if datetime.utcnow() - cached.timestamp < self.cache_ttl:
                        results[name] = cached
                        continue
                
                check_tasks.append(self._run_check(name, check))
            
            if check_tasks:
                await asyncio.gather(*check_tasks)
            
            # Combine cached and new results
            all_results = {**self.results_cache, **results}
            
            # Determine overall status
            if any(r.status == HealthStatus.UNHEALTHY for r in all_results.values()):
                overall_status = HealthStatus.UNHEALTHY
            elif any(r.status == HealthStatus.DEGRADED for r in all_results.values()):
                overall_status = HealthStatus.DEGRADED
            
            return {
                "service": self.service_name,
                "status": overall_status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "checks": {
                    name: {
                        "status": result.status.value,
                        "message": result.message,
                        "details": result.details,
                        "timestamp": result.timestamp.isoformat()
                    }
                    for name, result in all_results.items()
                }
            }
            
        except Exception as e:
            self.logger.error("health_check_aggregation_failed",
                            error=str(e))
            return {
                "service": self.service_name,
                "status": HealthStatus.UNHEALTHY.value,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def _run_check(self, name: str, check: BaseHealthCheck) -> None:
        """Run a single health check and cache result."""
        try:
            result = await check.check()
            self.results_cache[name] = result
        except Exception as e:
            self.logger.error("health_check_failed",
                            check=name,
                            error=str(e))
            self.results_cache[name] = HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {str(e)}"
            ) 