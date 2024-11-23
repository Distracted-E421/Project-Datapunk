from typing import Dict, Any, Optional, List
import asyncio
import consul.aio
import structlog
from datetime import datetime, timedelta
from ..utils.retry import with_retry, RetryConfig

logger = structlog.get_logger(__name__)

class ServiceDiscovery:
    """Service discovery using Consul"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.consul_client = None
        self.service_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = timedelta(minutes=5)
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
        
    async def initialize(self):
        """Initialize Consul client"""
        try:
            self.consul_client = consul.aio.Consul(
                host=self.config.get('consul_host', 'consul'),
                port=self.config.get('consul_port', 8500),
                scheme=self.config.get('consul_scheme', 'http')
            )
            logger.info("Service discovery initialized")
        except Exception as e:
            logger.error("Failed to initialize service discovery", error=str(e))
            raise
    
    @with_retry()
    async def register_service(
        self,
        service_name: str,
        host: str,
        port: int,
        tags: List[str] = None,
        health_check_url: Optional[str] = None
    ) -> bool:
        """Register service with Consul"""
        try:
            service_id = f"{service_name}-{host}-{port}"
            service_def = {
                'name': service_name,
                'service_id': service_id,
                'address': host,
                'port': port,
                'tags': tags or []
            }
            
            if health_check_url:
                service_def['check'] = {
                    'http': health_check_url,
                    'interval': '10s',
                    'timeout': '5s',
                    'deregister_critical_service_after': '1m'
                }
            
            await self.consul_client.agent.service.register(**service_def)
            logger.info(f"Service registered: {service_name}", service_id=service_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service: {service_name}", error=str(e))
            raise
    
    @with_retry()
    async def deregister_service(self, service_id: str) -> bool:
        """Deregister service from Consul"""
        try:
            await self.consul_client.agent.service.deregister(service_id)
            logger.info(f"Service deregistered", service_id=service_id)
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service", service_id=service_id, error=str(e))
            raise
    
    @with_retry()
    async def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover service with caching"""
        # Check cache first
        if service_name in self.service_cache:
            cached = self.service_cache[service_name]
            if datetime.now() - cached['timestamp'] < self.cache_ttl:
                return cached['data']
        
        try:
            _, services = await self.consul_client.health.service(
                service_name,
                passing=True
            )
            
            if not services:
                logger.warning(f"No healthy instances found", service=service_name)
                return None
            
            # Basic load balancing - round robin
            service = services[0]['Service']
            service_data = {
                'id': service['ID'],
                'address': service['Address'],
                'port': service['Port'],
                'tags': service['Tags'],
                'meta': service.get('Meta', {})
            }
            
            # Update cache
            self.service_cache[service_name] = {
                'timestamp': datetime.now(),
                'data': service_data
            }
            
            return service_data
            
        except Exception as e:
            logger.error(f"Service discovery failed", service=service_name, error=str(e))
            raise
    
    async def watch_service_health(self, service_name: str, callback):
        """Watch service health changes"""
        index = None
        while True:
            try:
                index, services = await self.consul_client.health.service(
                    service_name,
                    index=index,
                    wait='30s'
                )
                await callback(services)
            except Exception as e:
                logger.error(f"Health watch failed", service=service_name, error=str(e))
                await asyncio.sleep(5)  # Back off on error 