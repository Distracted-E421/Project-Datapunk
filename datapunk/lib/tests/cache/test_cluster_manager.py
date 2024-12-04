import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime
import aioredis

from datapunk_shared.cache.cluster_manager import (
    ClusterNode,
    ClusterManager,
    CacheConfig,
    CacheStrategy,
    InvalidationStrategy
)

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.ping = AsyncMock()
    redis.publish = AsyncMock()
    redis.close = AsyncMock()
    return redis

@pytest.fixture
def mock_metrics():
    """Mock metrics client."""
    metrics = Mock()
    metrics.increment_counter = AsyncMock()
    metrics.gauge = AsyncMock()
    return metrics

@pytest.fixture
def cache_config():
    """Create cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=3600,
        namespace="test"
    )

@pytest.fixture
def cluster_nodes():
    """Create list of cluster nodes."""
    return [
        ClusterNode("node1", "localhost", 6379, is_master=False, weight=1),
        ClusterNode("node2", "localhost", 6380, is_master=False, weight=1),
        ClusterNode("node3", "localhost", 6381, is_master=False, weight=2)
    ]

@pytest.fixture
async def cluster_manager(cache_config, cluster_nodes, mock_redis, mock_metrics):
    """Create cluster manager instance."""
    with patch('aioredis.from_url', return_value=mock_redis):
        manager = ClusterManager(
            config=cache_config,
            nodes=cluster_nodes,
            metrics_client=mock_metrics
        )
        await manager.start()
        yield manager
        await manager.stop()

class TestClusterNode:
    def test_node_initialization(self):
        """Test cluster node initialization."""
        node = ClusterNode("test_node", "localhost", 6379, is_master=True, weight=2)
        
        assert node.node_id == "test_node"
        assert node.host == "localhost"
        assert node.port == 6379
        assert node.is_master is True
        assert node.weight == 2
        assert node.status == "connecting"
        assert node.last_heartbeat is None
        assert node.connection is None

class TestClusterManager:
    @pytest.mark.asyncio
    async def test_start_cluster(self, cluster_manager, mock_redis):
        """Test cluster startup."""
        assert cluster_manager._running is True
        assert cluster_manager._master_node is not None
        assert len(cluster_manager._hash_ring) > 0
        assert cluster_manager._heartbeat_task is not None
        assert cluster_manager._sync_task is not None

    @pytest.mark.asyncio
    async def test_stop_cluster(self, cluster_manager, mock_redis):
        """Test cluster shutdown."""
        await cluster_manager.stop()
        
        assert cluster_manager._running is False
        assert mock_redis.close.called

    @pytest.mark.asyncio
    async def test_node_connection(self, cache_config, cluster_nodes, mock_redis, mock_metrics):
        """Test node connection process."""
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, cluster_nodes, mock_metrics)
            await manager._connect_nodes()
            
            for node in manager.nodes.values():
                assert node.status == "connected"
                assert node.connection is not None

    @pytest.mark.asyncio
    async def test_master_election(self, cluster_manager):
        """Test master node election."""
        master = cluster_manager._master_node
        assert master is not None
        assert master.is_master is True
        # Should elect node with lowest ID as master
        assert master.node_id == min(n.node_id for n in cluster_manager.nodes.values())

    @pytest.mark.asyncio
    async def test_hash_ring_distribution(self, cluster_manager):
        """Test hash ring key distribution."""
        # Test multiple keys to verify distribution
        test_keys = [f"key{i}" for i in range(100)]
        node_counts = {node.node_id: 0 for node in cluster_manager.nodes.values()}
        
        for key in test_keys:
            node = await cluster_manager.get_node_for_key(key)
            node_counts[node.node_id] += 1
        
        # Verify each node got some keys
        assert all(count > 0 for count in node_counts.values())
        # Node with weight=2 should get roughly twice as many keys
        high_weight_node = [n for n in cluster_manager.nodes.values() if n.weight == 2][0]
        assert node_counts[high_weight_node.node_id] > sum(
            node_counts[n.node_id] for n in cluster_manager.nodes.values()
            if n.weight == 1
        ) / len([n for n in cluster_manager.nodes.values() if n.weight == 1])

    @pytest.mark.asyncio
    async def test_key_sync(self, cluster_manager, mock_redis):
        """Test key synchronization across cluster."""
        test_key = "test:sync_key"
        test_value = {"data": "test"}
        
        await cluster_manager.sync_key(test_key, test_value, ttl=3600)
        
        assert mock_redis.publish.called
        publish_args = mock_redis.publish.call_args[0]
        assert publish_args[0] == "test:sync"
        sync_data = json.loads(publish_args[1])
        assert sync_data["key"] == test_key
        assert sync_data["value"] == test_value
        assert sync_data["ttl"] == 3600

    @pytest.mark.asyncio
    async def test_heartbeat_monitoring(self, cluster_manager, mock_redis):
        """Test node heartbeat monitoring."""
        # Simulate successful heartbeat
        await cluster_manager._run_heartbeat()
        
        assert mock_redis.ping.called
        for node in cluster_manager.nodes.values():
            assert node.last_heartbeat is not None
            assert node.status == "connected"

    @pytest.mark.asyncio
    async def test_node_failure_handling(self, cluster_manager, mock_redis):
        """Test handling of node failures."""
        # Simulate node failure
        mock_redis.ping.side_effect = Exception("Connection lost")
        await cluster_manager._run_heartbeat()
        
        # Should trigger re-election if master fails
        if cluster_manager._master_node.status == "error":
            assert any(n.is_master for n in cluster_manager.nodes.values())
        
        # Hash ring should be rebuilt
        assert len(cluster_manager._hash_ring) > 0

    @pytest.mark.asyncio
    async def test_metrics_recording(self, cluster_manager, mock_metrics):
        """Test cluster metrics recording."""
        await cluster_manager._run_heartbeat()
        
        assert mock_metrics.gauge.called
        gauge_args = mock_metrics.gauge.call_args[0]
        assert gauge_args[0] == "cache_cluster_nodes"
        assert isinstance(gauge_args[1], int) 