from typing import Dict, List, Optional, Any
import structlog
import consul
import aiohttp
import asyncio
from dataclasses import dataclass
from datetime import datetime
from .metrics import ServiceDiscoveryMetrics
from ..cache import CacheClient
from ..tracing import trace_method
from ..exceptions import ServiceDiscoveryError

logger = structlog.get_logger()

"""
Service discovery implementation with caching and health monitoring.

Provides:
- Service registration and deregistration
- Health check integration
- Cached service discovery
- Real-time service watching
- Performance metrics collection

NOTE: Requires running Consul instance for service discovery
"""

@dataclass
class ServiceEndpoint:
    """
    Service endpoint representation with health status.
    
    Tracks:
    - Instance identity and location
    - Health status and history
    - Custom metadata
    
    NOTE: metadata used for routing decisions
    """
    id: str
    address: str
    port: int
    healthy: bool = True
    last_check: Optional[datetime] = None
    metadata: Dict[str, str] = None

@dataclass
class ServiceDiscoveryConfig:
    """
    Discovery configuration with performance tuning.
    
    Key settings:
    - Cache TTL balances freshness vs performance
    - Health check interval affects detection speed
    - Deregister timeout handles ungraceful shutdowns
    
    TODO: Add support for custom health check endpoints
    """
    consul_host: str = "consul"
    consul_port: int = 8500
    cache_ttl: int = 30  # seconds
    health_check_interval: int = 10  # seconds
    deregister_critical_timeout: str = "1m"
    enable_caching: bool = True

class ServiceDiscoveryManager:
    """
    Manages service discovery and health monitoring.
    
    Features:
    - Automatic service registration
    - Cached service lookups
    - Health status tracking
    - Real-time updates
    
    WARNING: Cache may briefly serve stale data
    TODO: Add circuit breaker for Consul failures
    """
    
    def __init__(self,
                 config: ServiceDiscoveryConfig,
                 cache_client: Optional[CacheClient] = None,
                 metrics_client = None):
        self.config = config
        self.consul = consul.Consul(
            host=config.consul_host,
            port=config.consul_port
        )
        self.cache = cache_client
        self.metrics = ServiceDiscoveryMetrics(metrics_client)
        self.logger = logger.bind(component="service_discovery")
        
        # Local cache for quick lookups
        self._local_cache: Dict[str, List[ServiceEndpoint]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    @trace_method("register_service")
    async def register_service(self,
                             service_name: str,
                             host: str,
                             port: int,
                             tags: List[str] = None,
                             metadata: Dict[str, str] = None) -> str:
        """
        Register service with health check configuration.
        
        Process:
        1. Create unique service ID
        2. Configure health check
        3. Register with Consul
        4. Start monitoring
        
        NOTE: Health check uses HTTP endpoint by default
        """
        try:
            service_id = f"{service_name}-{host}-{port}"
            
            # Create service definition
            service_def = {
                "Name": service_name,
                "ID": service_id,
                "Address": host,
                "Port": port,
                "Tags": tags or [],
                "Meta": metadata or {},
                "Check": {
                    "HTTP": f"http://{host}:{port}/health",
                    "Method": "GET",
                    "Interval": f"{self.config.health_check_interval}s",
                    "Timeout": "5s",
                    "DeregisterCriticalServiceAfter": self.config.deregister_critical_timeout
                }
            }
            
            # Register with Consul
            self.consul.agent.service.register(**service_def)
            
            # Update metrics
            self.metrics.record_registration(service_name)
            
            self.logger.info("service_registered",
                           service_name=service_name,
                           service_id=service_id)
            
            return service_id
            
        except Exception as e:
            self.logger.error("service_registration_failed",
                            service_name=service_name,
                            error=str(e))
            raise ServiceDiscoveryError(f"Failed to register service: {str(e)}")
    
    @trace_method("discover_service")
    async def discover_service(self,
                             service_name: str,
                             use_cache: bool = True) -> List[ServiceEndpoint]:
        """
        Discover healthy service instances with caching.
        
        Features:
        - Cache-first lookups for performance
        - Automatic cache updates
        - Health status filtering
        - Metric collection
        
        NOTE: Only returns healthy instances
        """
        try:
            # Check cache first if enabled
            if use_cache and self.config.enable_caching:
                cached = await self._get_cached_service(service_name)
                if cached:
                    return cached
            
            # Query Consul for healthy instances
            _, nodes = await self.consul.health.service(
                service_name,
                passing=True
            )
            
            endpoints = [
                ServiceEndpoint(
                    id=node["Service"]["ID"],
                    address=node["Service"]["Address"],
                    port=node["Service"]["Port"],
                    healthy=True,
                    last_check=datetime.utcnow(),
                    metadata=node["Service"].get("Meta", {})
                )
                for node in nodes
            ]
            
            # Update cache
            if self.config.enable_caching:
                await self._cache_service_endpoints(service_name, endpoints)
            
            # Update metrics
            self.metrics.record_discovery(
                service_name,
                len(endpoints),
                cached=False
            )
            
            return endpoints
            
        except Exception as e:
            self.logger.error("service_discovery_failed",
                            service_name=service_name,
                            error=str(e))
            raise ServiceDiscoveryError(f"Failed to discover service: {str(e)}")
    
    @trace_method("watch_service")
    async def watch_service(self,
                          service_name: str,
                          callback: callable) -> None:
        """
        Watch for service changes in real-time.
        
        Uses:
        - Long polling for efficiency
        - Automatic reconnection
        - Error backoff
        - Cache updates
        
        WARNING: May miss updates during reconnection
        """
        index = None
        while True:
            try:
                # Long polling for changes
                index, nodes = await self.consul.health.service(
                    service_name,
                    index=index,
                    passing=True,
                    wait="30s"
                )
                
                endpoints = [
                    ServiceEndpoint(
                        id=node["Service"]["ID"],
                        address=node["Service"]["Address"],
                        port=node["Service"]["Port"],
                        healthy=True,
                        last_check=datetime.utcnow(),
                        metadata=node["Service"].get("Meta", {})
                    )
                    for node in nodes
                ]
                
                # Update cache
                if self.config.enable_caching:
                    await self._cache_service_endpoints(service_name, endpoints)
                
                # Notify callback
                await callback(endpoints)
                
            except Exception as e:
                self.logger.error("service_watch_error",
                                service_name=service_name,
                                error=str(e))
                await asyncio.sleep(5)  # Backoff on error
    
    async def _get_cached_service(self,
                                service_name: str) -> Optional[List[ServiceEndpoint]]:
        """
        Retrieve service endpoints from cache.
        
        Features:
        - Fast lookup path
        - Metric tracking
        - Error handling
        
        NOTE: Returns None on cache miss or error
        """
        if not self.cache:
            return None
            
        try:
            cache_key = f"service:discovery:{service_name}"
            cached = await self.cache.get(cache_key)
            
            if cached:
                self.metrics.record_discovery(
                    service_name,
                    len(cached),
                    cached=True
                )
                return [ServiceEndpoint(**endpoint) for endpoint in cached]
                
        except Exception as e:
            self.logger.warning("cache_retrieval_failed",
                              service_name=service_name,
                              error=str(e))
            
        return None
    
    async def _cache_service_endpoints(self,
                                     service_name: str,
                                     endpoints: List[ServiceEndpoint]) -> None:
        """
        Cache service endpoints for future lookups.
        
        Process:
        - Serialize endpoints
        - Set cache TTL
        - Update metrics
        
        NOTE: Failures logged but not propagated
        """
        if not self.cache:
            return
            
        try:
            cache_key = f"service:discovery:{service_name}"
            await self.cache.set(
                cache_key,
                [vars(endpoint) for endpoint in endpoints],
                ttl=self.config.cache_ttl
            )
            
        except Exception as e:
            self.logger.warning("cache_update_failed",
                              service_name=service_name,
                              error=str(e))