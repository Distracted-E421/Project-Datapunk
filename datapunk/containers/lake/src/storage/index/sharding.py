from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from enum import Enum
import hashlib
import bisect
from collections import defaultdict
import threading
import asyncio

from .distributed import DistributedManager, Node, NodeState
from .manager import IndexManager
from .monitor import IndexMonitor

logger = logging.getLogger(__name__)

class ShardState(Enum):
    """Shard operational states."""
    ACTIVE = "active"
    REBALANCING = "rebalancing"
    MIGRATING = "migrating"
    SPLIT = "splitting"
    MERGED = "merged"

class PartitionStrategy(Enum):
    """Data partitioning strategies."""
    HASH = "hash"
    RANGE = "range"
    COMPOSITE = "composite"
    DYNAMIC = "dynamic"

@dataclass
class ShardInfo:
    """Shard information."""
    shard_id: str
    index_name: str
    key_range: Tuple[Any, Any]  # (min_key, max_key)
    node_id: str
    state: ShardState
    size_bytes: int
    record_count: int
    created_at: datetime
    last_modified: datetime

@dataclass
class PartitionMap:
    """Partition mapping information."""
    partition_id: str
    strategy: PartitionStrategy
    key_ranges: List[Tuple[Any, Any]]
    shard_mapping: Dict[str, Set[str]]  # partition_key -> shard_ids
    version: int
    last_updated: datetime

class ShardManager:
    """Manages index sharding and partitioning."""
    
    def __init__(
        self,
        distributed: DistributedManager,
        config_path: Optional[Union[str, Path]] = None
    ):
        self.distributed = distributed
        self.config_path = Path(config_path) if config_path else None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.shards: Dict[str, ShardInfo] = {}
        self.partition_maps: Dict[str, PartitionMap] = {}
        self.ring: List[int] = []  # Consistent hashing ring
        self.ring_nodes: Dict[int, str] = {}  # Hash point -> node_id
        
        # Initialize consistent hashing ring
        self._initialize_ring()
        
        # Start background tasks
        self._start_background_tasks()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load sharding configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "sharding": {
                    "default_strategy": "hash",
                    "virtual_nodes": 256,  # Per physical node
                    "min_shard_size_mb": 64,
                    "max_shard_size_mb": 512,
                    "rebalance_threshold": 0.2  # 20% imbalance triggers rebalance
                },
                "partitioning": {
                    "max_partitions": 1024,
                    "partition_size_mb": 256,
                    "replication_factor": 3
                },
                "monitoring": {
                    "shard_stats_interval_seconds": 60,
                    "rebalance_check_interval_minutes": 5
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _initialize_ring(self):
        """Initialize consistent hashing ring."""
        virtual_nodes = self.config["sharding"]["virtual_nodes"]
        
        for node_id in self.distributed.nodes:
            # Add virtual nodes for each physical node
            for i in range(virtual_nodes):
                hash_key = f"{node_id}:{i}"
                hash_point = self._hash_key(hash_key)
                
                bisect.insort(self.ring, hash_point)
                self.ring_nodes[hash_point] = node_id
                
    def _hash_key(self, key: str) -> int:
        """Generate hash for consistent hashing."""
        return int(
            hashlib.sha256(str(key).encode()).hexdigest(),
            16
        )
        
    def _find_node(self, key: str) -> str:
        """Find responsible node for key using consistent hashing."""
        if not self.ring:
            raise ValueError("No nodes in ring")
            
        hash_point = self._hash_key(key)
        idx = bisect.bisect(self.ring, hash_point)
        
        if idx == len(self.ring):
            idx = 0
            
        return self.ring_nodes[self.ring[idx]]
        
    def create_partition_map(
        self,
        index_name: str,
        strategy: PartitionStrategy = None,
        key_ranges: List[Tuple[Any, Any]] = None
    ) -> str:
        """Create new partition map."""
        if not strategy:
            strategy = PartitionStrategy(
                self.config["sharding"]["default_strategy"]
            )
            
        # Generate partition ID
        partition_id = hashlib.sha256(
            f"{index_name}:{strategy.value}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Create partition map
        partition_map = PartitionMap(
            partition_id=partition_id,
            strategy=strategy,
            key_ranges=key_ranges or [],
            shard_mapping={},
            version=1,
            last_updated=datetime.now()
        )
        
        self.partition_maps[partition_id] = partition_map
        return partition_id
        
    def create_shard(
        self,
        index_name: str,
        key_range: Tuple[Any, Any],
        node_id: Optional[str] = None
    ) -> str:
        """Create new shard."""
        # Generate shard ID
        shard_id = hashlib.sha256(
            f"{index_name}:{key_range}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        # Find target node if not specified
        if not node_id:
            node_id = self._find_node(str(key_range[0]))
            
        # Create shard info
        shard = ShardInfo(
            shard_id=shard_id,
            index_name=index_name,
            key_range=key_range,
            node_id=node_id,
            state=ShardState.ACTIVE,
            size_bytes=0,
            record_count=0,
            created_at=datetime.now(),
            last_modified=datetime.now()
        )
        
        self.shards[shard_id] = shard
        return shard_id
        
    async def rebalance_shards(self):
        """Rebalance shards across nodes."""
        # Calculate current distribution
        node_loads = defaultdict(int)
        for shard in self.shards.values():
            node_loads[shard.node_id] += shard.size_bytes
            
        if not node_loads:
            return
            
        # Calculate average load
        avg_load = sum(node_loads.values()) / len(node_loads)
        threshold = avg_load * self.config["sharding"]["rebalance_threshold"]
        
        # Find overloaded and underloaded nodes
        overloaded = {
            node_id: load
            for node_id, load in node_loads.items()
            if load > avg_load + threshold
        }
        
        underloaded = {
            node_id: load
            for node_id, load in node_loads.items()
            if load < avg_load - threshold
        }
        
        if not overloaded or not underloaded:
            return
            
        # Rebalance shards
        for over_node in overloaded:
            shards_to_move = [
                shard for shard in self.shards.values()
                if shard.node_id == over_node and
                shard.state == ShardState.ACTIVE
            ]
            
            for shard in shards_to_move:
                # Find best target node
                target_node = min(
                    underloaded.items(),
                    key=lambda x: x[1]
                )[0]
                
                # Initiate shard migration
                await self._migrate_shard(shard.shard_id, target_node)
                
                # Update loads
                underloaded[target_node] += shard.size_bytes
                
    async def _migrate_shard(self, shard_id: str, target_node: str):
        """Migrate shard to target node."""
        if shard_id not in self.shards:
            raise ValueError(f"Shard {shard_id} not found")
            
        shard = self.shards[shard_id]
        source_node = shard.node_id
        
        try:
            # Mark shard as migrating
            shard.state = ShardState.MIGRATING
            
            # Export shard data
            index_data = await self.distributed.manager.export_index(
                shard.index_name
            )
            
            # Filter data for shard's key range
            # TODO: Implement key range filtering
            
            # Import to target node
            success = await self.distributed.manager.import_index(
                shard.index_name,
                index_data,
                target_node
            )
            
            if success:
                # Update shard info
                shard.node_id = target_node
                shard.state = ShardState.ACTIVE
                shard.last_modified = datetime.now()
                
                # Update partition maps
                self._update_partition_maps(shard_id, target_node)
                
            else:
                raise Exception("Shard migration failed")
                
        except Exception as e:
            logger.error(f"Shard migration failed: {str(e)}")
            shard.state = ShardState.ACTIVE
            shard.node_id = source_node
            
    def _update_partition_maps(self, shard_id: str, new_node: str):
        """Update partition maps after shard migration."""
        for partition_map in self.partition_maps.values():
            for key, shard_ids in partition_map.shard_mapping.items():
                if shard_id in shard_ids:
                    partition_map.version += 1
                    partition_map.last_updated = datetime.now()
                    
    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        asyncio.create_task(self._monitor_shards())
        asyncio.create_task(self._check_rebalance())
        
    async def _monitor_shards(self):
        """Monitor shard statistics."""
        while True:
            try:
                await self._collect_shard_stats()
                await asyncio.sleep(
                    self.config["monitoring"]["shard_stats_interval_seconds"]
                )
            except Exception as e:
                logger.error(f"Shard monitoring error: {str(e)}")
                
    async def _collect_shard_stats(self):
        """Collect statistics for all shards."""
        for shard in self.shards.values():
            try:
                stats = await self.distributed.manager.get_index_stats(
                    shard.index_name,
                    shard.node_id
                )
                
                if stats:
                    shard.size_bytes = stats.size_bytes
                    shard.record_count = stats.record_count
                    shard.last_modified = datetime.now()
                    
            except Exception as e:
                logger.error(f"Stats collection failed for {shard.shard_id}: {str(e)}")
                
    async def _check_rebalance(self):
        """Periodically check and initiate rebalancing."""
        while True:
            try:
                await self.rebalance_shards()
                await asyncio.sleep(
                    self.config["monitoring"]["rebalance_check_interval_minutes"] * 60
                )
            except Exception as e:
                logger.error(f"Rebalance check error: {str(e)}") 