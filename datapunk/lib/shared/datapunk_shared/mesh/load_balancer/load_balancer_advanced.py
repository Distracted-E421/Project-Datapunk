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
    """Configuration for advanced load balancer."""
    health_threshold: float = 0.5
    latency_threshold: float = 1.0  # seconds
    max_retries: int = 3
    circuit_breaker_threshold: int = 5
    window_size: int = 60  # seconds

class ResourceAwareStrategy(LoadBalancerStrategy):
    """Load balancing based on resource utilization."""
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance based on resource availability."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        # Calculate load score based on CPU, memory, and connections
        def load_score(instance: ServiceInstance) -> float:
            cpu_weight = 0.4
            memory_weight = 0.3
            conn_weight = 0.3
            
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
    """Load balancing based on geographical proximity."""
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance],
                       client_region: Optional[str] = None) -> Optional[ServiceInstance]:
        """Select instance based on geographical proximity."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        if client_region:
            # Prefer instances in same region
            same_region = [
                i for i in healthy
                if i.metadata.get("region") == client_region
            ]
            if same_region:
                return random.choice(same_region)
        
        # Fallback to random selection
        return random.choice(healthy)

class AdaptiveStrategy(LoadBalancerStrategy):
    """Adaptive load balancing based on performance metrics."""
    
    def __init__(self, metrics: MetricsClient, config: LoadBalancerConfig):
        super().__init__(metrics)
        self.config = config
        self._performance_scores: Dict[str, float] = {}
        self._error_counts: Dict[str, int] = {}
        self._last_reset = time.time()
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance]) -> Optional[ServiceInstance]:
        """Select instance using adaptive strategy."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        # Reset metrics periodically
        current_time = time.time()
        if current_time - self._last_reset > self.config.window_size:
            self._performance_scores.clear()
            self._error_counts.clear()
            self._last_reset = current_time
        
        # Calculate adaptive score
        def adaptive_score(instance: ServiceInstance) -> float:
            base_score = self._performance_scores.get(instance.id, 0.5)
            error_penalty = self._error_counts.get(instance.id, 0) * 0.1
            health_bonus = instance.health_score
            
            return (base_score + health_bonus) / (1 + error_penalty)
        
        return max(healthy, key=adaptive_score)
    
    def record_latency(self, instance_id: str, latency: float):
        """Record request latency for instance."""
        current_score = self._performance_scores.get(instance_id, 0.5)
        
        # Update score based on latency
        if latency > self.config.latency_threshold:
            self._performance_scores[instance_id] = max(0.1, current_score - 0.1)
        else:
            self._performance_scores[instance_id] = min(1.0, current_score + 0.05)
    
    def record_error(self, instance_id: str):
        """Record error for instance."""
        self._error_counts[instance_id] = self._error_counts.get(instance_id, 0) + 1
        
        # Circuit breaker logic
        if self._error_counts[instance_id] >= self.config.circuit_breaker_threshold:
            self._performance_scores[instance_id] = 0.0

class ConsistentHashingStrategy(LoadBalancerStrategy):
    """Load balancing using consistent hashing."""
    
    def __init__(self, metrics: MetricsClient, replicas: int = 100):
        super().__init__(metrics)
        self.replicas = replicas
        self._hash_ring: Dict[int, str] = {}
    
    def _hash_key(self, key: str) -> int:
        """Generate hash for key."""
        return hash(key)
    
    def _build_ring(self, instances: List[ServiceInstance]):
        """Build hash ring from instances."""
        self._hash_ring.clear()
        for instance in instances:
            for i in range(self.replicas):
                hash_key = self._hash_key(f"{instance.id}:{i}")
                self._hash_ring[hash_key] = instance.id
    
    def select_instance(self,
                       service: str,
                       instances: List[ServiceInstance],
                       key: Optional[str] = None) -> Optional[ServiceInstance]:
        """Select instance using consistent hashing."""
        healthy = self._filter_healthy(instances)
        if not healthy:
            return None
        
        # Rebuild ring if needed
        self._build_ring(healthy)
        
        if not key:
            return random.choice(healthy)
        
        # Find instance on hash ring
        hash_key = self._hash_key(key)
        ring_keys = sorted(self._hash_ring.keys())
        
        for ring_key in ring_keys:
            if ring_key >= hash_key:
                instance_id = self._hash_ring[ring_key]
                return next(i for i in healthy if i.id == instance_id)
        
        # Wrap around to first key
        instance_id = self._hash_ring[ring_keys[0]]
        return next(i for i in healthy if i.id == instance_id) 