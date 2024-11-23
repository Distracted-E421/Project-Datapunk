from typing import Dict, Any, Optional
import aiohttp
import asyncio
from datetime import datetime, timedelta
import consul.aio
from ..config.storage_config import StorageConfig
from ..core.logging import get_logger
from datapunk_shared.utils.retry import with_retry, RetryConfig

logger = get_logger(__name__)

class MeshIntegrator:
    """Handles service mesh integration and communication"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.consul_client = None
        self.service_cache = {}
        self.last_health_check = None
        self.retry_config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=30.0
        )
        
    async def initialize(self):
        """Initialize mesh connections"""
        try:
            self.consul_client = consul.aio.Consul(
                host=self.config.CONSUL_HOST,
                port=self.config.CONSUL_PORT
            )
            await self.register_service()
            await self.start_health_checks()
            logger.info("Mesh integrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize mesh integrator: {str(e)}")
            raise
    
    async def register_service(self):
        """Register service with service discovery"""
        service_def = {
            'name': 'datapunk-lake',
            'address': self.config.DB_HOST,
            'port': self.config.DB_PORT,
            'tags': ['storage', 'database', 'lake'],
            'checks': [
                {
                    'http': f'http://{self.config.DB_HOST}:{self.config.DB_PORT}/health',
                    'interval': '10s',
                    'timeout': '5s'
                }
            ]
        }
        await self.consul_client.agent.service.register(**service_def)
    
    @with_retry(exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def discover_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Discover service with retry logic"""
        if service_name in self.service_cache:
            cached = self.service_cache[service_name]
            if datetime.now() - cached['timestamp'] < timedelta(minutes=5):
                return cached['data']

        _, services = await self.consul_client.health.service(service_name, passing=True)
        
        if not services:
            return None
            
        service = services[0]['Service']
        service_data = {
            'address': service['Address'],
            'port': service['Port'],
            'tags': service['Tags']
        }
        
        self.service_cache[service_name] = {
            'timestamp': datetime.now(),
            'data': service_data
        }
        
        return service_data
    
    @with_retry(exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
    async def handle_stream_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle stream data with retry logic"""
        stream_service = await self.discover_service('datapunk-stream')
        if not stream_service:
            raise ServiceDiscoveryError("Stream service not found")
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{stream_service['address']}:{stream_service['port']}/ingest",
                json=data
            ) as response:
                return await response.json()
    
    async def handle_nexus_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests from nexus service"""
        try:
            nexus_service = await self.discover_service('datapunk-nexus')
            if not nexus_service:
                raise ValueError("Nexus service not found")
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{nexus_service['address']}:{nexus_service['port']}/query",
                    json=request
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to handle nexus request: {str(e)}")
            return {"error": str(e)}
    
    async def start_health_checks(self):
        """Start periodic health checks"""
        while True:
            try:
                health_status = await self.check_mesh_health()
                self.last_health_check = {
                    'timestamp': datetime.utcnow(),
                    'status': health_status
                }
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Health check failed: {str(e)}")
                await asyncio.sleep(5)  # Shorter retry interval on failure
    
    async def check_mesh_health(self) -> Dict[str, Any]:
        """Check health of mesh services"""
        health_status = {
            'stream': False,
            'nexus': False,
            'consul': False
        }
        
        try:
            # Check Consul
            leader = await self.consul_client.status.leader()
            health_status['consul'] = bool(leader)
            
            # Check Stream
            stream = await self.discover_service('datapunk-stream')
            if stream:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{stream['address']}:{stream['port']}/health"
                    ) as response:
                        health_status['stream'] = response.status == 200
            
            # Check Nexus
            nexus = await self.discover_service('datapunk-nexus')
            if nexus:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"http://{nexus['address']}:{nexus['port']}/health"
                    ) as response:
                        health_status['nexus'] = response.status == 200
                        
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            
        return health_status 