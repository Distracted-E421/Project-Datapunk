import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch

from ..src.storage.index.sharding import (
    ShardManager,
    ShardState,
    PartitionStrategy,
    ShardInfo,
    PartitionMap
)
from ..src.storage.index.distributed import (
    DistributedManager,
    NodeRole,
    NodeState,
    Node
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.monitor import IndexMonitor
from ..src.storage.index.security import SecurityManager

class TestShardingSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "sharding_config.json"
        
        # Create test configuration
        config = {
            "sharding": {
                "default_strategy": "hash",
                "virtual_nodes": 8,  # Small number for testing
                "min_shard_size_mb": 1,
                "max_shard_size_mb": 10,
                "rebalance_threshold": 0.2
            },
            "partitioning": {
                "max_partitions": 16,
                "partition_size_mb": 5,
                "replication_factor": 2
            },
            "monitoring": {
                "shard_stats_interval_seconds": 1,
                "rebalance_check_interval_minutes": 1
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
            None,  # No config needed
            "test_node"
        )
        
        # Initialize shard manager
        self.shard_manager = ShardManager(
            self.distributed,
            self.config_path
        )
        
        # Create test data
        self._create_test_data()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_data(self):
        """Create test nodes and indexes."""
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
        
        # Create test index data
        self.test_data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        
    def test_consistent_hashing(self):
        """Test consistent hashing ring."""
        # Verify ring initialization
        self.assertTrue(len(self.shard_manager.ring) > 0)
        self.assertEqual(
            len(self.shard_manager.ring),
            len(self.test_nodes) * 
            self.shard_manager.config["sharding"]["virtual_nodes"]
        )
        
        # Test node lookup
        node = self.shard_manager._find_node("test_key")
        self.assertIn(node, self.test_nodes)
        
        # Test consistent mapping
        node2 = self.shard_manager._find_node("test_key")
        self.assertEqual(node, node2)
        
    def test_partition_map_creation(self):
        """Test partition map creation."""
        # Create partition map
        partition_id = self.shard_manager.create_partition_map(
            "test_index",
            PartitionStrategy.HASH,
            [(0, 100), (100, 200)]
        )
        
        # Verify partition map
        self.assertIn(partition_id, self.shard_manager.partition_maps)
        partition_map = self.shard_manager.partition_maps[partition_id]
        
        self.assertEqual(partition_map.strategy, PartitionStrategy.HASH)
        self.assertEqual(len(partition_map.key_ranges), 2)
        self.assertEqual(partition_map.version, 1)
        
    def test_shard_creation(self):
        """Test shard creation."""
        # Create shard
        shard_id = self.shard_manager.create_shard(
            "test_index",
            (0, 100)
        )
        
        # Verify shard
        self.assertIn(shard_id, self.shard_manager.shards)
        shard = self.shard_manager.shards[shard_id]
        
        self.assertEqual(shard.index_name, "test_index")
        self.assertEqual(shard.key_range, (0, 100))
        self.assertEqual(shard.state, ShardState.ACTIVE)
        
    @patch('aiohttp.ClientSession.get')
    async def test_shard_migration(self, mock_get):
        """Test shard migration."""
        # Create shard
        shard_id = self.shard_manager.create_shard(
            "test_index",
            (0, 100),
            "node1"
        )
        
        # Mock responses
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: self.test_data)
            
        # Migrate shard
        await self.shard_manager._migrate_shard(shard_id, "node2")
        
        # Verify migration
        shard = self.shard_manager.shards[shard_id]
        self.assertEqual(shard.node_id, "node2")
        self.assertEqual(shard.state, ShardState.ACTIVE)
        
    async def test_rebalancing(self):
        """Test shard rebalancing."""
        # Create imbalanced shards
        shard1 = self.shard_manager.create_shard(
            "test_index",
            (0, 100),
            "node1"
        )
        self.shard_manager.shards[shard1].size_bytes = 1024 * 1024 * 100  # 100MB
        
        shard2 = self.shard_manager.create_shard(
            "test_index",
            (100, 200),
            "node1"
        )
        self.shard_manager.shards[shard2].size_bytes = 1024 * 1024 * 100  # 100MB
        
        # Node1 has 200MB, Node2 has 0MB
        
        # Trigger rebalance
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = \
                asyncio.coroutine(lambda: self.test_data)
                
            await self.shard_manager.rebalance_shards()
            
        # Verify rebalance
        node1_load = sum(
            shard.size_bytes
            for shard in self.shard_manager.shards.values()
            if shard.node_id == "node1"
        )
        
        node2_load = sum(
            shard.size_bytes
            for shard in self.shard_manager.shards.values()
            if shard.node_id == "node2"
        )
        
        # Should be more balanced now
        self.assertLess(abs(node1_load - node2_load), 1024 * 1024 * 100)
        
    @patch('aiohttp.ClientSession.get')
    async def test_shard_monitoring(self, mock_get):
        """Test shard statistics monitoring."""
        # Create shard
        shard_id = self.shard_manager.create_shard(
            "test_index",
            (0, 100)
        )
        
        # Mock stats response
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.json = \
            asyncio.coroutine(lambda: {
                "size_bytes": 1024 * 1024,
                "record_count": 1000
            })
            
        # Collect stats
        await self.shard_manager._collect_shard_stats()
        
        # Verify stats updated
        shard = self.shard_manager.shards[shard_id]
        self.assertEqual(shard.size_bytes, 1024 * 1024)
        self.assertEqual(shard.record_count, 1000)
        
    def test_partition_strategies(self):
        """Test different partition strategies."""
        # Test hash partitioning
        hash_id = self.shard_manager.create_partition_map(
            "test_index",
            PartitionStrategy.HASH
        )
        self.assertEqual(
            self.shard_manager.partition_maps[hash_id].strategy,
            PartitionStrategy.HASH
        )
        
        # Test range partitioning
        range_id = self.shard_manager.create_partition_map(
            "test_index",
            PartitionStrategy.RANGE,
            [(0, 100), (100, 200)]
        )
        self.assertEqual(
            self.shard_manager.partition_maps[range_id].strategy,
            PartitionStrategy.RANGE
        )
        
        # Test composite partitioning
        composite_id = self.shard_manager.create_partition_map(
            "test_index",
            PartitionStrategy.COMPOSITE
        )
        self.assertEqual(
            self.shard_manager.partition_maps[composite_id].strategy,
            PartitionStrategy.COMPOSITE
        )