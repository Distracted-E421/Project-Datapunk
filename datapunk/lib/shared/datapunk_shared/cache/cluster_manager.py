from typing import List, Dict, Any, Optional, Set
import asyncio
import json
import logging
import time
from datetime import datetime
import aioredis
from .cache_types import CacheConfig, CacheEntry
from ..monitoring.metrics import MetricsClient

class ClusterNode:
    def __init__(
        self,
        node_id: str,
        host: str,
        port: int,
        is_master: bool = False,
        weight: int = 1
    ):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.is_master = is_master
        self.weight = weight
        self.last_heartbeat: Optional[float] = None
        self.status: str = "connecting"
        self.connection: Optional[aioredis.Redis] = None

class ClusterManager:
    def __init__(
        self,
        config: CacheConfig,
        nodes: List[ClusterNode],
        metrics_client: Optional[MetricsClient] = None
    ):
        self.config = config
        self.nodes = {node.node_id: node for node in nodes}
        self.metrics = metrics_client
        self.logger = logging.getLogger(__name__)
        
        self._master_node: Optional[ClusterNode] = None
        self._sync_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Consistent hashing ring
        self._hash_ring: List[tuple] = []  # (hash_value, node_id)
        self._virtual_nodes = 160  # Number of virtual nodes per physical node

    async def start(self) -> None:
        """Start cluster management"""
        self._running = True
        await self._connect_nodes()
        await self._elect_master()
        self._build_hash_ring()
        
        self._heartbeat_task = asyncio.create_task(self._run_heartbeat())
        self._sync_task = asyncio.create_task(self._run_sync())

    async def stop(self) -> None:
        """Stop cluster management"""
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._sync_task:
            self._sync_task.cancel()
        
        for node in self.nodes.values():
            if node.connection:
                await node.connection.close()

    async def get_node_for_key(self, key: str) -> Optional[ClusterNode]:
        """Get responsible node for a key using consistent hashing"""
        if not self._hash_ring:
            return self._master_node
        
        key_hash = self._hash_key(key)
        for hash_value, node_id in self._hash_ring:
            if key_hash <= hash_value:
                return self.nodes[node_id]
        
        return self.nodes[self._hash_ring[0][1]]  # Wrap around

    async def sync_key(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Synchronize a key across the cluster"""
        if not self._master_node:
            return

        try:
            # Create sync entry
            sync_entry = {
                'key': key,
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'source_node': self._master_node.node_id,
                'ttl': ttl
            }

            # Publish sync message
            await self._master_node.connection.publish(
                f"{self.config.namespace}:sync",
                json.dumps(sync_entry)
            )

            if self.metrics:
                await self.metrics.increment_counter(
                    'cache_sync_operations_total',
                    {'namespace': self.config.namespace}
                )

        except Exception as e:
            self.logger.error(f"Failed to sync key {key}: {str(e)}")

    async def _connect_nodes(self) -> None:
        """Connect to all cluster nodes"""
        for node in self.nodes.values():
            try:
                node.connection = await aioredis.from_url(
                    f"redis://{node.host}:{node.port}"
                )
                node.status = "connected"
                node.last_heartbeat = time.time()
            except Exception as e:
                self.logger.error(f"Failed to connect to node {node.node_id}: {str(e)}")
                node.status = "error"

    async def _elect_master(self) -> None:
        """Elect a master node"""
        connected_nodes = [
            node for node in self.nodes.values()
            if node.status == "connected" and node.connection
        ]
        
        if not connected_nodes:
            raise Exception("No available nodes for master election")

        # Simple election: choose node with lowest node_id
        self._master_node = min(connected_nodes, key=lambda n: n.node_id)
        self._master_node.is_master = True
        
        self.logger.info(f"Elected master node: {self._master_node.node_id}")

    def _build_hash_ring(self) -> None:
        """Build consistent hashing ring"""
        self._hash_ring = []
        
        for node in self.nodes.values():
            if node.status != "connected":
                continue
                
            for i in range(self._virtual_nodes * node.weight):
                hash_key = f"{node.node_id}:{i}"
                hash_value = self._hash_key(hash_key)
                self._hash_ring.append((hash_value, node.node_id))
        
        self._hash_ring.sort()

    def _hash_key(self, key: str) -> int:
        """Compute hash for a key"""
        import hashlib
        return int(hashlib.md5(key.encode()).hexdigest(), 16)

    async def _run_heartbeat(self) -> None:
        """Run heartbeat checks"""
        while self._running:
            try:
                for node in self.nodes.values():
                    if node.status != "connected" or not node.connection:
                        continue

                    try:
                        await node.connection.ping()
                        node.last_heartbeat = time.time()
                    except Exception as e:
                        self.logger.error(f"Heartbeat failed for node {node.node_id}: {str(e)}")
                        node.status = "error"
                        
                        if node == self._master_node:
                            await self._elect_master()
                            self._build_hash_ring()

                if self.metrics:
                    await self.metrics.gauge(
                        'cache_cluster_nodes',
                        len([n for n in self.nodes.values() if n.status == "connected"]),
                        {'namespace': self.config.namespace}
                    )

            except Exception as e:
                self.logger.error(f"Heartbeat error: {str(e)}")

            await asyncio.sleep(5)  # Configurable interval

    async def _run_sync(self) -> None:
        """Run cluster synchronization"""
        if not self._master_node or not self._master_node.connection:
            return

        try:
            pubsub = self._master_node.connection.pubsub()
            await pubsub.subscribe(f"{self.config.namespace}:sync")

            while self._running:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True)
                    if not message:
                        await asyncio.sleep(0.1)
                        continue

                    sync_entry = json.loads(message['data'])
                    source_node = sync_entry['source_node']

                    # Apply sync to all nodes except source
                    for node in self.nodes.values():
                        if (
                            node.node_id != source_node and
                            node.status == "connected" and
                            node.connection
                        ):
                            try:
                                await node.connection.set(
                                    sync_entry['key'],
                                    sync_entry['value'],
                                    ex=sync_entry.get('ttl')
                                )
                            except Exception as e:
                                self.logger.error(
                                    f"Sync failed for node {node.node_id}: {str(e)}"
                                )

                except Exception as e:
                    self.logger.error(f"Sync processing error: {str(e)}")

        except Exception as e:
            self.logger.error(f"Sync subscription error: {str(e)}")
        finally:
            await pubsub.unsubscribe() 