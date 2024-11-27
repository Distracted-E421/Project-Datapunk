"""
Advanced Load Balancing System

Implements sophisticated load balancing strategies for the Datapunk service mesh,
providing resource-aware, geographical, adaptive, and consistent hashing algorithms.
Designed to optimize service distribution while maintaining performance and reliability.

Key Features:
- Resource utilization awareness
- Geographical proximity routing
- Adaptive performance-based balancing
- Consistent hashing support
- Circuit breaker integration
- Performance metrics tracking

NOTE: Strategy selection impacts both performance and resource distribution.
Choose based on specific service requirements and infrastructure capabilities.
"""

from typing import List, Dict, Optional, Any
import structlog
import random
import time
from dataclasses import dataclass
from .load_balancer_strategies import LoadBalancerStrategy, ServiceInstance
from ..health.health_checks import HealthCheckResult, HealthStatus
from ..monitoring import MetricsClient

logger = structlog.get_logger()

@dataclass
class LoadBalancerConfig:
    """
    Configuration for advanced load balancing strategies.
    
    Thresholds and windows are tuned for typical microservice deployments.
    Adjust based on specific service characteristics and SLA requirements.
    
    TODO: Add support for dynamic threshold adjustment
    TODO: Implement A/B testing for strategy optimization
    """
    health_threshold: float = 0.5    # Minimum health score for instance selection
    latency_threshold: float = 1.0   # Maximum acceptable latency (seconds)
    max_retries: int = 3             # Maximum retry attempts
    circuit_breaker_threshold: int = 5  # Failures before circuit breaks
    window_size: int = 60            # Monitoring window (seconds)

class ResourceAwareStrategy(LoadBalancerStrategy):
    """
    Load balancing based on resource utilization metrics.
    
    Selects instances based on weighted combination of:
    - CPU usage (40% weight)
    - Memory usage (30% weight)
    - Connection count (30% weight)
    
    IMPORTANT: Requires accurate resource metrics from instances.
    Falls back to random selection if metrics unavailable.
    """
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """
        Select instance with lowest resource utilization score.
        
        Score calculation:
        score = (cpu_score * 0.4 + memory_score * 0.3 + conn_score * 0.3) / health_score
        Lower scores indicate better resource availability.
        """
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        def load_score(instance: ServiceInstance) -> float:
            cpu_weight = 0.4
            memory_weight = 0.3
            conn_weight = 0.3
            
            # Default to 50% utilization if metric unavailable
            cpu_score = instance.metadata.get("cpu_usage", 0.5)
            memory_score = instance.metadata.get("memory_usage", 0.5)
            conn_score = instance.active_connections / 100 if instance.active_connections else 0
            
            return (
                cpu_score * cpu_weight +
                memory_score * memory_weight +
                conn_score * conn_weight
            ) / instance.health_score
        
        return min(healthy, key=load_score)

class GeographicalStrategy(LoadBalancerStrategy):
    """
    Load balancing based on geographical proximity.
    
    Prioritizes instances in same region as client to minimize latency.
    Falls back to random selection if no same-region instances available.
    
    NOTE: Requires region metadata in instance configuration.
    Consider implementing distance-based selection for more precise routing.
    """
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance],
                       client_region: Optional[str] = None) -> Optional[ServiceInstance]:
        """
        Select instance based on geographical proximity to client.
        
        Prioritization:
        1. Healthy instances in same region
        2. Random healthy instance (fallback)
        """
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        if client_region:
            same_region = [
                i for i in healthy
                if i.metadata.get("region") == client_region
            ]
            if same_region:
                return random.choice(same_region)
        
        return random.choice(healthy)

class AdaptiveStrategy(LoadBalancerStrategy):
    """
    Adaptive load balancing based on performance metrics.
    
    Dynamically adjusts instance selection based on:
    - Historical performance
    - Error rates
    - Health scores
    - Circuit breaker status
    
    Features automatic recovery through gradual score improvement
    and circuit breaker reset after successful operations.
    """
    
    def __init__(self, metrics: MetricsClient, config: LoadBalancerConfig):
        """
        Initialize adaptive strategy with performance tracking.
        
        Maintains separate scores for performance and errors to enable
        fine-grained control over instance selection.
        """
        super().__init__(metrics)
        self.config = config
        self._performance_scores: Dict[str, float] = {}
        self._error_counts: Dict[str, int] = {}
        self._last_reset = time.time()
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """
        Select instance using adaptive scoring.
        
        Score calculation combines:
        - Base performance score
        - Error penalty
        - Health score bonus
        
        Periodic reset prevents score stagnation and enables recovery.
        """
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        # Reset metrics periodically to enable recovery
        current_time = time.time()
        if current_time - self._last_reset > self.config.window_size:
            self._performance_scores.clear()
            self._error_counts.clear()
            self._last_reset = current_time
        
        def adaptive_score(instance: ServiceInstance) -> float:
            base_score = self._performance_scores.get(instance.id, 0.5)
            error_penalty = self._error_counts.get(instance.id, 0) * 0.1
            health_bonus = instance.health_score
            
            return (base_score + health_bonus) / (1 + error_penalty)
        
        return max(healthy, key=adaptive_score)

class ConsistentHashingStrategy(LoadBalancerStrategy):
    """
    Load balancing using consistent hashing algorithm.
    
    Provides stable instance selection based on request keys,
    minimizing redistribution during instance changes.
    
    Features:
    - Multiple virtual nodes per instance
    - Hash ring implementation
    - Fallback to random selection
    
    NOTE: Hash ring rebuilds can impact performance during
    instance changes. Consider implementing incremental updates.
    """
    
    def __init__(self, metrics: MetricsClient, replicas: int = 100):
        """
        Initialize consistent hashing ring.
        
        Higher replica counts provide better distribution but
        increase memory usage and ring rebuild time.
        """
        super().__init__(metrics)
        self.replicas = replicas
        self._hash_ring: Dict[int, str] = {}
    
    def _hash_key(self, key: str) -> int:
        """Generate consistent hash for key."""
        return hash(key)
    
    def _build_ring(self, instances: List[ServiceInstance]):
        """
        Build hash ring from available instances.
        
        Creates multiple virtual nodes per instance to improve
        distribution uniformity.
        """
        self._hash_ring.clear()
        for instance in instances:
            for i in range(self.replicas):
                hash_key = self._hash_key(f"{instance.id}:{i}")
                self._hash_ring[hash_key] = instance.id
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance],
                       key: Optional[str] = None) -> Optional[ServiceInstance]:
        """
        Select instance using consistent hashing.
        
        Process:
        1. Build/update hash ring
        2. Hash request key
        3. Find next highest hash in ring
        4. Map back to instance
        
        Falls back to random selection if no key provided.
        """
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        self._build_ring(healthy)
        
        if not key:
            return random.choice(healthy)
        
        hash_key = self._hash_key(key)
        ring_keys = sorted(self._hash_ring.keys())
        
        for ring_key in ring_keys:
            if ring_key >= hash_key:
                instance_id = self._hash_ring[ring_key]
                return next(i for i in healthy if i.id == instance_id)
        
        # Wrap around to first key if necessary
        instance_id = self._hash_ring[ring_keys[0]]
        return next(i for i in healthy if i.id == instance_id) 