# Service mesh integration module for Lake service
# Handles service discovery, health checks, and inter-service communication
# Part of the Infrastructure Layer (see sys-arch.mmd)

from typing import Dict, Any, Optional, List
import aiohttp
import asyncio
from datetime import datetime, timedelta
import consul.aio
from ..config.storage_config import StorageConfig
from ..core.logging import get_logger
from datapunk_shared.utils.retry import with_retry, RetryConfig
import json

logger = get_logger(__name__)

class MeshIntegrator:
    """
    Service mesh integration for Lake service communication
    
    Manages:
    - Service discovery via Consul
    - Health check reporting
    - Inter-service communication
    - Partition coordination and health
    """
    
    def __init__(self, config: StorageConfig):
        """
        Initialize mesh integration with retry policies
        
        IMPORTANT: Retry configuration is critical for mesh stability
        during network issues or service restarts
        """
        self.config = config
        self.consul_client = None
        self.service_cache = {}  # Cache for discovered services
        self.last_health_check = None
        self.partition_status = {}  # Track partition health
        self.retry_config = RetryConfig(
            max_attempts=5,    # Aligned with project retry policies
            base_delay=1.0,    # Start with 1s delay
            max_delay=30.0     # Cap at 30s to prevent excessive waits
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
        """Check health of mesh services including partitions"""
        health_status = {
            'stream': False,
            'nexus': False,
            'consul': False,
            'partitions': {}
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
                        
            # Add partition health status
            active_partitions = await self.list_active_partitions()
            
            for partition in active_partitions:
                partition_id = partition['id']
                health_status['partitions'][partition_id] = await self.check_partition_health(partition_id)
                
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            
        return health_status
    
    async def register_partition_service(self, partition_id: str, details: Dict[str, Any]):
        """Register a partition as a discoverable service"""
        service_def = {
            'name': f'datapunk-lake-partition-{partition_id}',
            'address': self.config.DB_HOST,
            'port': self.config.DB_PORT,
            'tags': ['storage', 'partition', partition_id],
            'meta': {
                'partition_type': details.get('type', 'default'),
                'data_pattern': details.get('pattern', 'general'),
                'size': str(details.get('size', 0)),
                'last_updated': str(datetime.utcnow())
            },
            'checks': [
                {
                    'http': f'http://{self.config.DB_HOST}:{self.config.DB_PORT}/partition/{partition_id}/health',
                    'interval': '10s',
                    'timeout': '5s'
                }
            ]
        }
        await self.consul_client.agent.service.register(**service_def)
        logger.info(f"Registered partition service: {partition_id}")

    async def deregister_partition_service(self, partition_id: str):
        """Deregister a partition service"""
        service_name = f'datapunk-lake-partition-{partition_id}'
        await self.consul_client.agent.service.deregister(service_name)
        logger.info(f"Deregistered partition service: {partition_id}")

    async def discover_partition(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Discover a specific partition's details"""
        service_name = f'datapunk-lake-partition-{partition_id}'
        return await self.discover_service(service_name)

    async def list_active_partitions(self) -> List[Dict[str, Any]]:
        """List all active and healthy partitions"""
        _, services = await self.consul_client.health.service('datapunk-lake-partition', passing=True)
        return [{
            'id': service['Service']['Service'].replace('datapunk-lake-partition-', ''),
            'address': service['Service']['Address'],
            'port': service['Service']['Port'],
            'meta': service['Service']['Meta'],
            'health': service['Checks'][0]['Status']
        } for service in services]

    async def update_partition_status(self, partition_id: str, status: Dict[str, Any]):
        """Update partition status in Consul KV store"""
        key = f'datapunk/lake/partitions/{partition_id}/status'
        value = json.dumps(status)
        await self.consul_client.kv.put(key, value)
        self.partition_status[partition_id] = status

    async def get_partition_status(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Get partition status from Consul KV store"""
        key = f'datapunk/lake/partitions/{partition_id}/status'
        _, data = await self.consul_client.kv.get(key)
        if data and data['Value']:
            return json.loads(data['Value'])
        return None

    async def check_partition_health(self, partition_id: str) -> Dict[str, Any]:
        """Check health of a specific partition"""
        health_status = {
            'id': partition_id,
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'unknown',
            'metrics': {}
        }
        
        try:
            # Check partition service health
            _, checks = await self.consul_client.health.checks(f'datapunk-lake-partition-{partition_id}')
            health_status['status'] = checks[0]['Status'] if checks else 'critical'
            
            # Get partition metrics
            status = await self.get_partition_status(partition_id)
            if status:
                health_status['metrics'] = status.get('metrics', {})
                
        except Exception as e:
            logger.error(f"Partition health check error: {str(e)}")
            health_status['status'] = 'critical'
            health_status['error'] = str(e)
            
        return health_status

    async def handle_partition_request(self, partition_id: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle requests for specific partitions"""
        try:
            partition = await self.discover_partition(partition_id)
            if not partition:
                raise ValueError(f"Partition {partition_id} not found")
                
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{partition['address']}:{partition['port']}/partition/{partition_id}/query",
                    json=request
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Failed to handle partition request: {str(e)}")
            return {"error": str(e)}