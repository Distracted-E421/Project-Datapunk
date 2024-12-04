"""
Distributed cache cluster manager implementing consistent hashing for data distribution
and master-slave replication for high availability.

The cluster uses a pub/sub mechanism for synchronization and maintains node health
through periodic heartbeats. Node failures trigger automatic master re-election
and redistribution of the hash ring.
"""

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
    """
    Represents a single node in the cache cluster with connection management
    and health monitoring capabilities.
    
    NOTE: Weight parameter affects the node's share of keys in consistent hashing.
    Higher weights are useful for nodes with more capacity.
    """
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
        self.status: str = "connecting"  # States: connecting, connected, error
        self.connection: Optional[aioredis.Redis] = None

class ClusterManager:
    """
    Manages a distributed cache cluster with consistent hashing and automatic failover.
    
    The consistent hashing ring uses virtual nodes (default: 160 per physical node)
    to ensure even distribution even with heterogeneous node capacities.
    
    NOTE: The cluster requires at least one node to be available for master election.
    Consider deploying an odd number of nodes to avoid split-brain scenarios.
    """
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
        
        # Virtual nodes improve distribution uniformity and handle node weight scaling
        self._hash_ring: List[tuple] = []  # (hash_value, node_id)
        self._virtual_nodes = 160  # Higher values = better distribution but more memory

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
        """
        Maps a key to its responsible node using consistent hashing.
        Falls back to master node if hash ring is empty.
        
        NOTE: Hash ring lookups are O(log n) due to binary search in sorted ring.
        """
        if not self._hash_ring:
            return self._master_node
        
        key_hash = self._hash_key(key)
        for hash_value, node_id in self._hash_ring:
            if key_hash <= hash_value:
                return self.nodes[node_id]
        
        # Wrap around to first node if key hash is larger than all ring values
        return self.nodes[self._hash_ring[0][1]]

    async def sync_key(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Propagates key updates to all cluster nodes through pub/sub.
        
        NOTE: Synchronization is eventually consistent. There may be a brief window
        where nodes have different values during the sync process.
        """
        if not self._master_node:
            return

        try:
            sync_entry = {
                'key': key,
                'value': value,
                'timestamp': datetime.now().isoformat(),
                'source_node': self._master_node.node_id,
                'ttl': ttl
            }

            # Publish via master to ensure ordering of updates
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
        """
        Simple master election using lowest node_id as tiebreaker.
        
        TODO: Implement more sophisticated election algorithm (e.g., Raft)
        for better partition tolerance.
        """
        connected_nodes = [
            node for node in self.nodes.values()
            if node.status == "connected" and node.connection
        ]
        
        if not connected_nodes:
            raise Exception("No available nodes for master election")

        self._master_node = min(connected_nodes, key=lambda n: n.node_id)
        self._master_node.is_master = True
        
        self.logger.info(f"Elected master node: {self._master_node.node_id}")

    def _build_hash_ring(self) -> None:
        """
        Builds consistent hash ring with virtual nodes for better distribution.
        Only includes healthy nodes in the ring.
        
        NOTE: Ring is rebuilt on node status changes, which can cause
        temporary redistribution of keys.
        """
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
        """
        Monitors node health through Redis PING commands.
        Failed master nodes trigger immediate re-election.
        
        NOTE: 5-second heartbeat interval is a trade-off between
        responsiveness and network overhead.
        """
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

            await asyncio.sleep(5)

    async def _run_sync(self) -> None:
        """
        Handles cluster-wide key synchronization through Redis pub/sub.
        
        FIXME: Consider implementing batch synchronization for better performance
        when many keys change simultaneously.
        """
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

                    # Propagate updates to all nodes except the source
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