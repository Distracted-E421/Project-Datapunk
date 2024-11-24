from typing import Dict, List, Optional, Any
import structlog
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from ..load_balancer.load_balancer_strategies import LoadBalancerStrategy, ServiceInstance
from .health_checks import HealthChecker, HealthStatus
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class HealthAwareConfig:
    """Configuration for health-aware load balancer."""
    check_interval: float = 30.0  # seconds
    health_threshold: float = 0.5
    recovery_threshold: float = 0.8
    circuit_break_threshold: int = 5
    recovery_window: int = 300  # seconds
    min_healthy_instances: int = 1

class HealthAwareLoadBalancer:
    """Load balancer with integrated health checking."""
    
    def __init__(self,
                 strategy: LoadBalancerStrategy,
                 health_checker: HealthChecker,
                 config: HealthAwareConfig,
                 metrics: MetricsClient):
        self.strategy = strategy
        self.health_checker = health_checker
        self.config = config
        self.metrics = metrics
        self.logger = logger.bind(component="health_aware_lb")
        
        # Health state tracking
        self.health_scores: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
        self.last_check: Dict[str, datetime] = {}
        self.circuit_breakers: Dict[str, bool] = {}
        
        # Start health check loop
        asyncio.create_task(self._health_check_loop())
    
    async def select_instance(self,
                            service: str,
                            instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance considering health status."""
        try:
            # Filter unhealthy instances
            healthy = [
                i for i in instances
                if self.is_healthy(i.id)
            ]
            
            if len(healthy) < self.config.min_healthy_instances:
                self.logger.warning("insufficient_healthy_instances",
                                  service=service,
                                  healthy_count=len(healthy))
                self.metrics.record_error(service, "insufficient_healthy")
                return None
            
            # Update instance health scores
            for instance in healthy:
                instance.health_score = self.health_scores.get(instance.id, 1.0)
            
            # Use strategy to select instance
            selected = self.strategy.select_instance(service, healthy)
            if selected:
                self.metrics.record_selection(
                    service,
                    selected.id,
                    self.health_scores.get(selected.id, 1.0)
                )
            
            return selected
            
        except Exception as e:
            self.logger.error("instance_selection_failed",
                            service=service,
                            error=str(e))
            self.metrics.record_error(service, "selection_failed")
            return None
    
    def is_healthy(self, instance_id: str) -> bool:
        """Check if instance is healthy."""
        # Check circuit breaker
        if self.circuit_breakers.get(instance_id, False):
            if not self._check_recovery_window(instance_id):
                return False
        
        # Check health score
        score = self.health_scores.get(instance_id, 0.0)
        return score >= self.config.health_threshold
    
    def record_success(self, instance_id: str):
        """Record successful request."""
        self.error_counts[instance_id] = 0
        
        # Improve health score
        current = self.health_scores.get(instance_id, 1.0)
        self.health_scores[instance_id] = min(1.0, current + 0.1)
        
        # Check for circuit breaker recovery
        if self.circuit_breakers.get(instance_id, False):
            if self.health_scores[instance_id] >= self.config.recovery_threshold:
                self.circuit_breakers[instance_id] = False
                self.logger.info("circuit_breaker_recovered",
                               instance_id=instance_id)
    
    def record_error(self, instance_id: str):
        """Record request error."""
        self.error_counts[instance_id] = self.error_counts.get(instance_id, 0) + 1
        
        # Degrade health score
        current = self.health_scores.get(instance_id, 1.0)
        self.health_scores[instance_id] = max(0.0, current - 0.2)
        
        # Check circuit breaker threshold
        if self.error_counts[instance_id] >= self.config.circuit_break_threshold:
            self.circuit_breakers[instance_id] = True
            self.logger.warning("circuit_breaker_opened",
                              instance_id=instance_id)
    
    async def _health_check_loop(self):
        """Continuous health check loop."""
        while True:
            try:
                await self._run_health_checks()
            except Exception as e:
                self.logger.error("health_check_failed",
                                error=str(e))
            
            await asyncio.sleep(self.config.check_interval)
    
    async def _run_health_checks(self):
        """Run health checks for all instances."""
        for instance_id, last_check in self.last_check.items():
            if datetime.utcnow() - last_check < timedelta(seconds=self.config.check_interval):
                continue
            
            result = await self.health_checker.check_health(instance_id)
            self.last_check[instance_id] = datetime.utcnow()
            
            if result.status == HealthStatus.HEALTHY:
                self.record_success(instance_id)
            else:
                self.record_error(instance_id)
    
    def _check_recovery_window(self, instance_id: str) -> bool:
        """Check if instance can attempt recovery."""
        last_check = self.last_check.get(instance_id)
        if not last_check:
            return True
        
        time_since_check = (datetime.utcnow() - last_check).total_seconds()
        return time_since_check >= self.config.recovery_window 