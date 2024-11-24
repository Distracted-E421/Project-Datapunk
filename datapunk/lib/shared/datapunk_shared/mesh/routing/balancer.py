from enum import Enum
from typing import List, Dict, Any
import random
from dataclasses import dataclass

@dataclass
class ServiceInstance:
    id: str
    host: str
    port: int
    weight: int = 100
    healthy: bool = True
    metadata: Dict[str, Any] = None

class BalancingStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED = "weighted"
    LEAST_CONNECTIONS = "least_connections"
    RANDOM = "random"

class LoadBalancer:
    def __init__(self, strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN):
        self.strategy = strategy
        self.instances: List[ServiceInstance] = []
        self.current_index = 0
        self.connection_counts: Dict[str, int] = {}

    def add_instance(self, instance: ServiceInstance):
        self.instances.append(instance)
        self.connection_counts[instance.id] = 0

    def get_next_instance(self) -> ServiceInstance:
        if not self.instances:
            raise Exception("No available instances")

        healthy_instances = [i for i in self.instances if i.healthy]
        if not healthy_instances:
            raise Exception("No healthy instances available")

        if self.strategy == BalancingStrategy.ROUND_ROBIN:
            instance = healthy_instances[self.current_index % len(healthy_instances)]
            self.current_index += 1
            return instance
        
        elif self.strategy == BalancingStrategy.WEIGHTED:
            total_weight = sum(i.weight for i in healthy_instances)
            r = random.uniform(0, total_weight)
            upto = 0
            for instance in healthy_instances:
                upto += instance.weight
                if upto > r:
                    return instance 