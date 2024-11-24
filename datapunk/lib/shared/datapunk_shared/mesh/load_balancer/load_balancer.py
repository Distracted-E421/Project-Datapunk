from typing import List, Dict, Any, Optional
from enum import Enum
import random
import time
import logging
from dataclasses import dataclass
from .load_balancer.load_balancer_metrics import LoadBalancerMetrics

@dataclass
class ServiceInstance:
    id: str
    address: str
    port: int
    weight: int = 1
    last_used: float = 0
    active_connections: int = 0
    health_score: float = 1.0

class LoadBalancerStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"

class LoadBalancer:
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
        """Register a new service instance"""
        if service_name not in self.instances:
            self.instances[service_name] = []
            self.current_index[service_name] = 0
        
        self.instances[service_name].append(instance)
        if self.metrics:
            await self.metrics.record_instance_registration(service_name)

    async def get_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Get next available instance based on selected strategy"""
        if service_name not in self.instances or not self.instances[service_name]:
            return None

        instance = await self._select_instance(service_name)
        if instance and self.metrics:
            await self.metrics.record_instance_selection(service_name, instance.id)
        
        return instance

    async def _select_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Select instance based on current strategy"""
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
        """Round robin selection strategy"""
        instances = self.instances[service_name]
        index = self.current_index[service_name]
        instance = instances[index]
        
        self.current_index[service_name] = (index + 1) % len(instances)
        return instance

    async def _least_connections_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Least connections selection strategy"""
        return min(instances, key=lambda x: x.active_connections)

    async def _weighted_round_robin_select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round robin selection strategy"""
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
        """Update health score for an instance"""
        for instance in self.instances.get(service_name, []):
            if instance.id == instance_id:
                instance.health_score = health_score
                if self.metrics:
                    await self.metrics.record_health_score(service_name, instance_id, health_score)
                break

    async def remove_instance(self, service_name: str, instance_id: str) -> None:
        """Remove an instance from the load balancer"""
        if service_name in self.instances:
            self.instances[service_name] = [
                i for i in self.instances[service_name] if i.id != instance_id
            ]
            if self.metrics:
                await self.metrics.record_instance_removal(service_name, instance_id)
    