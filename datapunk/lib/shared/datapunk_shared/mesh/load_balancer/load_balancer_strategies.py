from typing import List, Dict, Optional, Any
import random
import time
import structlog
from dataclasses import dataclass
from abc import ABC, abstractmethod
from .load_balancer_metrics import LoadBalancerMetrics

logger = structlog.get_logger()

# ServiceInstance represents a backend service endpoint with health and performance metrics
# Health score ranges from 0.0 (unhealthy) to 1.0 (fully healthy)
@dataclass
class ServiceInstance:
    """Service instance details with health and performance tracking."""
    id: str  # Unique identifier for the service instance
    address: str  # Network address (IP or hostname)
    port: int  # Service port number
    weight: int = 1  # Relative capacity weight for load distribution
    active_connections: int = 0  # Current number of active connections
    last_used: float = 0.0  # Timestamp of last request (Unix timestamp)
    health_score: float = 1.0  # Dynamic health score based on monitoring
    metadata: Dict[str, Any] = None  # Additional instance-specific metadata

class LoadBalancerStrategy(ABC):
    """Base strategy for load balancing with health awareness.
    
    Implementations should consider:
    - Instance health scores for availability
    - Current load and capacity
    - Historical performance metrics
    """
    
    def __init__(self, metrics: LoadBalancerMetrics):
        self.metrics = metrics
        self.logger = logger.bind(strategy=self.__class__.__name__)
    
    @abstractmethod
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select next instance based on strategy."""
        pass
    
    def _filter_healthy(self, instances: List[ServiceInstance]) -> List[ServiceInstance]:
        """Filter instances with health scores above 0.5.
        
        NOTE: Threshold of 0.5 chosen based on production testing.
        TODO: Make health threshold configurable per service
        """
        return [i for i in instances if i.health_score > 0.5]

class WeightedRoundRobin(LoadBalancerStrategy):
    """Weighted round-robin selection with dynamic weight adjustment.
    
    Maintains separate weight counters per service to ensure fair distribution
    while respecting instance capacity differences.
    """
    
    def __init__(self, metrics: LoadBalancerMetrics):
        super().__init__(metrics)
        self._current_weights: Dict[str, Dict[str, int]] = {}
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using weighted round-robin algorithm.
        
        FIXME: Current implementation may show slight bias towards higher-weighted
        instances during rapid rebalancing
        """
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
            
        if service not in self._current_weights:
            self._current_weights[service] = {
                i.id: i.weight for i in healthy
            }
        
        # Get current weights
        weights = self._current_weights[service]
        
        # Find instance with highest current weight
        max_weight = max(weights.values())
        selected_id = next(
            id for id, w in weights.items()
            if w == max_weight
        )
        
        # Update weights
        total_weight = sum(i.weight for i in healthy)
        for id in weights:
            weights[id] += next(
                i.weight for i in healthy
                if i.id == id
            )
        weights[selected_id] -= total_weight
        
        return next(i for i in healthy if i.id == selected_id)

class LeastConnections(LoadBalancerStrategy):
    """Least connections selection weighted by instance health.
    
    Optimizes for even load distribution while considering instance health,
    preventing overload of degraded instances.
    """
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance with fewest active connections."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
            
        # Calculate load score (connections / health_score)
        def load_score(instance: ServiceInstance) -> float:
            return instance.active_connections / max(0.1, instance.health_score)
        
        return min(healthy, key=load_score)

class PowerOfTwo(LoadBalancerStrategy):
    """Power of two random choices with health-weighted load scoring.
    
    Provides O(1) selection time while maintaining good load distribution.
    Particularly effective under high concurrent load scenarios.
    """
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select best instance from two random choices."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
            
        if len(healthy) == 1:
            return healthy[0]
            
        # Select two random instances
        candidates = random.sample(healthy, min(2, len(healthy)))
        
        # Calculate load score (connections * (1/health_score))
        def load_score(instance: ServiceInstance) -> float:
            return instance.active_connections * (1 / max(0.1, instance.health_score))
        
        return min(candidates, key=load_score)

class AdaptiveLoadBalancer:
    """Adaptive load balancer that switches strategies based on system conditions.
    
    Strategy selection logic:
    - Uses least connections when load variance > 30%
    - Uses power of two under high load (>100 connections/instance)
    - Defaults to weighted round-robin for normal conditions
    
    NOTE: Thresholds determined through load testing and may need adjustment
    based on specific service characteristics
    """
    
    def __init__(self, metrics: LoadBalancerMetrics):
        self.metrics = metrics
        self.strategies = {
            "weighted_rr": WeightedRoundRobin(metrics),
            "least_conn": LeastConnections(metrics),
            "power_of_2": PowerOfTwo(metrics)
        }
        self.current_strategy = "weighted_rr"
        self.logger = logger.bind(component="adaptive_lb")
    
    def select_strategy(self,
                       service: str,
                       instances: List[ServiceInstance]) -> str:
        """Select optimal strategy based on current system conditions.
        
        TODO: Add historical performance analysis for strategy selection
        TODO: Make thresholds configurable per service
        """
        # Use least connections when load is uneven
        load_variance = self._calculate_load_variance(instances)
        if load_variance > 0.3:  # 30% variance threshold
            return "least_conn"
        
        # Use power of two under high load
        avg_load = sum(i.active_connections for i in instances) / len(instances)
        if avg_load > 100:  # High load threshold
            return "power_of_2"
        
        # Default to weighted round-robin
        return "weighted_rr"
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using adaptive strategy."""
        if not instances:
            return None
            
        # Select appropriate strategy
        strategy_name = self.select_strategy(service, instances)
        if strategy_name != self.current_strategy:
            self.logger.info("strategy_change",
                           old=self.current_strategy,
                           new=strategy_name)
            self.current_strategy = strategy_name
        
        # Use selected strategy
        strategy = self.strategies[strategy_name]
        instance = strategy.select_instance(service, instances)
        
        if instance:
            self.metrics.record_request(
                service,
                instance.id,
                strategy_name,
                time.time() - instance.last_used
            )
        
        return instance
    
    def _calculate_load_variance(self,
                               instances: List[ServiceInstance]) -> float:
        """Calculate coefficient of variation for instance loads.
        
        Returns normalized variance (standard deviation / mean) to compare
        load distribution across instances regardless of absolute load levels.
        """
        if not instances:
            return 0.0
            
        loads = [i.active_connections for i in instances]
        avg_load = sum(loads) / len(loads)
        
        if avg_load == 0:
            return 0.0
            
        variance = sum((l - avg_load) ** 2 for l in loads) / len(loads)
        return (variance ** 0.5) / avg_load  # Coefficient of variation 