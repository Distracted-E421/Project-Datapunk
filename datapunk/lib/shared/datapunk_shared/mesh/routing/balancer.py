from typing import Optional, Dict, Any, List, TypeVar, Generic, Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import random
from ..discovery.registry import ServiceRegistration
from ..health.checks import HealthCheck
from ...monitoring import MetricsCollector

T = TypeVar('T')

class BalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"
    CONSISTENT_HASH = "consistent_hash"

@dataclass
class BalancerConfig:
    """Configuration for load balancer"""
    strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN
    health_check_interval: float = 10.0  # seconds
    max_retries: int = 3
    connection_timeout: float = 5.0  # seconds
    enable_circuit_breaker: bool = True
    enable_sticky_sessions: bool = False
    session_cookie_name: str = "SERVERID"
    consistent_hash_replicas: int = 100
    response_timeout: float = 30.0  # seconds

class ServiceInstance:
    """Represents a service instance"""
    def __init__(self, registration: ServiceRegistration):
        self.registration = registration
        self.connections: int = 0
        self.response_times: List[float] = []
        self.last_health_check: Optional[datetime] = None
        self.is_healthy: bool = True
        self.weight: int = 1
        self.failures: int = 0

    def update_response_time(self, response_time: float):
        """Update average response time"""
        self.response_times.append(response_time)
        if len(self.response_times) > 100:  # Keep last 100 measurements
            self.response_times.pop(0)

    @property
    def avg_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return float('inf')
        return sum(self.response_times) / len(self.response_times)

class LoadBalancer(Generic[T]):
    """Load balancer implementation"""
    def __init__(
        self,
        config: BalancerConfig,
        health_check: Optional[HealthCheck] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.health_check = health_check
        self.metrics = metrics_collector
        self._instances: Dict[str, ServiceInstance] = {}
        self._current_index: int = 0
        self._hash_ring: Dict[int, str] = {}
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start load balancer"""
        if self.health_check:
            self._health_check_task = asyncio.create_task(
                self._health_check_loop()
            )

    async def stop(self):
        """Stop load balancer"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    async def add_instance(self, registration: ServiceRegistration):
        """Add service instance"""
        async with self._lock:
            instance = ServiceInstance(registration)
            self._instances[registration.id] = instance
            
            if self.config.strategy == BalancingStrategy.CONSISTENT_HASH:
                self._update_hash_ring()
            
            if self.metrics:
                await self.metrics.increment(
                    "load_balancer.instances.added",
                    tags={"service": registration.service_name}
                )

    async def remove_instance(self, instance_id: str):
        """Remove service instance"""
        async with self._lock:
            if instance_id in self._instances:
                del self._instances[instance_id]
                
                if self.config.strategy == BalancingStrategy.CONSISTENT_HASH:
                    self._update_hash_ring()
                
                if self.metrics:
                    await self.metrics.increment(
                        "load_balancer.instances.removed",
                        tags={"instance": instance_id}
                    )

    async def get_instance(
        self,
        key: Optional[str] = None
    ) -> Optional[ServiceInstance]:
        """Get next service instance based on strategy"""
        async with self._lock:
            healthy_instances = [
                i for i in self._instances.values()
                if i.is_healthy
            ]
            
            if not healthy_instances:
                return None

            instance = await self._select_instance(healthy_instances, key)
            if instance:
                instance.connections += 1
                
                if self.metrics:
                    await self.metrics.gauge(
                        "load_balancer.instance.connections",
                        instance.connections,
                        tags={"instance": instance.registration.id}
                    )
                
            return instance

    async def _select_instance(
        self,
        instances: List[ServiceInstance],
        key: Optional[str] = None
    ) -> Optional[ServiceInstance]:
        """Select instance based on balancing strategy"""
        if not instances:
            return None

        if self.config.strategy == BalancingStrategy.ROUND_ROBIN:
            instance = instances[self._current_index % len(instances)]
            self._current_index += 1
            return instance

        elif self.config.strategy == BalancingStrategy.LEAST_CONNECTIONS:
            return min(instances, key=lambda i: i.connections)

        elif self.config.strategy == BalancingStrategy.WEIGHTED_ROUND_ROBIN:
            total_weight = sum(i.weight for i in instances)
            if total_weight == 0:
                return random.choice(instances)
                
            point = random.randint(0, total_weight - 1)
            for instance in instances:
                if point < instance.weight:
                    return instance
                point -= instance.weight

        elif self.config.strategy == BalancingStrategy.RANDOM:
            return random.choice(instances)

        elif self.config.strategy == BalancingStrategy.LEAST_RESPONSE_TIME:
            return min(instances, key=lambda i: i.avg_response_time)

        elif self.config.strategy == BalancingStrategy.CONSISTENT_HASH:
            if not key:
                return random.choice(instances)
            hash_key = self._get_hash(key)
            instance_id = self._get_instance_from_ring(hash_key)
            return self._instances.get(instance_id)

        return random.choice(instances)

    def _update_hash_ring(self):
        """Update consistent hash ring"""
        self._hash_ring.clear()
        for instance_id in self._instances:
            for i in range(self.config.consistent_hash_replicas):
                hash_key = self._get_hash(f"{instance_id}:{i}")
                self._hash_ring[hash_key] = instance_id
                
    def _get_hash(self, key: str) -> int:
        """Get hash value for key"""
        return hash(key)

    def _get_instance_from_ring(self, hash_key: int) -> str:
        """Get instance ID from hash ring"""
        if not self._hash_ring:
            raise ValueError("Hash ring is empty")
            
        keys = sorted(self._hash_ring.keys())
        for key in keys:
            if hash_key <= key:
                return self._hash_ring[key]
        return self._hash_ring[keys[0]]

    async def _health_check_loop(self):
        """Periodic health check of instances"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_instances_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "load_balancer.health_check.error",
                        tags={"error": str(e)}
                    )

    async def _check_instances_health(self):
        """Check health of all instances"""
        for instance in self._instances.values():
            try:
                is_healthy = await self.health_check.check_instance_health(
                    instance.registration
                )
                
                instance.is_healthy = is_healthy
                instance.last_health_check = datetime.utcnow()
                
                if self.metrics:
                    await self.metrics.gauge(
                        "load_balancer.instance.health",
                        1 if is_healthy else 0,
                        tags={"instance": instance.registration.id}
                    )
                    
            except Exception as e:
                instance.failures += 1
                if self.metrics:
                    await self.metrics.increment(
                        "load_balancer.health_check.failure",
                        tags={
                            "instance": instance.registration.id,
                            "error": str(e)
                        }
                    )

    async def release_instance(self, instance: ServiceInstance):
        """Release instance after use"""
        async with self._lock:
            instance.connections = max(0, instance.connections - 1)
            
            if self.metrics:
                await self.metrics.gauge(
                    "load_balancer.instance.connections",
                    instance.connections,
                    tags={"instance": instance.registration.id}
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        stats = {
            "total_instances": len(self._instances),
            "healthy_instances": len([i for i in self._instances.values() if i.is_healthy]),
            "strategy": self.config.strategy.value,
            "instances": {}
        }
        
        for instance_id, instance in self._instances.items():
            stats["instances"][instance_id] = {
                "connections": instance.connections,
                "avg_response_time": instance.avg_response_time,
                "is_healthy": instance.is_healthy,
                "failures": instance.failures,
                "last_health_check": instance.last_health_check.isoformat() if instance.last_health_check else None
            }
            
        return stats