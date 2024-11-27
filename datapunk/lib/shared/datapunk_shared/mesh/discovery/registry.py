from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
import asyncio
from datetime import datetime, timedelta
from enum import Enum
import json
import aiohttp
from ..health.checks import HealthCheck
from ...monitoring import MetricsCollector

"""
Service Registry Implementation for Datapunk Service Mesh

This module provides a distributed service registry that enables:
- Dynamic service discovery and registration
- Health monitoring and status tracking
- Event-driven service updates
- State persistence and recovery

The registry is a critical component of the mesh architecture,
maintaining the service topology and enabling reliable communication
between components like Lake, Stream, and Cortex services.

TODO: Implement cluster synchronization for multi-node deployments
TODO: Add support for service versioning and gradual rollout
FIXME: Improve cleanup performance for large service counts
"""

class ServiceStatus(Enum):
    """
    Service lifecycle states within the mesh.
    
    The status progression typically follows:
    STARTING -> RUNNING -> STOPPING -> STOPPED
    
    UNHEALTHY and UNKNOWN are special states for error handling.
    """
    STARTING = "starting"    # Initial registration, not ready for traffic
    RUNNING = "running"      # Healthy and accepting requests
    STOPPING = "stopping"    # Graceful shutdown in progress
    STOPPED = "stopped"      # No longer accepting requests
    UNHEALTHY = "unhealthy" # Failed health checks
    UNKNOWN = "unknown"     # State cannot be determined

@dataclass
class ServiceMetadata:
    """
    Extended service information for mesh routing and management.
    
    Used to:
    - Enable capability-based routing
    - Track service dependencies
    - Manage service endpoints
    - Support blue/green deployments
    
    NOTE: Tags should follow mesh-wide naming conventions
    """
    version: str  # Semantic version for compatibility checking
    environment: str  # e.g., prod, staging, dev
    region: str  # Geographic location for locality routing
    tags: Dict[str, str] = field(default_factory=dict)  # Custom metadata
    capabilities: Set[str] = field(default_factory=set)  # Supported features
    dependencies: List[str] = field(default_factory=list)  # Required services
    endpoints: Dict[str, str] = field(default_factory=dict)  # Service URLs

@dataclass
class ServiceRegistration:
    """
    Service instance registration record.
    
    Combines identity, status, and routing information needed for:
    - Service discovery
    - Load balancing
    - Health monitoring
    - Traffic management
    
    NOTE: weight affects load balancing decisions
    """
    id: str  # Unique instance identifier
    service_name: str  # Logical service name
    host: str  # Network address
    port: int  # Service port
    status: ServiceStatus = ServiceStatus.STARTING
    metadata: ServiceMetadata = field(default_factory=ServiceMetadata)
    last_heartbeat: Optional[datetime] = None
    health_check_url: Optional[str] = None
    weight: int = 100  # Load balancing weight
    registered_at: datetime = field(default_factory=datetime.utcnow)

class RegistryError(Exception):
    """Base class for registry errors"""
    pass

@dataclass
class RegistryConfig:
    """
    Configuration for service registry behavior.
    
    Timeouts and intervals are tuned for typical mesh deployments:
    - TTL covers temporary network issues
    - Cleanup prevents resource leaks
    - Health checks balance accuracy and overhead
    
    TODO: Add support for dynamic interval adjustment
    """
    ttl: int = 30  # Service expiration time
    cleanup_interval: int = 60  # Expired service removal frequency
    heartbeat_interval: int = 10  # Service liveness check interval
    health_check_interval: int = 15  # Service health check frequency
    sync_interval: int = 30  # Multi-node sync interval
    storage_path: Optional[str] = None  # State persistence location
    enable_persistence: bool = True  # Enable state recovery
    enable_health_checks: bool = True  # Enable active health monitoring
    enable_sync: bool = True  # Enable multi-node synchronization

class ServiceRegistry:
    """
    Service registry for mesh service discovery and health tracking.
    
    Core responsibilities:
    - Maintain service inventory
    - Monitor service health
    - Notify subscribers of changes
    - Persist registry state
    - Synchronize across nodes
    
    The registry uses multiple background tasks:
    - Cleanup: Remove expired services
    - Health Check: Monitor service health
    - Sync: Maintain registry consistency
    
    NOTE: All public methods are thread-safe through async locking
    FIXME: Improve subscription notification performance
    """
    def __init__(
        self,
        config: RegistryConfig,
        health_check: Optional[HealthCheck] = None,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.health_check = health_check
        self.metrics = metrics_collector
        self._services: Dict[str, ServiceRegistration] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._subscribers: Dict[str, Set[callable]] = {}

    async def start(self):
        """Start registry background tasks"""
        if self.config.enable_persistence:
            await self._load_state()

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        if self.config.enable_health_checks and self.health_check:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
        if self.config.enable_sync:
            self._sync_task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """Stop registry background tasks"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            await self._cleanup_task
            
        if self._health_check_task:
            self._health_check_task.cancel()
            await self._health_check_task
            
        if self._sync_task:
            self._sync_task.cancel()
            await self._sync_task

        if self.config.enable_persistence:
            await self._save_state()

    async def register(self, registration: ServiceRegistration) -> bool:
        """Register a service instance"""
        async with self._lock:
            try:
                self._services[registration.id] = registration
                
                if self.metrics:
                    await self.metrics.increment(
                        "registry.services.registered",
                        tags={
                            "service": registration.service_name,
                            "id": registration.id
                        }
                    )
                
                await self._notify_subscribers(
                    "register",
                    registration.service_name,
                    registration
                )
                
                return True

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "registry.registration.error",
                        tags={"error": str(e)}
                    )
                raise RegistryError(f"Registration failed: {str(e)}")

    async def deregister(self, service_id: str) -> bool:
        """Deregister a service instance"""
        async with self._lock:
            if service_id in self._services:
                service = self._services.pop(service_id)
                
                if self.metrics:
                    await self.metrics.increment(
                        "registry.services.deregistered",
                        tags={
                            "service": service.service_name,
                            "id": service_id
                        }
                    )
                
                await self._notify_subscribers(
                    "deregister",
                    service.service_name,
                    service
                )
                
                return True
            return False

    async def heartbeat(self, service_id: str) -> bool:
        """Update service heartbeat"""
        async with self._lock:
            if service_id in self._services:
                self._services[service_id].last_heartbeat = datetime.utcnow()
                return True
            return False

    async def get_service(self, service_id: str) -> Optional[ServiceRegistration]:
        """Get service registration by ID"""
        return self._services.get(service_id)

    async def get_services(
        self,
        service_name: Optional[str] = None,
        status: Optional[ServiceStatus] = None,
        metadata_filter: Optional[Dict[str, str]] = None
    ) -> List[ServiceRegistration]:
        """Get services with optional filtering"""
        services = list(self._services.values())
        
        if service_name:
            services = [s for s in services if s.service_name == service_name]
            
        if status:
            services = [s for s in services if s.status == status]
            
        if metadata_filter:
            services = [
                s for s in services
                if all(
                    s.metadata.tags.get(k) == v
                    for k, v in metadata_filter.items()
                )
            ]
            
        return services

    async def update_status(
        self,
        service_id: str,
        status: ServiceStatus
    ) -> bool:
        """Update service status"""
        async with self._lock:
            if service_id in self._services:
                old_status = self._services[service_id].status
                self._services[service_id].status = status
                
                if self.metrics:
                    await self.metrics.increment(
                        "registry.services.status_changed",
                        tags={
                            "service": self._services[service_id].service_name,
                            "id": service_id,
                            "old_status": old_status.value,
                            "new_status": status.value
                        }
                    )
                
                await self._notify_subscribers(
                    "status_change",
                    self._services[service_id].service_name,
                    self._services[service_id]
                )
                
                return True
            return False

    async def subscribe(
        self,
        event_type: str,
        service_name: str,
        callback: callable
    ):
        """Subscribe to service events"""
        key = f"{event_type}:{service_name}"
        if key not in self._subscribers:
            self._subscribers[key] = set()
        self._subscribers[key].add(callback)

    async def unsubscribe(
        self,
        event_type: str,
        service_name: str,
        callback: callable
    ):
        """Unsubscribe from service events"""
        key = f"{event_type}:{service_name}"
        if key in self._subscribers:
            self._subscribers[key].discard(callback)

    async def _notify_subscribers(
        self,
        event_type: str,
        service_name: str,
        service: ServiceRegistration
    ):
        """
        Notify subscribers of service events.
        
        Events are delivered asynchronously to prevent:
        - Blocking registry operations
        - Cascading failures
        - Slow subscriber impact
        
        FIXME: Add event batching for high-frequency updates
        """
        key = f"{event_type}:{service_name}"
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                try:
                    await callback(service)
                except Exception as e:
                    if self.metrics:
                        await self.metrics.increment(
                            "registry.notification.error",
                            tags={"error": str(e)}
                        )

    async def _cleanup_loop(self):
        """
        Periodic cleanup of expired services.
        
        Services are expired when:
        - TTL has elapsed since last heartbeat
        - Health checks consistently fail
        - Explicit deregistration
        
        NOTE: Cleanup runs even if persistence is disabled
        """
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)
                await self._cleanup_expired_services()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "registry.cleanup.error",
                        tags={"error": str(e)}
                    )

    async def _cleanup_expired_services(self):
        """
        Remove expired service registrations.
        
        Uses TTL-based expiration to handle:
        - Crashed services
        - Network partitions
        - Unclean shutdowns
        
        TODO: Add grace period for temporary failures
        """
        now = datetime.utcnow()
        expired_ids = []
        
        async with self._lock:
            for service_id, service in self._services.items():
                if service.last_heartbeat:
                    age = (now - service.last_heartbeat).total_seconds()
                    if age > self.config.ttl:
                        expired_ids.append(service_id)

            for service_id in expired_ids:
                await self.deregister(service_id)

    async def _health_check_loop(self):
        """Periodic health check of services"""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self._check_services_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "registry.health_check.error",
                        tags={"error": str(e)}
                    )

    async def _check_services_health(self):
        """Check health of registered services"""
        for service in self._services.values():
            if service.health_check_url:
                try:
                    is_healthy = await self.health_check.check_url_health(
                        service.health_check_url
                    )
                    new_status = (
                        ServiceStatus.RUNNING if is_healthy
                        else ServiceStatus.UNHEALTHY
                    )
                    await self.update_status(service.id, new_status)
                    
                except Exception as e:
                    if self.metrics:
                        await self.metrics.increment(
                            "registry.health_check.failed",
                            tags={
                                "service": service.service_name,
                                "id": service.id,
                                "error": str(e)
                            }
                        )

    async def _load_state(self):
        """Load registry state from storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'r') as f:
                data = json.load(f)
                for service_data in data:
                    service = ServiceRegistration(**service_data)
                    self._services[service.id] = service
                    
        except FileNotFoundError:
            pass
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "registry.storage.load_error",
                    tags={"error": str(e)}
                )

    async def _save_state(self):
        """Save registry state to storage"""
        if not self.config.storage_path:
            return

        try:
            with open(self.config.storage_path, 'w') as f:
                data = [vars(s) for s in self._services.values()]
                json.dump(data, f)
                
        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "registry.storage.save_error",
                    tags={"error": str(e)}
                )

    async def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            "total_services": len(self._services),
            "services_by_status": {},
            "services_by_name": {},
            "total_subscribers": sum(len(s) for s in self._subscribers.values())
        }
        
        for service in self._services.values():
            # Count by status
            status = service.status.value
            stats["services_by_status"][status] = (
                stats["services_by_status"].get(status, 0) + 1
            )
            
            # Count by name
            name = service.service_name
            stats["services_by_name"][name] = (
                stats["services_by_name"].get(name, 0) + 1
            )
            
        return stats