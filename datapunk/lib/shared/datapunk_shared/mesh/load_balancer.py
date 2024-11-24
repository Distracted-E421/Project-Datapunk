from typing import List, Dict, Optional, Any
from enum import Enum
import random
import time
import structlog
from dataclasses import dataclass
from collections import defaultdict
from .metrics import LoadBalancerMetrics
from ..tracing import trace_method

logger = structlog.get_logger()

class LoadBalancerStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    RANDOM = "random"

@dataclass
class ServiceInstance:
    id: str
    address: str
    port: int
    weight: int = 1
    active_connections: int = 0
    last_used: float = 0.0
    health_score: float = 1.0

class LoadBalancer:
    def __init__(self, strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.instances: Dict[str, List[ServiceInstance]] = defaultdict(list)
        self.current_index: Dict[str, int] = defaultdict(int)
        self.logger = logger.bind(component="load_balancer")
        self.metrics = LoadBalancerMetrics()

    def register_instance(self, service_name: str, instance: ServiceInstance) -> None:
        """Register a service instance with the load balancer."""
        self.instances[service_name].append(instance)
        self.logger.info("instance_registered",
                        service=service_name,
                        instance_id=instance.id)

    def deregister_instance(self, service_name: str, instance_id: str) -> None:
        """Remove a service instance from the load balancer."""
        self.instances[service_name] = [
            inst for inst in self.instances[service_name]
            if inst.id != instance_id
        ]
        self.logger.info("instance_deregistered",
                        service=service_name,
                        instance_id=instance_id)

    @trace_method("get_next_instance")
    def get_next_instance(self, service_name: str) -> Optional[ServiceInstance]:
        """Get the next available instance based on the selected strategy."""
        with self.tracer.start_span("check_instances") as span:
            instances = self.instances.get(service_name, [])
            span.set_attribute("available_instances", len(instances))
            
            if not instances:
                self.metrics.record_error(service_name, "no_instances_available")
                self.logger.warning("no_instances_available", service=service_name)
                return None

        try:
            with self.tracer.start_span("select_instance") as span:
                instance = None
                span.set_attribute("strategy", self.strategy.value)
                
                if self.strategy == LoadBalancerStrategy.ROUND_ROBIN:
                    instance = self._round_robin(service_name, instances)
                elif self.strategy == LoadBalancerStrategy.LEAST_CONNECTIONS:
                    instance = self._least_connections(instances)
                elif self.strategy == LoadBalancerStrategy.WEIGHTED_ROUND_ROBIN:
                    instance = self._weighted_round_robin(service_name, instances)
                elif self.strategy == LoadBalancerStrategy.RANDOM:
                    instance = self._random(instances)

                if instance:
                    span.set_attribute("selected_instance", instance.id)
                    self.metrics.record_request(
                        service_name, 
                        instance.id, 
                        self.strategy.value
                    )
                return instance

        except Exception as e:
            self.tracer.record_exception(e)
            self.metrics.record_error(service_name, str(e))
            self.logger.error("instance_selection_failed",
                            service=service_name,
                            error=str(e))
            return None

    def _round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Simple round-robin selection."""
        index = self.current_index[service_name]
        instance = instances[index]
        self.current_index[service_name] = (index + 1) % len(instances)
        return instance

    def _least_connections(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Select instance with fewest active connections."""
        return min(instances, key=lambda x: x.active_connections)

    def _weighted_round_robin(self, service_name: str, instances: List[ServiceInstance]) -> ServiceInstance:
        """Weighted round-robin selection."""
        total_weight = sum(instance.weight for instance in instances)
        if total_weight == 0:
            return self._round_robin(service_name, instances)

        current = self.current_index[service_name]
        for instance in instances:
            current -= instance.weight
            if current < 0:
                return instance
        return instances[0]

    def _random(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """Random instance selection."""
        return random.choice(instances)

    def record_request_start(self, instance: ServiceInstance) -> None:
        """Record the start of a request to an instance."""
        instance.active_connections += 1
        instance.last_used = time.time()
        self.metrics.update_active_connections(
            instance.id.split('-')[0],  # service name
            instance.id,
            instance.active_connections
        )

    def record_request_complete(self, instance: ServiceInstance) -> None:
        """Record the completion of a request to an instance."""
        instance.active_connections = max(0, instance.active_connections - 1)
        self.metrics.update_active_connections(
            instance.id.split('-')[0],  # service name
            instance.id,
            instance.active_connections
        )

    def update_health_score(self, instance: ServiceInstance, score: float) -> None:
        """Update the health score of an instance."""
        instance.health_score = max(0.0, min(1.0, score))
        self.metrics.update_health_score(
            instance.id.split('-')[0],  # service name
            instance.id,
            instance.health_score
        )
    