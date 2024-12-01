from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from enum import Enum
import asyncio
import aiohttp
import hashlib
import time
from collections import defaultdict
import threading
import queue

from .manager import IndexManager
from .stats import StatisticsStore
from .monitor import IndexMonitor
from .security import SecurityManager

logger = logging.getLogger(__name__)

class NodeRole(Enum):
    """Node roles in the distributed system."""
    PRIMARY = "primary"
    REPLICA = "replica"
    COORDINATOR = "coordinator"

class ConsistencyLevel(Enum):
    """Consistency levels for operations."""
    ONE = "one"           # Write/read from any node
    QUORUM = "quorum"     # Write/read from majority
    ALL = "all"           # Write/read from all nodes

class NodeState(Enum):
    """Node operational states."""
    ACTIVE = "active"
    SYNCING = "syncing"
    DEGRADED = "degraded"
    OFFLINE = "offline"

@dataclass
class Node:
    """Distributed node information."""
    node_id: str
    role: NodeRole
    host: str
    port: int
    state: NodeState
    last_heartbeat: datetime
    indexes: Set[str]
    version: str

@dataclass
class ReplicationGroup:
    """Group of nodes replicating the same data."""
    group_id: str
    primary_node: str
    replica_nodes: Set[str]
    indexes: Set[str]
    consistency_level: ConsistencyLevel

@dataclass
class OperationLog:
    """Log of distributed operations."""
    operation_id: str
    timestamp: datetime
    operation_type: str
    index_name: str
    node_id: str
    status: str
    details: Dict[str, Any]

class DistributedManager:
    """Manages distributed index operations."""
    
    def __init__(
        self,
        store: StatisticsStore,
        manager: IndexManager,
        monitor: IndexMonitor,
        security: SecurityManager,
        config_path: Optional[Union[str, Path]] = None,
        node_id: Optional[str] = None
    ):
        self.store = store
        self.manager = manager
        self.monitor = monitor
        self.security = security
        self.config_path = Path(config_path) if config_path else None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize node
        self.node_id = node_id or self._generate_node_id()
        self.node = self._initialize_node()
        
        # Initialize state
        self.nodes: Dict[str, Node] = {self.node_id: self.node}
        self.replication_groups: Dict[str, ReplicationGroup] = {}
        self.operation_logs: List[OperationLog] = []
        
        # Background tasks
        self._operation_queue = queue.Queue()
        self._worker_thread = threading.Thread(
            target=self._operation_worker,
            daemon=True
        )
        self._worker_thread.start()
        
        # Start heartbeat and sync tasks
        asyncio.create_task(self._heartbeat_task())
        asyncio.create_task(self._sync_task())
        
    def _load_config(self) -> Dict[str, Any]:
        """Load distributed configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "network": {
                    "heartbeat_interval_seconds": 5,
                    "sync_interval_seconds": 30,
                    "operation_timeout_seconds": 10
                },
                "replication": {
                    "default_consistency": "quorum",
                    "min_replicas": 2,
                    "max_replicas": 5,
                    "sync_batch_size": 1000
                },
                "recovery": {
                    "max_operation_retry": 3,
                    "recovery_timeout_seconds": 300,
                    "auto_recovery_enabled": True
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _generate_node_id(self) -> str:
        """Generate unique node ID."""
        return hashlib.sha256(
            f"{time.time()}:{id(self)}".encode()
        ).hexdigest()[:12]
        
    def _initialize_node(self) -> Node:
        """Initialize local node."""
        return Node(
            node_id=self.node_id,
            role=NodeRole.PRIMARY,  # Initial role, may change
            host="localhost",  # TODO: Get from config
            port=8000,        # TODO: Get from config
            state=NodeState.ACTIVE,
            last_heartbeat=datetime.now(),
            indexes=set(),
            version="1.0.0"   # TODO: Get from package
        )
        
    async def _heartbeat_task(self):
        """Send heartbeats to other nodes."""
        while True:
            try:
                await self._send_heartbeats()
                await asyncio.sleep(
                    self.config["network"]["heartbeat_interval_seconds"]
                )
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
                
    async def _send_heartbeats(self):
        """Send heartbeat to all known nodes."""
        async with aiohttp.ClientSession() as session:
            for node_id, node in self.nodes.items():
                if node_id == self.node_id:
                    continue
                    
                try:
                    url = f"http://{node.host}:{node.port}/heartbeat"
                    async with session.post(
                        url,
                        json={"node_id": self.node_id}
                    ) as response:
                        if response.status == 200:
                            node.last_heartbeat = datetime.now()
                        else:
                            logger.warning(
                                f"Failed heartbeat to {node_id}: {response.status}"
                            )
                except Exception as e:
                    logger.error(f"Heartbeat to {node_id} failed: {str(e)}")
                    
    async def _sync_task(self):
        """Synchronize indexes with other nodes."""
        while True:
            try:
                await self._sync_indexes()
                await asyncio.sleep(
                    self.config["network"]["sync_interval_seconds"]
                )
            except Exception as e:
                logger.error(f"Sync error: {str(e)}")
                
    async def _sync_indexes(self):
        """Synchronize indexes with replication group."""
        for group in self.replication_groups.values():
            if self.node_id == group.primary_node:
                await self._sync_as_primary(group)
            elif self.node_id in group.replica_nodes:
                await self._sync_as_replica(group)
                
    async def _sync_as_primary(self, group: ReplicationGroup):
        """Synchronize replicas as primary node."""
        for replica_id in group.replica_nodes:
            if replica_id not in self.nodes:
                continue
                
            replica = self.nodes[replica_id]
            if replica.state != NodeState.ACTIVE:
                continue
                
            try:
                # Get replica's index versions
                async with aiohttp.ClientSession() as session:
                    url = f"http://{replica.host}:{replica.port}/index_versions"
                    async with session.get(url) as response:
                        if response.status != 200:
                            continue
                            
                        replica_versions = await response.json()
                        
                # Compare and sync different versions
                for index_name in group.indexes:
                    local_version = await self._get_index_version(index_name)
                    if local_version != replica_versions.get(index_name):
                        await self._push_index_update(
                            index_name,
                            replica
                        )
            except Exception as e:
                logger.error(f"Sync to {replica_id} failed: {str(e)}")
                
    async def _sync_as_replica(self, group: ReplicationGroup):
        """Synchronize with primary node."""
        if group.primary_node not in self.nodes:
            return
            
        primary = self.nodes[group.primary_node]
        if primary.state != NodeState.ACTIVE:
            return
            
        try:
            # Get primary's index versions
            async with aiohttp.ClientSession() as session:
                url = f"http://{primary.host}:{primary.port}/index_versions"
                async with session.get(url) as response:
                    if response.status != 200:
                        return
                        
                    primary_versions = await response.json()
                    
            # Compare and request updates
            for index_name in group.indexes:
                local_version = await self._get_index_version(index_name)
                if local_version != primary_versions.get(index_name):
                    await self._pull_index_update(
                        index_name,
                        primary
                    )
        except Exception as e:
            logger.error(f"Sync from primary failed: {str(e)}")
            
    async def _get_index_version(self, index_name: str) -> str:
        """Get index version hash."""
        index_data = self.manager.export_index(index_name)
        if not index_data:
            return ""
            
        return hashlib.sha256(
            json.dumps(index_data).encode()
        ).hexdigest()
        
    async def _push_index_update(
        self,
        index_name: str,
        target_node: Node
    ):
        """Push index update to target node."""
        index_data = self.manager.export_index(index_name)
        if not index_data:
            return
            
        async with aiohttp.ClientSession() as session:
            url = f"http://{target_node.host}:{target_node.port}/update_index"
            async with session.post(
                url,
                json={
                    "index_name": index_name,
                    "data": index_data
                }
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Push to {target_node.node_id} failed: {response.status}"
                    )
                    
    async def _pull_index_update(
        self,
        index_name: str,
        source_node: Node
    ):
        """Pull index update from source node."""
        async with aiohttp.ClientSession() as session:
            url = f"http://{source_node.host}:{source_node.port}/export_index"
            async with session.get(
                url,
                params={"index_name": index_name}
            ) as response:
                if response.status != 200:
                    logger.error(
                        f"Pull from {source_node.node_id} failed: {response.status}"
                    )
                    return
                    
                index_data = await response.json()
                self.manager.import_index(index_name, index_data)
                
    def create_replication_group(
        self,
        indexes: Set[str],
        replica_count: int = None,
        consistency: ConsistencyLevel = None
    ) -> str:
        """Create new replication group."""
        if not indexes:
            raise ValueError("No indexes specified")
            
        # Use configuration defaults
        if replica_count is None:
            replica_count = self.config["replication"]["min_replicas"]
            
        if consistency is None:
            consistency = ConsistencyLevel(
                self.config["replication"]["default_consistency"]
            )
            
        # Generate group ID
        group_id = hashlib.sha256(
            f"{self.node_id}:{time.time()}:{sorted(indexes)}".encode()
        ).hexdigest()[:12]
        
        # Create group with this node as primary
        group = ReplicationGroup(
            group_id=group_id,
            primary_node=self.node_id,
            replica_nodes=set(),  # Will be assigned
            indexes=indexes,
            consistency_level=consistency
        )
        
        self.replication_groups[group_id] = group
        return group_id
        
    def join_group(
        self,
        group_id: str,
        node_id: str,
        role: NodeRole
    ):
        """Add node to replication group."""
        if group_id not in self.replication_groups:
            raise ValueError(f"Group {group_id} not found")
            
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found")
            
        group = self.replication_groups[group_id]
        
        if role == NodeRole.PRIMARY:
            if group.primary_node:
                raise ValueError("Group already has primary node")
            group.primary_node = node_id
        else:
            group.replica_nodes.add(node_id)
            
    def _operation_worker(self):
        """Process distributed operations."""
        while True:
            try:
                operation = self._operation_queue.get()
                self._process_operation(operation)
            except Exception as e:
                logger.error(f"Operation failed: {str(e)}")
            finally:
                self._operation_queue.task_done()
                
    def _process_operation(self, operation: Dict[str, Any]):
        """Process a distributed operation."""
        operation_id = operation.get("operation_id")
        if not operation_id:
            return
            
        try:
            # Execute operation
            result = self._execute_operation(operation)
            
            # Log operation
            self.operation_logs.append(
                OperationLog(
                    operation_id=operation_id,
                    timestamp=datetime.now(),
                    operation_type=operation["type"],
                    index_name=operation["index_name"],
                    node_id=self.node_id,
                    status="success" if result else "failed",
                    details=operation
                )
            )
        except Exception as e:
            logger.error(f"Operation {operation_id} failed: {str(e)}")
            
    def _execute_operation(self, operation: Dict[str, Any]) -> bool:
        """Execute a distributed operation."""
        op_type = operation.get("type")
        if not op_type:
            return False
            
        if op_type == "create_index":
            return self.manager.create_index(
                operation["index_name"],
                operation["index_type"]
            )
        elif op_type == "delete_index":
            return self.manager.delete_index(
                operation["index_name"]
            )
        elif op_type == "update_index":
            return self.manager.import_index(
                operation["index_name"],
                operation["data"]
            )
            
        return False 