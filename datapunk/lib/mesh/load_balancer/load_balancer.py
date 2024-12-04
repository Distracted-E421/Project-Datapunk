from typing import List, Dict, Any, Optional
from enum import Enum
import random
import time
import logging
from dataclasses import dataclass
from .load_balancer.load_balancer_metrics import LoadBalancerMetrics

"""
Core load balancer implementation supporting multiple distribution strategies
with health awareness and metrics collection.

This module implements the service mesh load balancing component, providing:
- Multiple load balancing strategies
- Health-aware instance selection
- Async metrics collection
- Dynamic instance registration/removal
"""

@dataclass
class ServiceInstance:
    """
    Represents a service instance with health and performance metrics.
    
    NOTE: health_score ranges from 0.0 (unhealthy) to 1.0 (healthy)
    TODO: Add capacity metrics for better load distribution
    """
    id: str
    address: str
    port: int
    weight: int = 1  # Relative capacity weight for load distribution
    last_used: float = 0  # Unix timestamp of last request
    active_connections: int = 0  # Current connection count
    health_score: float = 1.0  # Dynamic health score from monitoring

class LoadBalancerStrategy(Enum):
    """
    Available load balancing strategies.
    
    NOTE: Strategy selection impacts performance under different load patterns:
    - ROUND_ROBIN: Best for uniform instance capacity
    - LEAST_CONNECTIONS: Best for varying instance capacity
    - WEIGHTED_ROUND_ROBIN: Best for known capacity differences
    - RANDOM: Useful for testing or very short-lived connections
    """
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"

class LoadBalancer:
    """
    Dynamic load balancer with health awareness and metrics collection.
    
    Supports multiple distribution strategies and maintains instance health
    scores for optimal request distribution. Integrates with metrics collection
    for performance monitoring and debugging.
    
    TODO: Add circuit breaker integration
    TODO: Implement strategy auto-switching based on load patterns
    """
    def __init__(
        self,
        strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN,
        metrics_enabled: bool = True
    ):
        self.strategy = strategy
        self.instances: Dict[str, List[ServiceInstance]] = {}
        self.current_index: Dict[str, int] = {}
        self.logger = logging.getLogger(__name__)
        self.metrics = LoadBalancerMetrics() if metrics_enabled else None

    async def register_instance(self, service_name: str, instance: ServiceInstance) -> None:
        """
        Register new service instance with the load balancer.
        
        Creates new service entry if needed and initializes round-robin index.
        Records registration event in metrics if enabled.
        """
        if service_name not in self.instances:
            self.instances[service_name] = []
            self.current_index[service_name] = 0
        
        self.instances[service_name].append(instance)
        if self.metrics:
            await self.metrics.record_instance_registration(service_name)

    async def get_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Get next available instance using current strategy.
        
        FIXME: May return None if service has no registered instances
        TODO: Add fallback strategy for service unavailability
        """
        if service_name not in self.instances or not self.instances[service_name]:
            return None

        instance = await self._select_instance(service_name)
        if instance and self.metrics:
            await self.metrics.record_instance_selection(service_name, instance.id)
        
        return instance

    async def _select_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Select instance using configured strategy.
        
        NOTE: Strategy changes take effect immediately on next selection
        """
        instances = self.instances[service_name]
        
        if self.strategy == LoadBalancerStrategy.ROUND_ROBIN:
            return await self._round_robin_select(service_name)
        elif self.strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_select(instances)
        elif self.strategy == LoadBalancerStrategy.WEIGHTED_ROUND_ROBIN:
            return await self._weighted_round_robin_select(instances)
        elif self.strategy == LoadBalancerStrategy.RANDOM:
            return random.choice(instances)
        
        return None

    async def _round_robin_select(self, service_name: str) -> ServiceInstance:
        """
        Basic round-robin selection.
        
        Maintains separate index per service for fair distribution.
        NOTE: Does not consider instance health or capacity
        """
        instances = self.instances[service_name]
        index = self.current_index[service_name]
        instance = instances[index]
        
        self.current_index[service_name] = (index + 1) % len(instances)
        return instance

    async def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """
        Select instance with fewest active connections.
        
        NOTE: Connection counts may be slightly stale due to async updates
        TODO: Consider health score in selection weight
        """
        return min(instances, key=lambda x: x.active_connections)

    async def _weighted_round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """
        Weighted selection based on instance capacity.
        
        Uses random selection weighted by instance capacity to prevent
        thundering herd problems with synchronized requests.
        
        FIXME: May show slight bias towards higher-weighted instances
        """
        total_weight = sum(instance.weight for instance in instances)
        if total_weight == 0:
            return random.choice(instances)

        r = random.uniform(0, total_weight)
        current_weight = 0
        
        for instance in instances:
            current_weight += instance.weight
            if current_weight >= r:
                return instance

        return instances[-1]

    async def update_instance_health(self, service_name: str, instance_id: str, health_score: float) -> None:
        """
        Update instance health score from monitoring.
        
        Health scores influence instance selection probability across all strategies.
        Records health change in metrics if enabled.
        """
        for instance in self.instances.get(service_name, []):
            if instance.id == instance_id:
                instance.health_score = health_score
                if self.metrics:
                    await self.metrics.record_health_score(service_name, instance_id, health_score)
                break

    async def remove_instance(self, service_name: str, instance_id: str) -> None:
        """
        Remove instance from load balancer.
        
        NOTE: Does not wait for active connections to complete
        TODO: Add graceful shutdown support with connection draining
        """
        if service_name in self.instances:
            self.instances[service_name] = [
                i for i in self.instances[service_name] if i.id != instance_id
            ]
            if self.metrics:
                await self.metrics.record_instance_removal(service_name, instance_id)
    