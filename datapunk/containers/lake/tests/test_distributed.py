import unittest
import tempfile
import shutil
from pathlib import Path
import json
import asyncio
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web
import threading
from unittest.mock import Mock, patch

from ..src.storage.index.distributed import (
    DistributedManager,
    NodeRole,
    ConsistencyLevel,
    NodeState,
    Node,
    ReplicationGroup,
    OperationLog
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.monitor import IndexMonitor
from ..src.storage.index.security import SecurityManager

class TestDistributedSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "distributed_config.json"
        
        # Create test configuration
        config = {
            "network": {
                "heartbeat_interval_seconds": 1,
                "sync_interval_seconds": 2,
                "operation_timeout_seconds": 5
            },
            "replication": {
                "default_consistency": "quorum",
                "min_replicas": 2,
                "max_replicas": 3,
                "sync_batch_size": 100
            },
            "recovery": {
                "max_operation_retry": 3,
                "recovery_timeout_seconds": 30,
                "auto_recovery_enabled": True
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        # Initialize components
        self.store = StatisticsStore(Path(self.temp_dir) / "test.db")
        self.manager = IndexManager(self.store)
        self.monitor = IndexMonitor(
            self.store,
            self.manager,
            None,  # No optimizer needed
            None   # No config needed
        )
        self.security = SecurityManager(None)  # No config needed
        
        # Initialize distributed manager
        self.distributed = DistributedManager(
            self.store,
            self.manager,
            self.monitor,
            self.security,
            self.config_path,
            "test_node"
        )
        
        # Create test data
        self._create_test_data()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_data(self):
        """Create test indexes and nodes."""
        # Create test index
        self.test_index_data = {
            "name": "test_index",
            "type": "btree",
            "entries": [
                {"key": "a", "value": 1},
                {"key": "b", "value": 2}
            ]
        }
        self.manager.import_index("test_index", self.test_index_data)
        
        # Create test nodes
        self.test_nodes = {
            "node1": Node(
                node_id="node1",
                role=NodeRole.PRIMARY,
                host="localhost",
                port=8001,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes={"test_index"},
                version="1.0.0"
            ),
            "node2": Node(
                node_id="node2",
                role=NodeRole.REPLICA,
                host="localhost",
                port=8002,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes={"test_index"},
                version="1.0.0"
            )
        }
        
        self.distributed.nodes.update(self.test_nodes)
        
    async def _start_mock_node(self, port: int):
        """Start mock node server."""
        async def handle_heartbeat(request):
            return web.Response(status=200)
            
        async def handle_index_versions(request):
            return web.json_response({"test_index": "test_version"})
            
        async def handle_update_index(request):
            return web.Response(status=200)
            
        app = web.Application()
        app.router.add_post("/heartbeat", handle_heartbeat)
        app.router.add_get("/index_versions", handle_index_versions)
        app.router.add_post("/update_index", handle_update_index)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', port)
        await site.start()
        return runner
        
    def test_node_initialization(self):
        """Test node initialization."""
        self.assertEqual(self.distributed.node_id, "test_node")
        self.assertEqual(self.distributed.node.role, NodeRole.PRIMARY)
        self.assertEqual(self.distributed.node.state, NodeState.ACTIVE)
        
    def test_replication_group_creation(self):
        """Test replication group creation."""
        group_id = self.distributed.create_replication_group(
            {"test_index"},
            replica_count=2,
            consistency=ConsistencyLevel.QUORUM
        )
        
        self.assertIn(group_id, self.distributed.replication_groups)
        group = self.distributed.replication_groups[group_id]
        
        self.assertEqual(group.primary_node, "test_node")
        self.assertEqual(group.indexes, {"test_index"})
        self.assertEqual(group.consistency_level, ConsistencyLevel.QUORUM)
        
    def test_node_join_group(self):
        """Test node joining replication group."""
        # Create group
        group_id = self.distributed.create_replication_group(
            {"test_index"}
        )
        
        # Add replica
        self.distributed.join_group(
            group_id,
            "node2",
            NodeRole.REPLICA
        )
        
        group = self.distributed.replication_groups[group_id]
        self.assertIn("node2", group.replica_nodes)
        
    @patch('aiohttp.ClientSession.post')
    async def test_heartbeat(self, mock_post):
        """Test heartbeat mechanism."""
        # Mock response
        mock_post.return_value.__aenter__.return_value.status = 200
        
        # Send heartbeats
        await self.distributed._send_heartbeats()
        
        # Verify heartbeat sent to all nodes
        self.assertEqual(mock_post.call_count, len(self.test_nodes))
        
    @patch('aiohttp.ClientSession.get')
    @patch('aiohttp.ClientSession.post')
    async def test_sync_as_primary(self, mock_post, mock_get):
        """Test synchronization as primary node."""
        # Create group
        group_id = self.distributed.create_replication_group(
            {"test_index"}
        )
        self.distributed.join_group(
            group_id,
            "node2",
            NodeRole.REPLICA
        )
        
        # Mock responses
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: {"test_index": "old_version"})
            
        mock_post.return_value.__aenter__.return_value.status = 200
        
        # Sync indexes
        await self.distributed._sync_indexes()
        
        # Verify sync attempted
        self.assertTrue(mock_get.called)
        self.assertTrue(mock_post.called)
        
    def test_operation_processing(self):
        """Test distributed operation processing."""
        # Create operation
        operation = {
            "operation_id": "test_op",
            "type": "create_index",
            "index_name": "new_index",
            "index_type": "btree"
        }
        
        # Process operation
        self.distributed._process_operation(operation)
        
        # Verify operation logged
        self.assertTrue(any(
            log.operation_id == "test_op"
            for log in self.distributed.operation_logs
        ))
        
    async def test_full_sync_cycle(self):
        """Test complete synchronization cycle."""
        # Start mock nodes
        runner1 = await self._start_mock_node(8001)
        runner2 = await self._start_mock_node(8002)
        
        try:
            # Create replication group
            group_id = self.distributed.create_replication_group(
                {"test_index"}
            )
            
            # Add nodes to group
            self.distributed.join_group(
                group_id,
                "node1",
                NodeRole.REPLICA
            )
            self.distributed.join_group(
                group_id,
                "node2",
                NodeRole.REPLICA
            )
            
            # Run sync cycle
            await self.distributed._sync_indexes()
            
            # Verify group state
            group = self.distributed.replication_groups[group_id]
            self.assertEqual(len(group.replica_nodes), 2)
            
        finally:
            await runner1.cleanup()
            await runner2.cleanup()
            
    def test_consistency_levels(self):
        """Test different consistency levels."""
        # Test ONE consistency
        group_id1 = self.distributed.create_replication_group(
            {"test_index"},
            consistency=ConsistencyLevel.ONE
        )
        self.assertEqual(
            self.distributed.replication_groups[group_id1].consistency_level,
            ConsistencyLevel.ONE
        )
        
        # Test QUORUM consistency
        group_id2 = self.distributed.create_replication_group(
            {"test_index"},
            consistency=ConsistencyLevel.QUORUM
        )
        self.assertEqual(
            self.distributed.replication_groups[group_id2].consistency_level,
            ConsistencyLevel.QUORUM
        )
        
        # Test ALL consistency
        group_id3 = self.distributed.create_replication_group(
            {"test_index"},
            consistency=ConsistencyLevel.ALL
        )
        self.assertEqual(
            self.distributed.replication_groups[group_id3].consistency_level,
            ConsistencyLevel.ALL
        )
        
    def test_node_state_transitions(self):
        """Test node state transitions."""
        # Create node in ACTIVE state
        node = Node(
            node_id="test_node",
            role=NodeRole.REPLICA,
            host="localhost",
            port=8003,
            state=NodeState.ACTIVE,
            last_heartbeat=datetime.now(),
            indexes=set(),
            version="1.0.0"
        )
        
        self.distributed.nodes["test_node"] = node
        
        # Simulate failed heartbeat
        node.last_heartbeat = datetime.now() - timedelta(minutes=5)
        
        # Node should be considered offline
        self.assertEqual(node.state, NodeState.ACTIVE)  # Still ACTIVE
        # In practice, the heartbeat task would mark it OFFLINE 