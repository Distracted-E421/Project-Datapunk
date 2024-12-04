from typing import Dict, List, Optional, Any
import structlog
import dns.resolver
import dns.asyncresolver
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from .registry import ServiceRegistration, ServiceMetadata
from ..exceptions import ServiceDiscoveryError
from ...cache import CacheClient

logger = structlog.get_logger()

@dataclass
class DNSResolverConfig:
    """
    DNS resolver configuration with caching and failover settings.
    
    Features:
    - Multiple DNS server support
    - Configurable timeouts
    - Cache TTL management
    - Failover retry settings
    """
    dns_servers: List[str]
    dns_port: int = 53
    timeout: float = 5.0
    cache_ttl: int = 30
    max_retries: int = 3
    failover_delay: float = 1.0
    enable_ipv6: bool = True
    prefer_ipv4: bool = True

class DNSServiceResolver:
    """
    Enhanced DNS resolver with caching and failover support.
    
    Features:
    - DNS-based service discovery
    - Multi-level caching
    - Automatic failover
    - Health monitoring
    - IPv4/IPv6 support
    """
    
    def __init__(
        self,
        config: DNSResolverConfig,
        cache_client: Optional[CacheClient] = None
    ):
        self.config = config
        self.cache = cache_client
        self.logger = logger.bind(component="dns_resolver")
        
        # Configure DNS resolver
        self.resolver = dns.asyncresolver.Resolver()
        if config.dns_servers:
            self.resolver.nameservers = config.dns_servers
        self.resolver.port = config.dns_port
        self.resolver.timeout = config.timeout
        self.resolver.lifetime = config.timeout * config.max_retries
        
        # Local in-memory cache
        self._local_cache: Dict[str, Any] = {}
        
    async def resolve_service(
        self,
        service_name: str,
        metadata_filter: Optional[Dict[str, str]] = None
    ) -> List[ServiceRegistration]:
        """
        Resolve service instances using DNS with caching.
        
        Process:
        1. Check local cache
        2. Check distributed cache
        3. Perform DNS lookup
        4. Update caches
        5. Apply metadata filters
        """
        try:
            # Check local cache first
            cached = self._get_from_local_cache(service_name)
            if cached:
                return self._filter_instances(cached, metadata_filter)
                
            # Check distributed cache if available
            if self.cache:
                cached = await self._get_from_distributed_cache(service_name)
                if cached:
                    return self._filter_instances(cached, metadata_filter)
                    
            # Perform DNS lookup
            instances = await self._resolve_dns(service_name)
            
            # Update caches
            self._update_local_cache(service_name, instances)
            if self.cache:
                await self._update_distributed_cache(service_name, instances)
                
            return self._filter_instances(instances, metadata_filter)
            
        except Exception as e:
            self.logger.error("dns_resolution_failed",
                            service=service_name,
                            error=str(e))
            raise ServiceDiscoveryError(f"DNS resolution failed: {str(e)}")
            
    async def _resolve_dns(self, service_name: str) -> List[ServiceRegistration]:
        """
        Perform DNS resolution with failover support.
        
        Features:
        - SRV record lookup
        - A/AAAA record resolution
        - Automatic retry
        - Failover handling
        """
        instances = []
        retries = 0
        
        while retries < self.config.max_retries:
            try:
                # Query SRV records
                srv_records = await self.resolver.resolve(
                    service_name,
                    "SRV"
                )
                
                # Process each SRV record
                for srv in srv_records:
                    try:
                        addresses = await self._resolve_addresses(
                            srv.target.to_text()
                        )
                        
                        for addr in addresses:
                            instances.append(
                                ServiceRegistration(
                                    id=f"{service_name}-{addr}-{srv.port}",
                                    service_name=service_name,
                                    host=addr,
                                    port=srv.port,
                                    metadata=ServiceMetadata(
                                        version="unknown",
                                        environment="unknown",
                                        region="unknown"
                                    )
                                )
                            )
                            
                    except Exception as e:
                        self.logger.warning(
                            "address_resolution_failed",
                            target=srv.target.to_text(),
                            error=str(e)
                        )
                        
                if instances:
                    break
                    
            except dns.resolver.NXDOMAIN:
                break  # Service doesn't exist
                
            except Exception as e:
                retries += 1
                if retries < self.config.max_retries:
                    await asyncio.sleep(
                        self.config.failover_delay * retries
                    )
                    continue
                raise
                
        return instances
        
    async def _resolve_addresses(self, hostname: str) -> List[str]:
        """
        Resolve both IPv4 and IPv6 addresses.
        
        Features:
        - Dual-stack support
        - Configurable preferences
        - Partial failure handling
        """
        addresses = []
        
        # Resolve IPv4
        if self.config.prefer_ipv4:
            try:
                a_records = await self.resolver.resolve(hostname, "A")
                addresses.extend(str(r) for r in a_records)
            except Exception as e:
                self.logger.warning("ipv4_resolution_failed",
                                  hostname=hostname,
                                  error=str(e))
                
        # Resolve IPv6 if enabled
        if self.config.enable_ipv6:
            try:
                aaaa_records = await self.resolver.resolve(hostname, "AAAA")
                addresses.extend(str(r) for r in aaaa_records)
            except Exception as e:
                self.logger.warning("ipv6_resolution_failed",
                                  hostname=hostname,
                                  error=str(e))
                
        # Fall back to IPv4 if no addresses found
        if not addresses and not self.config.prefer_ipv4:
            try:
                a_records = await self.resolver.resolve(hostname, "A")
                addresses.extend(str(r) for r in a_records)
            except Exception as e:
                self.logger.warning("ipv4_fallback_failed",
                                  hostname=hostname,
                                  error=str(e))
                
        return addresses
        
    def _get_from_local_cache(
        self,
        service_name: str
    ) -> Optional[List[ServiceRegistration]]:
        """Get service instances from local cache"""
        cached = self._local_cache.get(service_name)
        if not cached:
            return None
            
        # Check TTL
        age = (datetime.utcnow() - cached["timestamp"]).total_seconds()
        if age > self.config.cache_ttl:
            return None
            
        return cached["instances"]
        
    async def _get_from_distributed_cache(
        self,
        service_name: str
    ) -> Optional[List[ServiceRegistration]]:
        """Get service instances from distributed cache"""
        if not self.cache:
            return None
            
        try:
            cached = await self.cache.get(f"dns:{service_name}")
            if cached:
                return cached
        except Exception as e:
            self.logger.warning("distributed_cache_get_failed",
                              service=service_name,
                              error=str(e))
        return None
        
    def _update_local_cache(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ):
        """Update local cache with service instances"""
        self._local_cache[service_name] = {
            "instances": instances,
            "timestamp": datetime.utcnow()
        }
        
    async def _update_distributed_cache(
        self,
        service_name: str,
        instances: List[ServiceRegistration]
    ):
        """Update distributed cache with service instances"""
        if not self.cache:
            return
            
        try:
            await self.cache.set(
                f"dns:{service_name}",
                instances,
                ttl=timedelta(seconds=self.config.cache_ttl)
            )
        except Exception as e:
            self.logger.warning("distributed_cache_set_failed",
                              service=service_name,
                              error=str(e))
            
    def _filter_instances(
        self,
        instances: List[ServiceRegistration],
        metadata_filter: Optional[Dict[str, str]]
    ) -> List[ServiceRegistration]:
        """Filter instances based on metadata"""
        if not metadata_filter:
            return instances
            
        return [
            instance for instance in instances
            if all(
                instance.metadata.tags.get(k) == v
                for k, v in metadata_filter.items()
            )
        ] 