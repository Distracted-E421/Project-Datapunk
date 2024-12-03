from typing import Dict, List, Optional, Type
from dataclasses import dataclass
import asyncio
import time
import structlog
from .strategies import (
    LoadBalancingStrategy,
    RoundRobinStrategy,
    LeastConnectionsStrategy,
    WeightedResponseTimeStrategy,
    AdaptiveStrategy,
    HealthStatus,
    LoadBalancerStats
)
from ..discovery.registry import ServiceRegistration
from ...monitoring import MetricsCollector

logger = structlog.get_logger()

@dataclass
class LoadBalancerConfig:
    """Load balancer configuration"""
    strategy_type: Type[LoadBalancingStrategy] = AdaptiveStrategy
    health_check_interval: float = 5.0  # seconds
    health_check_timeout: float = 1.0  # seconds
    error_threshold: int = 3  # errors before marking unhealthy
    recovery_threshold: int = 2  # successes before marking healthy
    metrics_enabled: bool = True

class LoadBalancer:
    """
    Health-aware load balancer with multiple strategies.
    
    Features:
    - Multiple balancing strategies
    - Health monitoring
    - Performance tracking
    - Metric collection
    - Automatic recovery
    """
    
    def __init__(
        self,
        config: LoadBalancerConfig,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.metrics = metrics_collector
        self.strategy = config.strategy_type()
        self.health_states: Dict[str, HealthStatus] = {}
        self.instances: Dict[str, List[ServiceRegistration]] = {}
        self._health_check_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self.logger = logger.bind(component="load_balancer")
        
    async def start(self):
        """Start load balancer background tasks"""
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )
        
    async def stop(self):
        """Stop load balancer background tasks"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
                
    async def update_instances(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ):
        """Update available instances for a service"""
        async with self._lock:
            self.instances[service_name] = instances
            
            # Initialize health states for new instances
            for instance in instances:
                if instance.id not in self.health_states:
                    self.health_states[instance.id] = HealthStatus()
                    
            # Clean up old health states
            current_ids = {inst.id for inst in instances}
            self.health_states = {
                id_: state
                for id_, state in self.health_states.items()
                if id_ in current_ids
            }
            
    async def get_instance(
        self,
        service_name: str
    ) -> Optional[ServiceRegistration]:
        """Get next instance based on strategy"""
        async with self._lock:
            instances = self.instances.get(service_name, [])
            if not instances:
                return None
                
            selected = await self.strategy.select_instance(
                instances,
                self.health_states
            )
            
            if selected and self.metrics:
                await self.metrics.increment(
                    "load_balancer.instance_selected",
                    tags={
                        "service": service_name,
                        "strategy": self.strategy.__class__.__name__
                    }
                )
                
            return selected
            
    async def record_request(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ):
        """Record request result for an instance"""
        async with self._lock:
            # Update strategy stats
            self.strategy.update_stats(instance_id, latency_ms, success)
            
            # Update health state
            if instance_id in self.health_states:
                state = self.health_states[instance_id]
                
                if success:
                    state.error_count = max(0, state.error_count - 1)
                    if not state.healthy and state.error_count <= self.config.recovery_threshold:
                        state.healthy = True
                        self.logger.info("instance_recovered",
                                       instance_id=instance_id)
                else:
                    state.error_count += 1
                    if state.healthy and state.error_count >= self.config.error_threshold:
                        state.healthy = False
                        self.logger.warning("instance_marked_unhealthy",
                                          instance_id=instance_id,
                                          error_count=state.error_count)
                        
                # Update metrics
                state.last_check = time.time()
                state.latency_ms = latency_ms
                
                if self.metrics:
                    await self.metrics.gauge(
                        "load_balancer.instance_latency",
                        latency_ms,
                        tags={"instance_id": instance_id}
                    )
                    await self.metrics.gauge(
                        "load_balancer.instance_errors",
                        state.error_count,
                        tags={"instance_id": instance_id}
                    )
                    
    async def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        async with self._lock:
            stats = self.strategy.stats
            return {
                "total_requests": stats.total_requests,
                "successful_requests": stats.successful_requests,
                "failed_requests": stats.failed_requests,
                "avg_latency_ms": stats.avg_latency_ms,
                "active_instances": stats.active_instances,
                "healthy_instances": stats.healthy_instances,
                "current_strategy": self.strategy.__class__.__name__
            }
            
    async def _health_check_loop(self):
        """Periodic health check of instances"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_instance_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error("health_check_error",
                                error=str(e))
                
    async def _check_instance_health(self):
        """Check health status of all instances"""
        async with self._lock:
            current_time = time.time()
            
            for instance_id, state in self.health_states.items():
                # Check if instance has been idle too long
                time_since_check = current_time - state.last_check
                if time_since_check > self.config.health_check_timeout:
                    if state.healthy:
                        state.healthy = False
                        self.logger.warning("instance_marked_unhealthy_timeout",
                                          instance_id=instance_id,
                                          time_since_check=time_since_check)
                        
            if self.metrics:
                healthy_count = sum(
                    1 for state in self.health_states.values()
                    if state.healthy
                )
                await self.metrics.gauge(
                    "load_balancer.healthy_instances",
                    healthy_count
                ) 