"""
Dependency-Aware Circuit Breaker Strategy

Implements a circuit breaker strategy that considers service dependencies
when making circuit breaking decisions. This allows for more intelligent
failure handling based on the health and status of dependencies.
"""

from typing import Dict, Optional, Any, List
import asyncio
import structlog
from datetime import datetime, timedelta

from .circuit_breaker_strategies import CircuitBreakerStrategy
from .dependency_chain import (
    DependencyChain,
    DependencyType,
    HealthStatus,
    DependencyConfig
)

logger = structlog.get_logger()

class DependencyAwareStrategy(CircuitBreakerStrategy):
    """
    A circuit breaker strategy that makes decisions based on dependency health.
    
    Features:
    - Dependency health monitoring
    - Cascading failure prevention
    - Smart recovery based on dependency status
    - Failure impact analysis
    - Health-aware request routing
    """
    
    def __init__(self,
                 service_id: str,
                 failure_threshold: int = 5,
                 success_threshold: int = 3,
                 timeout: float = 30.0,
                 half_open_timeout: float = 5.0,
                 dependency_config: Optional[DependencyConfig] = None):
        """Initialize dependency-aware strategy"""
        super().__init__(
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            half_open_timeout=half_open_timeout
        )
        
        self.service_id = service_id
        self.dependency_chain = DependencyChain(dependency_config)
        self.logger = logger.bind(
            component="dependency_aware_strategy",
            service=service_id
        )
        
        # Track dependency-related failures
        self.dependency_failures: Dict[str, int] = {}
        self.last_dependency_check = datetime.utcnow()
        
    async def start(self):
        """Start dependency monitoring"""
        await self.dependency_chain.start()
        
    async def stop(self):
        """Stop dependency monitoring"""
        await self.dependency_chain.stop()
        
    def add_dependency(self,
                      dependency_id: str,
                      dependency_type: DependencyType,
                      impact_score: float = 1.0):
        """Add a service dependency"""
        self.dependency_chain.add_dependency(
            self.service_id,
            dependency_id,
            dependency_type,
            impact_score
        )
        self.dependency_failures[dependency_id] = 0
        
    def remove_dependency(self, dependency_id: str):
        """Remove a service dependency"""
        self.dependency_chain.remove_dependency(
            self.service_id,
            dependency_id
        )
        if dependency_id in self.dependency_failures:
            del self.dependency_failures[dependency_id]
            
    async def should_allow_request(self) -> bool:
        """
        Determine if request should be allowed based on circuit state
        and dependency health.
        """
        # First check basic circuit breaker state
        if not await super().should_allow_request():
            return False
            
        # Check dependency health
        dependency_status = await self.dependency_chain.get_dependency_status(
            self.service_id
        )
        
        # Update last check time
        self.last_dependency_check = datetime.utcnow()
        
        # Check for critical dependency failures
        for dep_id, status in dependency_status.items():
            if status == HealthStatus.UNHEALTHY:
                dep_info = self.dependency_chain.dependencies[
                    self.service_id
                ][dep_id]
                if dep_info.dependency_type == DependencyType.CRITICAL:
                    self.logger.warning(
                        "Critical dependency unhealthy",
                        dependency=dep_id
                    )
                    return False
                    
        return True
        
    async def record_success(self):
        """Record successful request and update dependency health"""
        await super().record_success()
        
        # Reset dependency failure counts on success
        for dep_id in self.dependency_failures:
            self.dependency_failures[dep_id] = 0
            
        # Update dependency health
        await self.dependency_chain.update_health(
            self.service_id,
            HealthStatus.HEALTHY
        )
        
    async def record_failure(self, error: Optional[Exception] = None):
        """Record failed request and update dependency health"""
        await super().record_failure(error)
        
        # Check if failure is dependency-related
        if error and hasattr(error, 'dependency_id'):
            dep_id = getattr(error, 'dependency_id')
            if dep_id in self.dependency_failures:
                self.dependency_failures[dep_id] += 1
                
                # Update dependency health if threshold reached
                if self.dependency_failures[dep_id] >= self.failure_threshold:
                    await self.dependency_chain.update_health(
                        dep_id,
                        HealthStatus.UNHEALTHY,
                        {
                            "reason": "failure_threshold_reached",
                            "failure_count": self.dependency_failures[dep_id]
                        }
                    )
                    
        # Update service health
        await self.dependency_chain.update_health(
            self.service_id,
            HealthStatus.UNHEALTHY if self.is_open else HealthStatus.DEGRADED,
            {
                "reason": "circuit_breaker_state",
                "state": "open" if self.is_open else "half_open"
            }
        )
        
    async def attempt_reset(self):
        """
        Attempt to reset circuit breaker based on both success count
        and dependency health.
        """
        # First check basic reset conditions
        if not await super().attempt_reset():
            return False
            
        # Check dependency health before full reset
        dependency_status = await self.dependency_chain.get_dependency_status(
            self.service_id
        )
        
        # Only reset if all critical/required dependencies are healthy
        for dep_id, status in dependency_status.items():
            dep_info = self.dependency_chain.dependencies[
                self.service_id
            ][dep_id]
            if dep_info.dependency_type in (
                DependencyType.CRITICAL,
                DependencyType.REQUIRED
            ):
                if not await self.dependency_chain.check_dependency_health(
                    self.service_id,
                    dep_id
                ):
                    self.logger.info(
                        "Reset blocked by unhealthy dependency",
                        dependency=dep_id,
                        type=dep_info.dependency_type.value
                    )
                    return False
                    
        # Update service health on successful reset
        await self.dependency_chain.update_health(
            self.service_id,
            HealthStatus.HEALTHY,
            {"reason": "circuit_breaker_reset"}
        )
        
        return True
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get combined circuit breaker and dependency metrics"""
        base_metrics = await super().get_metrics()
        dependency_metrics = await self.dependency_chain.get_metrics()
        
        return {
            **base_metrics,
            "dependencies": dependency_metrics,
            "dependency_failures": self.dependency_failures,
            "last_dependency_check": self.last_dependency_check.isoformat()
        } 