from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass
import random
import time
import structlog
from ..discovery.registry import ServiceRegistration

logger = structlog.get_logger()

@dataclass
class HealthStatus:
    """Health status information for load balancing decisions"""
    healthy: bool = True
    last_check: float = time.time()
    error_count: int = 0
    latency_ms: float = 0.0
    success_rate: float = 1.0
    capacity: float = 1.0  # 0.0-1.0 representing available capacity

@dataclass
class LoadBalancerStats:
    """Load balancer performance statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    active_instances: int = 0
    healthy_instances: int = 0

class LoadBalancingStrategy(ABC):
    """Base class for load balancing strategies"""
    
    @abstractmethod
    async def select_instance(
        self,
        instances: List[ServiceRegistration],
        health_states: Dict[str, HealthStatus]
    ) -> Optional[ServiceRegistration]:
        """Select an instance based on strategy and health"""
        pass
        
    @abstractmethod
    def update_stats(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update instance statistics"""
        pass

class RoundRobinStrategy(LoadBalancingStrategy):
    """Round-robin selection with health checks"""
    
    def __init__(self):
        self.current_index = 0
        self.stats = LoadBalancerStats()
        
    async def select_instance(
        self,
        instances: List[ServiceRegistration],
        health_states: Dict[str, HealthStatus]
    ) -> Optional[ServiceRegistration]:
        """Select next healthy instance in rotation"""
        if not instances:
            return None
            
        # Filter healthy instances
        healthy_instances = [
            inst for inst in instances
            if health_states.get(inst.id, HealthStatus()).healthy
        ]
        
        if not healthy_instances:
            return None
            
        # Update stats
        self.stats.active_instances = len(instances)
        self.stats.healthy_instances = len(healthy_instances)
        
        # Select next instance
        selected = healthy_instances[self.current_index % len(healthy_instances)]
        self.current_index += 1
        
        return selected
        
    def update_stats(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update instance statistics"""
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
            
        # Update average latency
        if self.stats.total_requests == 1:
            self.stats.avg_latency_ms = latency_ms
        else:
            self.stats.avg_latency_ms = (
                (self.stats.avg_latency_ms * (self.stats.total_requests - 1) + latency_ms)
                / self.stats.total_requests
            )

class LeastConnectionsStrategy(LoadBalancingStrategy):
    """Select instance with fewest active connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, int] = {}
        self.stats = LoadBalancerStats()
        
    async def select_instance(
        self,
        instances: List[ServiceRegistration],
        health_states: Dict[str, HealthStatus]
    ) -> Optional[ServiceRegistration]:
        """Select instance with lowest connection count"""
        if not instances:
            return None
            
        # Filter healthy instances
        healthy_instances = [
            inst for inst in instances
            if health_states.get(inst.id, HealthStatus()).healthy
        ]
        
        if not healthy_instances:
            return None
            
        # Update stats
        self.stats.active_instances = len(instances)
        self.stats.healthy_instances = len(healthy_instances)
        
        # Select instance with fewest connections
        selected = min(
            healthy_instances,
            key=lambda x: self.active_connections.get(x.id, 0)
        )
        
        # Increment connection count
        self.active_connections[selected.id] = (
            self.active_connections.get(selected.id, 0) + 1
        )
        
        return selected
        
    def update_stats(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update instance statistics"""
        # Decrement connection count
        if instance_id in self.active_connections:
            self.active_connections[instance_id] -= 1
            if self.active_connections[instance_id] <= 0:
                del self.active_connections[instance_id]
                
        # Update general stats
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
            
        # Update average latency
        if self.stats.total_requests == 1:
            self.stats.avg_latency_ms = latency_ms
        else:
            self.stats.avg_latency_ms = (
                (self.stats.avg_latency_ms * (self.stats.total_requests - 1) + latency_ms)
                / self.stats.total_requests
            )

class WeightedResponseTimeStrategy(LoadBalancingStrategy):
    """Select instance based on weighted response time"""
    
    def __init__(self, smoothing_factor: float = 0.1):
        self.response_times: Dict[str, float] = {}
        self.smoothing_factor = smoothing_factor
        self.stats = LoadBalancerStats()
        
    async def select_instance(
        self,
        instances: List[ServiceRegistration],
        health_states: Dict[str, HealthStatus]
    ) -> Optional[ServiceRegistration]:
        """Select instance with best response time weight"""
        if not instances:
            return None
            
        # Filter healthy instances
        healthy_instances = [
            inst for inst in instances
            if health_states.get(inst.id, HealthStatus()).healthy
        ]
        
        if not healthy_instances:
            return None
            
        # Update stats
        self.stats.active_instances = len(instances)
        self.stats.healthy_instances = len(healthy_instances)
        
        # Calculate weights based on response times
        weights = []
        for instance in healthy_instances:
            rt = self.response_times.get(instance.id, 0)
            if rt == 0:
                weights.append(1.0)  # New instance gets full weight
            else:
                # Convert response time to weight (faster = higher weight)
                weights.append(1.0 / (rt + 1))
                
        # Normalize weights
        total_weight = sum(weights)
        if total_weight == 0:
            return random.choice(healthy_instances)
            
        normalized_weights = [w/total_weight for w in weights]
        
        # Select instance based on weights
        r = random.random()
        cumsum = 0
        for instance, weight in zip(healthy_instances, normalized_weights):
            cumsum += weight
            if r <= cumsum:
                return instance
                
        return healthy_instances[-1]
        
    def update_stats(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update instance statistics with exponential smoothing"""
        # Update response time with exponential smoothing
        current_rt = self.response_times.get(instance_id, latency_ms)
        self.response_times[instance_id] = (
            current_rt * (1 - self.smoothing_factor) +
            latency_ms * self.smoothing_factor
        )
        
        # Update general stats
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
            
        # Update average latency
        if self.stats.total_requests == 1:
            self.stats.avg_latency_ms = latency_ms
        else:
            self.stats.avg_latency_ms = (
                (self.stats.avg_latency_ms * (self.stats.total_requests - 1) + latency_ms)
                / self.stats.total_requests
            )

class AdaptiveStrategy(LoadBalancingStrategy):
    """Adaptive strategy that switches based on conditions"""
    
    def __init__(self):
        self.strategies = {
            "round_robin": RoundRobinStrategy(),
            "least_conn": LeastConnectionsStrategy(),
            "weighted_rt": WeightedResponseTimeStrategy()
        }
        self.current_strategy = "round_robin"
        self.stats = LoadBalancerStats()
        self.evaluation_window = 100  # requests
        self.last_evaluation = 0
        
    async def select_instance(
        self,
        instances: List[ServiceRegistration],
        health_states: Dict[str, HealthStatus]
    ) -> Optional[ServiceRegistration]:
        """Select instance using current best strategy"""
        # Evaluate and potentially switch strategies
        if (self.stats.total_requests - self.last_evaluation) >= self.evaluation_window:
            self._evaluate_strategy()
            self.last_evaluation = self.stats.total_requests
            
        return await self.strategies[self.current_strategy].select_instance(
            instances,
            health_states
        )
        
    def update_stats(
        self,
        instance_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Update stats for all strategies"""
        # Update current strategy
        self.strategies[self.current_strategy].update_stats(
            instance_id,
            latency_ms,
            success
        )
        
        # Update general stats
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
        else:
            self.stats.failed_requests += 1
            
        # Update average latency
        if self.stats.total_requests == 1:
            self.stats.avg_latency_ms = latency_ms
        else:
            self.stats.avg_latency_ms = (
                (self.stats.avg_latency_ms * (self.stats.total_requests - 1) + latency_ms)
                / self.stats.total_requests
            )
            
    def _evaluate_strategy(self) -> None:
        """Evaluate and switch strategies based on performance"""
        # Get stats for each strategy
        stats = {
            name: strategy.stats
            for name, strategy in self.strategies.items()
        }
        
        # Simple evaluation based on success rate and latency
        best_score = float('-inf')
        best_strategy = self.current_strategy
        
        for name, stat in stats.items():
            if stat.total_requests == 0:
                continue
                
            success_rate = stat.successful_requests / stat.total_requests
            score = success_rate * 1000 - stat.avg_latency_ms
            
            if score > best_score:
                best_score = score
                best_strategy = name
                
        if best_strategy != self.current_strategy:
            logger.info("switching_lb_strategy",
                       old=self.current_strategy,
                       new=best_strategy,
                       score=best_score)
            self.current_strategy = best_strategy 