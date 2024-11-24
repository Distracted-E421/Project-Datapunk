from typing import Optional, Dict, List, Any, Set
from dataclasses import dataclass
import asyncio
import json
from datetime import datetime, timedelta
from .registry import ServiceRegistration
from ..security.encryption import DataEncryption, EncryptionKey
from ...messaging import MessageQueue  # We'll implement this later
import consul
import hashlib

@dataclass
class SyncConfig:
    """Configuration for registry synchronization"""
    consul_host: str = "localhost"
    consul_port: int = 8500
    sync_interval: int = 30  # seconds
    message_queue_url: str = "amqp://localhost:5672"
    encryption_key: Optional[EncryptionKey] = None
    cluster_name: str = "default"
    sync_timeout: float = 5.0
    max_sync_retries: int = 3

class RegistrySync:
    """Handles synchronization of service registries across the mesh"""
    def __init__(self, config: SyncConfig):
        self.config = config
        self.consul = consul.Consul(
            host=config.consul_host,
            port=config.consul_port
        )
        self._message_queue = MessageQueue(config.message_queue_url)
        self._encryption = DataEncryption(config.encryption_key) if config.encryption_key else None
        self._local_registry: Dict[str, ServiceRegistration] = {}
        self._sync_task: Optional[asyncio.Task] = None
        self._last_sync: Optional[datetime] = None
        self._sync_lock = asyncio.Lock()
        self._registry_version = 0
        self._sync_errors: List[str] = []

    async def start(self):
        """Start the synchronization process"""
        await self._message_queue.connect()
        await self._setup_message_handlers()
        self._sync_task = asyncio.create_task(self._sync_loop())
        print(f"Registry sync started for cluster: {self.config.cluster_name}")

    async def stop(self):
        """Stop the synchronization process"""
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        await self._message_queue.close()

    async def _sync_loop(self):
        """Main synchronization loop"""
        while True:
            try:
                await self._perform_sync()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._sync_errors.append(f"Sync error: {str(e)}")
                await asyncio.sleep(self.config.sync_interval)

    async def _perform_sync(self):
        """Perform one synchronization cycle"""
        async with self._sync_lock:
            try:
                # Get local services from Consul
                local_services = await self._get_local_services()
                local_hash = self._calculate_registry_hash(local_services)

                # Prepare sync message
                sync_message = {
                    "cluster": self.config.cluster_name,
                    "version": self._registry_version,
                    "hash": local_hash,
                    "services": local_services,
                    "timestamp": datetime.utcnow().isoformat()
                }

                # Encrypt if configured
                if self._encryption:
                    sync_message = await self._encryption.encrypt(sync_message)

                # Publish sync message
                await self._message_queue.publish(
                    "service.registry.sync",
                    sync_message
                )

                self._last_sync = datetime.utcnow()
                self._registry_version += 1

            except Exception as e:
                raise RegistrySyncError(f"Sync failed: {str(e)}")

    async def _get_local_services(self) -> Dict[str, Any]:
        """Get services from local Consul instance"""
        try:
            index, services = await self.consul.catalog.services()
            result = {}

            for service_name in services:
                index, service_info = await self.consul.catalog.service(service_name)
                if service_info:
                    result[service_name] = service_info

            return result
        except Exception as e:
            raise RegistrySyncError(f"Failed to get local services: {str(e)}")

    async def _setup_message_handlers(self):
        """Set up handlers for sync messages"""
        await self._message_queue.subscribe(
            "service.registry.sync",
            self._handle_sync_message
        )

    async def _handle_sync_message(self, message: Dict[str, Any]):
        """Handle incoming sync messages"""
        try:
            # Decrypt if needed
            if self._encryption:
                message = await self._encryption.decrypt(message)

            # Skip our own messages
            if message["cluster"] == self.config.cluster_name:
                return

            # Version check
            if message["version"] <= self._registry_version:
                return

            # Verify and apply changes
            await self._apply_sync_changes(message["services"])
            self._registry_version = message["version"]

        except Exception as e:
            self._sync_errors.append(f"Message handling error: {str(e)}")

    async def _apply_sync_changes(self, remote_services: Dict[str, Any]):
        """Apply changes from remote registry"""
        async with self._sync_lock:
            try:
                local_services = await self._get_local_services()
                
                # Find services to add/update
                for service_name, service_info in remote_services.items():
                    if service_name not in local_services:
                        await self._register_service(service_name, service_info)
                    else:
                        await self._update_service(service_name, service_info)

                # Find services to remove
                for service_name in local_services:
                    if service_name not in remote_services:
                        await self._deregister_service(service_name)

            except Exception as e:
                raise RegistrySyncError(f"Failed to apply sync changes: {str(e)}")

    async def _register_service(self, name: str, info: Dict[str, Any]):
        """Register a new service"""
        try:
            for instance in info:
                await self.consul.agent.service.register(
                    name=name,
                    service_id=instance["ServiceID"],
                    address=instance["ServiceAddress"],
                    port=instance["ServicePort"],
                    tags=instance.get("ServiceTags", []),
                    meta=instance.get("ServiceMeta", {})
                )
        except Exception as e:
            raise RegistrySyncError(f"Failed to register service {name}: {str(e)}")

    async def _update_service(self, name: str, info: Dict[str, Any]):
        """Update an existing service"""
        await self._deregister_service(name)
        await self._register_service(name, info)

    async def _deregister_service(self, name: str):
        """Deregister a service"""
        try:
            index, instances = await self.consul.catalog.service(name)
            for instance in instances:
                await self.consul.agent.service.deregister(
                    service_id=instance["ServiceID"]
                )
        except Exception as e:
            raise RegistrySyncError(f"Failed to deregister service {name}: {str(e)}")

    @staticmethod
    def _calculate_registry_hash(services: Dict[str, Any]) -> str:
        """Calculate hash of registry state"""
        serialized = json.dumps(services, sort_keys=True)
        return hashlib.sha256(serialized.encode()).hexdigest()

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        return {
            "cluster": self.config.cluster_name,
            "version": self._registry_version,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "errors": self._sync_errors[-5:],  # Last 5 errors
            "is_syncing": self._sync_lock.locked(),
            "service_count": len(self._local_registry)
        }

class RegistrySyncError(Exception):
    """Custom exception for registry synchronization errors"""
    pass 