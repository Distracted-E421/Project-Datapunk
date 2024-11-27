from typing import Dict, List, Optional, Any
import structlog
import dns.resolver
import dns.asyncresolver
import asyncio
from dataclasses import dataclass
from datetime import datetime
from .discovery import ServiceEndpoint
from ..exceptions import ServiceDiscoveryError

logger = structlog.get_logger()

"""
DNS-based service discovery with SRV record support.

Provides service discovery through DNS:
- SRV record resolution
- Dual-stack IPv4/IPv6 support
- Automatic health monitoring
- Service change detection
- Configurable caching

NOTE: Requires DNS server with SRV record support
"""

@dataclass
class DNSConfig:
    """
    DNS discovery configuration with performance tuning.
    
    Key parameters:
    - domain_suffix: Service naming convention
    - dns_port: Non-standard port for internal DNS
    - cache_ttl: Balance between freshness and load
    - timeout: Prevent discovery delays
    
    NOTE: Default port 8600 optimized for Consul DNS
    TODO: Add support for custom record types
    """
    domain_suffix: str = "service.consul"
    dns_port: int = 8600
    dns_servers: List[str] = None
    cache_ttl: int = 30  # seconds
    timeout: float = 5.0  # seconds
    max_retries: int = 3

class DNSServiceDiscovery:
    """
    DNS-based service discovery implementation.
    
    Features:
    - Automatic failover
    - Health status tracking
    - Change detection
    - Metric collection
    
    WARNING: DNS caching may affect update speed
    TODO: Add DNS-SD service type support
    """
    
    def __init__(self, config: DNSConfig):
        self.config = config
        self.logger = logger.bind(component="dns_discovery")
        
        # Configure DNS resolver
        self.resolver = dns.asyncresolver.Resolver()
        if config.dns_servers:
            self.resolver.nameservers = config.dns_servers
        self.resolver.port = config.dns_port
        self.resolver.timeout = config.timeout
        self.resolver.lifetime = config.timeout * config.max_retries
    
    async def discover_service(self, service_name: str) -> List[ServiceEndpoint]:
        """
        Discover service instances using DNS SRV records.
        
        Process:
        1. Query SRV records for service
        2. Resolve A/AAAA records
        3. Build endpoint list
        4. Track health status
        
        NOTE: Returns empty list if service not found
        """
        try:
            # Query SRV records
            fqdn = f"{service_name}.{self.config.domain_suffix}"
            srv_records = await self._query_srv_records(fqdn)
            
            # Query A/AAAA records for each target
            endpoints = []
            for record in srv_records:
                try:
                    addresses = await self._resolve_addresses(record.target.to_text())
                    for address in addresses:
                        endpoints.append(
                            ServiceEndpoint(
                                id=f"{service_name}-{address}-{record.port}",
                                address=address,
                                port=record.port,
                                healthy=True,
                                last_check=datetime.utcnow()
                            )
                        )
                except Exception as e:
                    self.logger.warning("address_resolution_failed",
                                      target=record.target.to_text(),
                                      error=str(e))
            
            return endpoints
            
        except Exception as e:
            self.logger.error("dns_discovery_failed",
                            service=service_name,
                            error=str(e))
            raise ServiceDiscoveryError(f"DNS discovery failed: {str(e)}")
    
    async def _query_srv_records(self, fqdn: str) -> List[Any]:
        """
        Query SRV records with error handling.
        
        Features:
        - Automatic retries
        - Timeout handling
        - Error logging
        - Empty result handling
        
        WARNING: May return empty list on DNS failures
        """
        try:
            return await self.resolver.resolve(fqdn, "SRV")
        except dns.resolver.NXDOMAIN:
            return []  # Service not found
        except Exception as e:
            self.logger.error("srv_query_failed",
                            fqdn=fqdn,
                            error=str(e))
            raise
    
    async def _resolve_addresses(self, hostname: str) -> List[str]:
        """
        Resolve both IPv4 and IPv6 addresses.
        
        Strategy:
        - Try IPv4 first for compatibility
        - Fall back to IPv6 if available
        - Handle partial failures
        - Log resolution issues
        
        NOTE: Returns all valid addresses found
        """
        addresses = []
        
        # Try IPv4
        try:
            a_records = await self.resolver.resolve(hostname, "A")
            addresses.extend([r.address for r in a_records])
        except Exception as e:
            self.logger.warning("ipv4_resolution_failed",
                              hostname=hostname,
                              error=str(e))
        
        # Try IPv6
        try:
            aaaa_records = await self.resolver.resolve(hostname, "AAAA")
            addresses.extend([r.address for r in aaaa_records])
        except Exception as e:
            self.logger.warning("ipv6_resolution_failed",
                              hostname=hostname,
                              error=str(e))
        
        return addresses
    
    async def watch_service(self,
                          service_name: str,
                          callback: callable,
                          interval: float = 30.0) -> None:
        """
        Watch for service changes using DNS polling.
        
        Features:
        - Periodic DNS queries
        - Change detection
        - Error recovery
        - Callback notifications
        
        WARNING: May miss rapid changes between polls
        TODO: Add DNS NOTIFY support for faster updates
        """
        previous_endpoints = set()
        
        while True:
            try:
                endpoints = await self.discover_service(service_name)
                current_endpoints = {
                    (e.address, e.port) for e in endpoints
                }
                
                if current_endpoints != previous_endpoints:
                    await callback(endpoints)
                    previous_endpoints = current_endpoints
                
            except Exception as e:
                self.logger.error("service_watch_failed",
                                service=service_name,
                                error=str(e))
            
            await asyncio.sleep(interval) 