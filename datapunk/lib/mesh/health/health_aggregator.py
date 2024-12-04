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

"""
Health Check Aggregator for Datapunk Service Mesh

This module aggregates health check results across service components:
- Combines multiple health check results
- Determines overall service health
- Provides caching for performance
- Supports concurrent check execution

The aggregator is crucial for mesh routing decisions and
service discovery by providing a unified health view.

TODO: Add weighted health scoring
TODO: Implement health trend analysis
FIXME: Improve cache memory usage for many checks
"""

class HealthAggregator:
    """
    Aggregates and manages multiple health checks for a service.
    
    Core responsibilities:
    - Maintain check registry
    - Execute checks concurrently
    - Cache results
    - Determine overall status
    
    Uses a cache-first approach with TTL to:
    - Reduce check frequency
    - Minimize resource usage
    - Provide consistent results
    
    NOTE: Cache TTL should be shorter than critical health windows
    FIXME: Add support for check priorities
    """
    
    def __init__(self, service_name: str):
        """
        Initialize aggregator with service context.
        
        The service name is used for:
        - Metrics tagging
        - Log correlation
        - Health report identification
        
        NOTE: Choose descriptive, mesh-unique service names
        """
        self.service_name = service_name
        self.checks: Dict[str, BaseHealthCheck] = {}
        self.results_cache: Dict[str, HealthCheckResult] = {}
        self.cache_ttl = timedelta(seconds=30)  # Balance freshness vs performance
        self.logger = logger.bind(component="health_aggregator")
    
    def add_check(self, name: str, check: BaseHealthCheck) -> None:
        """
        Register a new health check.
        
        Checks should be atomic and focused:
        - One responsibility per check
        - Independent execution
        - Clear failure conditions
        
        NOTE: Check names must be unique per aggregator
        """
        self.checks[name] = check
    
    def remove_check(self, name: str) -> None:
        """Remove a health check."""
        self.checks.pop(name, None)
        self.results_cache.pop(name, None)
    
    async def check_health(self, use_cache: bool = True) -> Dict:
        """
        Execute health checks and aggregate results.
        
        Aggregation strategy:
        1. Use cache when valid
        2. Run new checks concurrently
        3. Determine overall status
        4. Update cache
        
        Status determination rules:
        - UNHEALTHY if any check is unhealthy
        - DEGRADED if any check is degraded
        - HEALTHY if all checks are healthy
        
        NOTE: Cache can be bypassed for immediate status
        TODO: Add support for check weighting
        """
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
        """
        Execute a single health check with error handling.
        
        Error handling strategy:
        1. Catch all exceptions
        2. Mark check as unhealthy
        3. Log error details
        4. Cache failure result
        
        This prevents individual check failures from:
        - Blocking other checks
        - Breaking aggregation
        - Losing error context
        
        NOTE: Failed checks are cached to prevent retry storms
        FIXME: Add support for partial check results
        """
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