"""
Service Discovery Integration

Implements dynamic service discovery and connection management with:
- Service registration and deregistration
- Health-based instance selection
- Connection pooling and management
- Automatic failover handling
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import structlog
from enum import Enum
import random
import json

logger = structlog.get_logger()

class InstanceState(Enum):
    """Service instance states"""
    ACTIVE = "active"
    DRAINING = "draining"
    INACTIVE = "inactive"
    FAILED = "failed"

@dataclass
class ServiceInstance:
    """Service instance information"""
    instance_id: str
    host: str
    port: int
    metadata: Dict[str, Any]
    state: InstanceState
    last_seen: datetime
    health_score: float
    connection_count: int

class DiscoveryConfig:
    """Configuration for service discovery"""
    def __init__(
        self,
        refresh_interval_ms: float = 5000.0,
        instance_timeout_ms: float = 30000.0,
        connection_limit: int = 100,
        drain_timeout_ms: float = 10000.0
    ):
        self.refresh_interval_ms = refresh_interval_ms
        self.instance_timeout_ms = instance_timeout_ms
        self.connection_limit = connection_limit
        self.drain_timeout_ms = drain_timeout_ms

class ServiceDiscoveryIntegration:
    """
    Integrates circuit breaker with service discovery system.
    Manages service instances and their connections.
    """
    
    def __init__(
        self,
        config: Optional[DiscoveryConfig] = None,
        metrics_client = None
    ):
        self.config = config or DiscoveryConfig()
        self.metrics = metrics_client
        self.logger = logger.bind(component="discovery_integration")
        
        # Instance tracking
        self.instances: Dict[str, Dict[str, ServiceInstance]] = {}
        self.connection_pools: Dict[str, Dict[str, List[Any]]] = {}
        self.draining_instances: Set[Tuple[str, str]] = set()
        
        # Background tasks
        self.refresh_task: Optional[asyncio.Task] = None
        self.drain_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self) -> None:
        """Start background tasks"""
        if self._running:
            return
            
        self._running = True
        self.refresh_task = asyncio.create_task(self._refresh_loop())
        self.drain_task = asyncio.create_task(self._drain_loop())
        
    async def stop(self) -> None:
        """Stop background tasks"""
        self._running = False
        
        if self.refresh_task:
            self.refresh_task.cancel()
            try:
                await self.refresh_task
            except asyncio.CancelledError:
                pass
                
        if self.drain_task:
            self.drain_task.cancel()
            try:
                await self.drain_task
            except asyncio.CancelledError:
                pass
                
    async def register_instance(
        self,
        service_id: str,
        instance: ServiceInstance
    ) -> None:
        """Register a new service instance"""
        if service_id not in self.instances:
            self.instances[service_id] = {}
            self.connection_pools[service_id] = {}
            
        self.instances[service_id][instance.instance_id] = instance
        self.connection_pools[service_id][instance.instance_id] = []
        
        if self.metrics:
            await self.metrics.increment(
                "discovery_instance_registered",
                {
                    "service_id": service_id,
                    "instance_id": instance.instance_id
                }
            )
            
    async def deregister_instance(
        self,
        service_id: str,
        instance_id: str
    ) -> None:
        """Deregister a service instance"""
        if service_id in self.instances:
            if instance_id in self.instances[service_id]:
                instance = self.instances[service_id][instance_id]
                instance.state = InstanceState.DRAINING
                self.draining_instances.add((service_id, instance_id))
                
                if self.metrics:
                    await self.metrics.increment(
                        "discovery_instance_deregistered",
                        {
                            "service_id": service_id,
                            "instance_id": instance_id
                        }
                    )
                    
    async def get_instance(
        self,
        service_id: str,
        metadata_requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[ServiceInstance]:
        """Get best available instance for a service"""
        if service_id not in self.instances:
            return None
            
        candidates = []
        for instance in self.instances[service_id].values():
            # Check instance state
            if instance.state != InstanceState.ACTIVE:
                continue
                
            # Check metadata requirements
            if metadata_requirements:
                matches = True
                for key, value in metadata_requirements.items():
                    if instance.metadata.get(key) != value:
                        matches = False
                        break
                if not matches:
                    continue
                    
            # Check connection limit
            pool = self.connection_pools[service_id][instance.instance_id]
            if len(pool) >= self.config.connection_limit:
                continue
                
            candidates.append(instance)
            
        if not candidates:
            return None
            
        # Select best instance based on health score and connection count
        return max(
            candidates,
            key=lambda i: i.health_score / (i.connection_count + 1)
        )
        
    async def get_connection(
        self,
        service_id: str,
        instance_id: str
    ) -> Optional[Any]:
        """Get connection from pool"""
        if (service_id not in self.connection_pools or
            instance_id not in self.connection_pools[service_id]):
            return None
            
        pool = self.connection_pools[service_id][instance_id]
        
        if not pool:
            return await self._create_connection(service_id, instance_id)
            
        return pool.pop()
        
    async def release_connection(
        self,
        service_id: str,
        instance_id: str,
        connection: Any
    ) -> None:
        """Return connection to pool"""
        if (service_id not in self.connection_pools or
            instance_id not in self.connection_pools[service_id]):
            return
            
        pool = self.connection_pools[service_id][instance_id]
        pool.append(connection)
        
    async def update_instance_health(
        self,
        service_id: str,
        instance_id: str,
        health_score: float
    ) -> None:
        """Update instance health score"""
        if (service_id in self.instances and
            instance_id in self.instances[service_id]):
            instance = self.instances[service_id][instance_id]
            instance.health_score = health_score
            instance.last_seen = datetime.utcnow()
            
            if self.metrics:
                await self.metrics.gauge(
                    "discovery_instance_health",
                    health_score,
                    {
                        "service_id": service_id,
                        "instance_id": instance_id
                    }
                )
                
    async def _refresh_loop(self) -> None:
        """Background task to refresh instance states"""
        while self._running:
            try:
                await self._check_instance_timeouts()
                await asyncio.sleep(
                    self.config.refresh_interval_ms / 1000
                )
            except Exception as e:
                self.logger.error(
                    "Error in refresh loop",
                    error=str(e)
                )
                
    async def _drain_loop(self) -> None:
        """Background task to drain inactive instances"""
        while self._running:
            try:
                await self._drain_inactive_instances()
                await asyncio.sleep(
                    self.config.drain_timeout_ms / 1000
                )
            except Exception as e:
                self.logger.error(
                    "Error in drain loop",
                    error=str(e)
                )
                
    async def _check_instance_timeouts(self) -> None:
        """Check for timed out instances"""
        now = datetime.utcnow()
        timeout = timedelta(
            milliseconds=self.config.instance_timeout_ms
        )
        
        for service_id, instances in self.instances.items():
            for instance_id, instance in instances.items():
                if (instance.state == InstanceState.ACTIVE and
                    now - instance.last_seen > timeout):
                    instance.state = InstanceState.FAILED
                    self.draining_instances.add(
                        (service_id, instance_id)
                    )
                    
                    if self.metrics:
                        await self.metrics.increment(
                            "discovery_instance_timeout",
                            {
                                "service_id": service_id,
                                "instance_id": instance_id
                            }
                        )
                        
    async def _drain_inactive_instances(self) -> None:
        """Drain connections from inactive instances"""
        to_remove = set()
        
        for service_id, instance_id in self.draining_instances:
            if (service_id in self.connection_pools and
                instance_id in self.connection_pools[service_id]):
                pool = self.connection_pools[service_id][instance_id]
                
                # Close all connections
                while pool:
                    conn = pool.pop()
                    try:
                        await self._close_connection(conn)
                    except Exception as e:
                        self.logger.error(
                            "Error closing connection",
                            error=str(e)
                        )
                        
                # Remove instance
                if service_id in self.instances:
                    self.instances[service_id].pop(instance_id, None)
                self.connection_pools[service_id].pop(instance_id, None)
                to_remove.add((service_id, instance_id))
                
                if self.metrics:
                    await self.metrics.increment(
                        "discovery_instance_drained",
                        {
                            "service_id": service_id,
                            "instance_id": instance_id
                        }
                    )
                    
        self.draining_instances -= to_remove
        
    async def _create_connection(
        self,
        service_id: str,
        instance_id: str
    ) -> Optional[Any]:
        """Create new connection to instance"""
        if (service_id not in self.instances or
            instance_id not in self.instances[service_id]):
            return None
            
        instance = self.instances[service_id][instance_id]
        
        try:
            # Connection creation logic here
            # This should be implemented based on the specific protocol
            connection = None  # Replace with actual connection
            
            if self.metrics:
                await self.metrics.increment(
                    "discovery_connection_created",
                    {
                        "service_id": service_id,
                        "instance_id": instance_id
                    }
                )
                
            return connection
            
        except Exception as e:
            self.logger.error(
                "Error creating connection",
                error=str(e),
                service_id=service_id,
                instance_id=instance_id
            )
            return None
            
    async def _close_connection(self, connection: Any) -> None:
        """Close connection"""
        # Connection closing logic here
        # This should be implemented based on the specific protocol
        pass 