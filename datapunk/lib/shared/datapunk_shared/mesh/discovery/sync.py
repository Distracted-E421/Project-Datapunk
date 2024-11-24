from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass
import asyncio
import aiohttp
from datetime import datetime, timedelta
from .registry import ServiceRegistry, ServiceRegistration, ServiceStatus
from ..monitoring import MetricsCollector
import json
import hashlib

@dataclass
class SyncConfig:
    """Configuration for registry synchronization"""
    sync_interval: float = 30.0  # seconds
    sync_timeout: float = 10.0  # seconds
    retry_delay: float = 5.0  # seconds
    max_retries: int = 3
    batch_size: int = 100
    conflict_resolution: str = "timestamp"  # timestamp or version
    enable_compression: bool = True
    compression_threshold: int = 1024  # bytes
    peers: List[str] = None  # List of peer sync endpoints
    local_endpoint: Optional[str] = None

class SyncError(Exception):
    """Base class for sync errors"""
    pass

class RegistrySync:
    """Handles synchronization of service registries"""
    def __init__(
        self,
        config: SyncConfig,
        registry: ServiceRegistry,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.registry = registry
        self.metrics = metrics_collector
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False
        self._last_sync: Dict[str, datetime] = {}
        self._sync_states: Dict[str, str] = {}  # Hash of last known state per peer
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Start sync process"""
        self._running = True
        self._session = aiohttp.ClientSession()
        self._sync_task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """Stop sync process"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()

    async def _sync_loop(self):
        """Main sync loop"""
        while self._running:
            try:
                await self._sync_with_peers()
                await asyncio.sleep(self.config.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "discovery.sync.error",
                        tags={"error": str(e)}
                    )
                await asyncio.sleep(self.config.retry_delay)

    async def _sync_with_peers(self):
        """Sync with all configured peers"""
        if not self.config.peers:
            return

        for peer in self.config.peers:
            try:
                await self._sync_with_peer(peer)
                
                if self.metrics:
                    await self.metrics.increment(
                        "discovery.sync.success",
                        tags={"peer": peer}
                    )
                    
            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "discovery.sync.peer_error",
                        tags={
                            "peer": peer,
                            "error": str(e)
                        }
                    )

    async def _sync_with_peer(self, peer: str):
        """Sync with a specific peer"""
        # Get local state hash
        local_state = await self._get_state_hash()
        
        # Check if peer state has changed
        peer_state = await self._get_peer_state_hash(peer)
        if peer_state == self._sync_states.get(peer):
            return  # No changes
            
        # Get peer services
        peer_services = await self._get_peer_services(peer)
        
        # Merge services
        await self._merge_services(peer_services)
        
        # Update sync state
        self._sync_states[peer] = peer_state
        self._last_sync[peer] = datetime.utcnow()

    async def _get_state_hash(self) -> str:
        """Get hash of current registry state"""
        services = await self.registry.get_services()
        state_data = [
            {
                "id": s.id,
                "service_name": s.service_name,
                "status": s.status.value,
                "last_heartbeat": s.last_heartbeat.isoformat() if s.last_heartbeat else None
            }
            for s in services
        ]
        return hashlib.sha256(
            json.dumps(state_data, sort_keys=True).encode()
        ).hexdigest()

    async def _get_peer_state_hash(self, peer: str) -> str:
        """Get state hash from peer"""
        async with self._session.get(
            f"{peer}/state_hash",
            timeout=self.config.sync_timeout
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return data["hash"]

    async def _get_peer_services(self, peer: str) -> List[ServiceRegistration]:
        """Get services from peer"""
        async with self._session.get(
            f"{peer}/services",
            timeout=self.config.sync_timeout
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return [
                ServiceRegistration(**service_data)
                for service_data in data["services"]
            ]

    async def _merge_services(self, peer_services: List[ServiceRegistration]):
        """Merge peer services with local registry"""
        local_services = {
            s.id: s for s in await self.registry.get_services()
        }
        
        for peer_service in peer_services:
            if peer_service.id not in local_services:
                # New service
                await self.registry.register(peer_service)
                continue
                
            local_service = local_services[peer_service.id]
            
            # Resolve conflicts based on configuration
            if self.config.conflict_resolution == "timestamp":
                if (
                    peer_service.last_heartbeat and
                    (
                        not local_service.last_heartbeat or
                        peer_service.last_heartbeat > local_service.last_heartbeat
                    )
                ):
                    await self.registry.update_service(peer_service)
                    
            elif self.config.conflict_resolution == "version":
                if peer_service.metadata.version > local_service.metadata.version:
                    await self.registry.update_service(peer_service)

    async def get_sync_stats(self) -> Dict[str, Any]:
        """Get synchronization statistics"""
        stats = {
            "peers": len(self.config.peers or []),
            "last_sync": {},
            "sync_states": self._sync_states.copy(),
            "errors": {}
        }
        
        for peer in (self.config.peers or []):
            stats["last_sync"][peer] = self._last_sync.get(peer)
            
        return stats

    async def force_sync(self, peer: Optional[str] = None):
        """Force immediate sync with peers"""
        if peer:
            await self._sync_with_peer(peer)
        else:
            await self._sync_with_peers()

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data if enabled and meets threshold"""
        if (
            self.config.enable_compression and
            len(data) > self.config.compression_threshold
        ):
            import zlib
            return zlib.compress(data)
        return data

    def _decompress_data(self, data: bytes) -> bytes:
        """Decompress data if compressed"""
        try:
            import zlib
            return zlib.decompress(data)
        except zlib.error:
            return data  # Data wasn't compressed 