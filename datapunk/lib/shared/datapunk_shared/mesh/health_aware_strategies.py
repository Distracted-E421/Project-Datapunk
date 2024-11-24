from typing import List, Dict, Optional, Any
import structlog
import random
import time
from dataclasses import dataclass
from .load_balancer_strategies import LoadBalancerStrategy, ServiceInstance
from .health_aware_metrics import HealthAwareMetrics

logger = structlog.get_logger()

@dataclass
class HealthStrategyConfig:
    """Configuration for health-aware strategies."""
    min_health_score: float = 0.5
    health_weight: float = 0.7
    load_weight: float = 0.3
    recovery_threshold: float = 0.8
    max_consecutive_failures: int = 3

class HealthWeightedRoundRobin(LoadBalancerStrategy):
    """Round-robin weighted by health scores."""
    
    def __init__(self, metrics: HealthAwareMetrics, config: HealthStrategyConfig):
        self.metrics = metrics
        self.config = config
        self._current_index: Dict[str, int] = {}
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using health-weighted round-robin."""
        if not instances:
            return None
        
        start_time = time.time()
        try:
            # Filter by minimum health score
            healthy = [i for i in instances if i.health_score >= self.config.min_health_score]
            if not healthy:
                self.metrics.record_rejection(service, "no_healthy_instances")
                return None
            
            # Get current index
            current = self._current_index.get(service, 0)
            
            # Select instance considering health scores
            selected = healthy[current % len(healthy)]
            self._current_index[service] = (current + 1) % len(healthy)
            
            # Record metrics
            self.metrics.record_selection(
                service,
                "health_weighted_rr",
                selected.health_score
            )
            
            return selected
            
        finally:
            self.metrics.observe_selection_latency(
                service,
                "health_weighted_rr",
                time.time() - start_time
            )

class HealthAwareLeastConnections(LoadBalancerStrategy):
    """Least connections weighted by health scores."""
    
    def __init__(self, metrics: HealthAwareMetrics, config: HealthStrategyConfig):
        self.metrics = metrics
        self.config = config
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using health-aware least connections."""
        if not instances:
            return None
        
        start_time = time.time()
        try:
            # Filter by minimum health score
            healthy = [i for i in instances if i.health_score >= self.config.min_health_score]
            if not healthy:
                self.metrics.record_rejection(service, "no_healthy_instances")
                return None
            
            # Calculate combined score (health and connections)
            def combined_score(instance: ServiceInstance) -> float:
                health_component = instance.health_score * self.config.health_weight
                conn_component = (1 - (instance.active_connections / 100)) * self.config.load_weight
                return health_component + conn_component
            
            # Select instance with best score
            selected = max(healthy, key=combined_score)
            
            # Record metrics
            self.metrics.record_selection(
                service,
                "health_aware_least_conn",
                selected.health_score
            )
            
            return selected
            
        finally:
            self.metrics.observe_selection_latency(
                service,
                "health_aware_least_conn",
                time.time() - start_time
            )

class AdaptiveHealthAware(LoadBalancerStrategy):
    """Adaptive strategy based on health trends."""
    
    def __init__(self, metrics: HealthAwareMetrics, config: HealthStrategyConfig):
        self.metrics = metrics
        self.config = config
        self._failure_counts: Dict[str, int] = {}
        self._last_health: Dict[str, float] = {}
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using adaptive health-aware strategy."""
        if not instances:
            return None
        
        start_time = time.time()
        try:
            # Update health trends
            for instance in instances:
                last_health = self._last_health.get(instance.id, 1.0)
                if instance.health_score < last_health:
                    self._failure_counts[instance.id] = \
                        self._failure_counts.get(instance.id, 0) + 1
                else:
                    self._failure_counts[instance.id] = 0
                self._last_health[instance.id] = instance.health_score
            
            # Filter instances
            viable = [
                i for i in instances
                if (i.health_score >= self.config.min_health_score and
                    self._failure_counts.get(i.id, 0) < self.config.max_consecutive_failures)
            ]
            
            if not viable:
                self.metrics.record_rejection(service, "no_viable_instances")
                return None
            
            # Prefer instances showing recovery
            recovering = [
                i for i in viable
                if i.health_score > self._last_health.get(i.id, 0)
            ]
            
            if recovering:
                selected = max(recovering, key=lambda i: i.health_score)
            else:
                selected = max(viable, key=lambda i: i.health_score)
            
            # Record metrics
            self.metrics.record_selection(
                service,
                "adaptive_health_aware",
                selected.health_score
            )
            
            return selected
            
        finally:
            self.metrics.observe_selection_latency(
                service,
                "adaptive_health_aware",
                time.time() - start_time
            ) 