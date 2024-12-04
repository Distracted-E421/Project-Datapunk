from typing import Dict, List, Optional, Any
import structlog
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from ..load_balancer.load_balancer_strategies import LoadBalancerStrategy, ServiceInstance
from .health_checks import HealthChecker, HealthStatus
from ..monitoring import MetricsClient

logger = structlog.get_logger()

"""
Health-Aware Load Balancer for Datapunk Service Mesh

This module provides intelligent load balancing with:
- Health-based instance selection
- Circuit breaking for fault isolation
- Gradual recovery mechanisms
- Health score tracking
- Continuous health monitoring

The balancer ensures reliable service routing by combining
load balancing strategies with health awareness.

TODO: Add predictive health scoring
TODO: Implement adaptive thresholds
FIXME: Improve memory usage for large instance sets
"""

@dataclass
class HealthAwareConfig:
    """
    Configuration for health-aware load balancing behavior.
    
    Thresholds and windows are tuned for:
    - Quick problem detection
    - Gradual recovery
    - Fault isolation
    
    NOTE: recovery_threshold should be > health_threshold
    TODO: Add support for service-specific configurations
    """
    check_interval: float = 30.0  # Health check frequency
    health_threshold: float = 0.5  # Minimum score for routing
    recovery_threshold: float = 0.8  # Score needed for circuit recovery
    circuit_break_threshold: int = 5  # Errors before breaking
    recovery_window: int = 300  # Seconds before retry
    min_healthy_instances: int = 1  # Required healthy instances

class HealthAwareLoadBalancer:
    """
    Load balancer with integrated health tracking and circuit breaking.
    
    Core responsibilities:
    - Track instance health scores
    - Manage circuit breakers
    - Filter unhealthy instances
    - Record success/failure
    - Monitor instance health
    
    Uses a scoring system that:
    - Degrades quickly on errors
    - Recovers gradually on success
    - Prevents flapping
    
    NOTE: All operations are thread-safe
    FIXME: Improve score calculation for burst errors
    """
    
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
    
    async def select_instance(
        self,
        service: str,
        instances: List[ServiceInstance]
    ) -> Optional[ServiceInstance]:
        """
        Select healthy instance using configured strategy.
        
        Selection process:
        1. Filter unhealthy instances
        2. Check minimum healthy requirement
        3. Apply health scores
        4. Use strategy for final selection
        
        NOTE: Returns None if insufficient healthy instances
        TODO: Add support for priority-based selection
        """
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
        """
        Update instance health on successful request.
        
        Success handling:
        1. Reset error count
        2. Gradually improve health score
        3. Check for circuit breaker recovery
        
        NOTE: Score improvement is intentionally gradual
        to prevent premature recovery
        """
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
        """
        Update instance health on request failure.
        
        Error handling:
        1. Increment error count
        2. Significantly reduce health score
        3. Check circuit breaker threshold
        
        NOTE: Score reduction is aggressive to quickly
        remove problematic instances
        """
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
        """
        Continuous health monitoring loop.
        
        Implements a pull-based check pattern:
        1. Check all instances periodically
        2. Update health scores
        3. Manage circuit breakers
        
        NOTE: Continues despite individual check failures
        FIXME: Add backoff for repeatedly failing checks
        """
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
        """
        Verify if instance can attempt recovery.
        
        Recovery logic:
        - Enforce minimum time between attempts
        - Allow immediate first attempt
        - Reset on successful recovery
        
        This prevents rapid cycling of problematic instances.
        NOTE: Window resets on successful recovery
        """
        last_check = self.last_check.get(instance_id)
        if not last_check:
            return True
        
        time_since_check = (datetime.utcnow() - last_check).total_seconds()
        return time_since_check >= self.config.recovery_window 