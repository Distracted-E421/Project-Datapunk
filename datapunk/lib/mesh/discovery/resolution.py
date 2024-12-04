from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from .registry import ServiceRegistry, ServiceRegistration, ServiceStatus
from ..routing.balancer import LoadBalancer, BalancingStrategy
from ...monitoring import MetricsCollector

"""
Service Resolution Implementation for Datapunk Service Mesh

This module provides intelligent service instance selection with:
- Multiple resolution strategies (direct, load balanced, nearest, etc.)
- Instance caching for performance
- Health-aware selection
- Region-aware routing
- Automatic failover

The resolver works with the service registry to implement higher-level
routing policies that support reliable service communication.

TODO: Add support for capability-based routing
TODO: Implement adaptive cache TTLs based on service stability
FIXME: Improve weighted distribution for large instance counts
"""

class ResolutionStrategy(Enum):
    """
    Service resolution strategies for different routing needs.
    
    Each strategy optimizes for different requirements:
    DIRECT: Lowest latency, no guarantees
    LOAD_BALANCED: Even distribution
    NEAREST: Network locality
    FAILOVER: High availability
    WEIGHTED: Traffic shaping
    """
    DIRECT = "direct"          # Fast path for simple cases
    LOAD_BALANCED = "load_balanced"  # Even traffic distribution
    NEAREST = "nearest"        # Network locality optimization
    FAILOVER = "failover"      # High availability with backup
    WEIGHTED = "weighted"      # Controlled traffic distribution

@dataclass
class ResolutionConfig:
    """
    Configuration for service resolution behavior.
    
    Timeouts and thresholds are tuned for:
    - Typical network latencies
    - Cache coherency requirements
    - Failover responsiveness
    
    NOTE: refresh_interval should be shorter than cache_ttl
    TODO: Add support for strategy-specific configurations
    """
    strategy: ResolutionStrategy = ResolutionStrategy.LOAD_BALANCED
    refresh_interval: float = 30.0  # Background refresh rate
    cache_ttl: int = 300  # Cache entry lifetime
    enable_health_filtering: bool = True  # Filter unhealthy instances
    enable_caching: bool = True  # Cache resolution results
    failover_threshold: int = 3  # Failed attempts before failover
    weighted_distribution: Optional[Dict[str, int]] = None  # Region weights
    preferred_regions: Optional[List[str]] = None  # Region preference order
    local_region: Optional[str] = None  # Current deployment region

class ServiceResolver:
    """
    Service instance resolver with multiple selection strategies.
    
    Core responsibilities:
    - Select appropriate instances based on strategy
    - Maintain resolution cache
    - Handle instance health
    - Manage load balancers
    - Track resolution metrics
    
    The resolver uses background refresh to:
    - Keep cache fresh
    - Update load balancer state
    - Maintain accurate health status
    
    NOTE: All public methods are thread-safe through async locking
    FIXME: Improve cache memory usage for many services
    """
    def __init__(
        self,
        config: ResolutionConfig,
        registry: ServiceRegistry,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.registry = registry
        self.metrics = metrics_collector
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_balancers: Dict[str, LoadBalancer] = {}
        self._refresh_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start resolver background tasks"""
        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def stop(self):
        """Stop resolver background tasks"""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass

    async def resolve(
        self,
        service_name: str,
        metadata_filter: Optional[Dict[str, str]] = None
    ) -> Optional[ServiceRegistration]:
        """
        Resolve service instance using configured strategy.
        
        Resolution process:
        1. Check cache if enabled
        2. Get healthy instances
        3. Apply resolution strategy
        4. Update cache
        5. Record metrics
        
        NOTE: Returns None if no suitable instances found
        """
        try:
            if self.config.enable_caching:
                cached = self._get_from_cache(service_name)
                if cached:
                    return cached

            instances = await self._get_healthy_instances(
                service_name,
                metadata_filter
            )
            
            if not instances:
                if self.metrics:
                    await self.metrics.increment(
                        "discovery.resolution.no_instances",
                        tags={"service": service_name}
                    )
                return None

            instance = await self._select_instance(service_name, instances)
            
            if instance and self.config.enable_caching:
                self._update_cache(service_name, instance)

            if self.metrics:
                await self.metrics.increment(
                    "discovery.resolution.success",
                    tags={
                        "service": service_name,
                        "strategy": self.config.strategy.value
                    }
                )

            return instance

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "discovery.resolution.error",
                    tags={
                        "service": service_name,
                        "error": str(e)
                    }
                )
            raise

    async def _get_healthy_instances(
        self,
        service_name: str,
        metadata_filter: Optional[Dict[str, str]] = None
    ) -> List[ServiceRegistration]:
        """Get healthy service instances"""
        instances = await self.registry.get_services(
            service_name=service_name,
            status=ServiceStatus.RUNNING if self.config.enable_health_filtering else None,
            metadata_filter=metadata_filter
        )
        return instances

    async def _select_instance(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ) -> Optional[ServiceRegistration]:
        """Select instance based on resolution strategy"""
        if not instances:
            return None

        if self.config.strategy == ResolutionStrategy.DIRECT:
            return instances[0]

        elif self.config.strategy == ResolutionStrategy.LOAD_BALANCED:
            return await self._get_load_balanced_instance(service_name, instances)

        elif self.config.strategy == ResolutionStrategy.NEAREST:
            return self._get_nearest_instance(instances)

        elif self.config.strategy == ResolutionStrategy.FAILOVER:
            return await self._get_failover_instance(service_name, instances)

        elif self.config.strategy == ResolutionStrategy.WEIGHTED:
            return self._get_weighted_instance(instances)

        return instances[0]

    async def _get_load_balanced_instance(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ) -> Optional[ServiceRegistration]:
        """Get load balanced instance"""
        balancer = self._get_or_create_balancer(service_name)
        
        # Update balancer with current instances
        for instance in instances:
            await balancer.add_instance(instance)
            
        return await balancer.get_instance()

    def _get_nearest_instance(
        self,
        instances: List[ServiceRegistration]
    ) -> Optional[ServiceRegistration]:
        """Get nearest instance based on region/zone"""
        if not self.config.local_region:
            return instances[0]

        # Try to find instance in local region
        for instance in instances:
            if instance.metadata.region == self.config.local_region:
                return instance

        # Try preferred regions in order
        if self.config.preferred_regions:
            for region in self.config.preferred_regions:
                for instance in instances:
                    if instance.metadata.region == region:
                        return instance

        return instances[0]

    async def _get_failover_instance(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ) -> Optional[ServiceRegistration]:
        """
        Select instance with automatic failover support.
        
        Implements a simple failover strategy:
        1. Try primary instance first
        2. Track failed attempts
        3. Switch to backup after threshold
        4. Reset counter periodically
        
        NOTE: Requires at least two instances for full failover
        TODO: Add support for multiple backup instances
        """
        cache_key = f"failover_{service_name}"
        failover_count = self._cache.get(cache_key, {}).get("count", 0)

        if failover_count >= self.config.failover_threshold:
            # Reset failover count and try secondary instances
            self._cache[cache_key] = {"count": 0}
            return instances[1] if len(instances) > 1 else instances[0]

        # Try primary instance
        primary = instances[0]
        if primary.status == ServiceStatus.RUNNING:
            return primary

        # Update failover count
        self._cache[cache_key] = {"count": failover_count + 1}
        return instances[1] if len(instances) > 1 else None

    def _get_weighted_instance(
        self,
        instances: List[ServiceRegistration]
    ) -> Optional[ServiceRegistration]:
        """
        Select instance based on weighted distribution.
        
        Uses weighted random selection to:
        - Control traffic distribution
        - Support gradual rollout
        - Enable A/B testing
        
        FIXME: Current implementation may be biased for small weights
        TODO: Add support for dynamic weight adjustment
        """
        if not self.config.weighted_distribution:
            return instances[0]

        total_weight = sum(
            self.config.weighted_distribution.get(i.metadata.region, 1)
            for i in instances
        )

        if total_weight == 0:
            return instances[0]

        import random
        point = random.randint(0, total_weight - 1)
        
        for instance in instances:
            weight = self.config.weighted_distribution.get(
                instance.metadata.region,
                1
            )
            if point < weight:
                return instance
            point -= weight

        return instances[0]

    def _get_or_create_balancer(self, service_name: str) -> LoadBalancer:
        """Get or create load balancer for service"""
        if service_name not in self._load_balancers:
            self._load_balancers[service_name] = LoadBalancer(
                strategy=BalancingStrategy.ROUND_ROBIN,
                metrics_collector=self.metrics
            )
        return self._load_balancers[service_name]

    def _get_from_cache(
        self,
        service_name: str
    ) -> Optional[ServiceRegistration]:
        """Get service instance from cache"""
        cached = self._cache.get(service_name)
        if not cached:
            return None

        # Check TTL
        age = (datetime.utcnow() - cached["timestamp"]).total_seconds()
        if age > self.config.cache_ttl:
            return None

        return cached["instance"]

    def _update_cache(
        self,
        service_name: str,
        instance: ServiceRegistration
    ):
        """Update service instance cache"""
        self._cache[service_name] = {
            "instance": instance,
            "timestamp": datetime.utcnow()
        }

    async def _refresh_loop(self):
        """Periodic refresh of service instances"""
        while True:
            try:
                await asyncio.sleep(self.config.refresh_interval)
                await self._refresh_instances()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "discovery.refresh.error",
                        tags={"error": str(e)}
                    )

    async def _refresh_instances(self):
        """
        Refresh cached instance data and load balancer state.
        
        Critical for maintaining:
        - Cache freshness
        - Load balancer accuracy
        - Health status
        
        NOTE: Holds lock during refresh to prevent inconsistency
        TODO: Consider incremental updates for large services
        """
        async with self._lock:
            # Clear cache
            self._cache.clear()
            
            # Update load balancers
            for service_name, balancer in self._load_balancers.items():
                instances = await self._get_healthy_instances(service_name, None)
                for instance in instances:
                    await balancer.add_instance(instance)

    async def get_resolution_stats(self) -> Dict[str, Any]:
        """Get resolution statistics"""
        return {
            "cached_services": len(self._cache),
            "load_balancers": len(self._load_balancers),
            "strategy": self.config.strategy.value,
            "cache_enabled": self.config.enable_caching,
            "health_filtering": self.config.enable_health_filtering
        }