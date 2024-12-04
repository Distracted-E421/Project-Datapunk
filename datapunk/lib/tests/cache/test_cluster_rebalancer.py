import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime
import asyncio

from datapunk_shared.cache.cluster_rebalancer import (
    ClusterRebalancer,
    RebalanceStrategy,
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
    redis.get = AsyncMock()
    redis.set = AsyncMock()
    redis.delete = AsyncMock()
    redis.ttl = AsyncMock()
    redis.scan = AsyncMock()
    redis.pipeline = Mock(return_value=AsyncMock())
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
    nodes = [
        ClusterNode("node1", "localhost", 6379, is_master=True, weight=1),
        ClusterNode("node2", "localhost", 6380, is_master=False, weight=1),
        ClusterNode("node3", "localhost", 6381, is_master=False, weight=2)
    ]
    for node in nodes:
        node.status = "connected"
        node.connection = AsyncMock()
    return nodes

@pytest.fixture
def cluster_manager(cache_config, cluster_nodes, mock_metrics):
    """Create cluster manager instance."""
    manager = ClusterManager(cache_config, cluster_nodes, mock_metrics)
    manager._master_node = cluster_nodes[0]
    manager._build_hash_ring()
    return manager

@pytest.fixture
def rebalancer(cluster_manager):
    """Create cluster rebalancer instance."""
    rebalancer = ClusterRebalancer(
        cluster_manager,
        strategy=RebalanceStrategy.GRADUAL,
        batch_size=10,
        sleep_between_batches=0.1
    )
    return rebalancer

class TestClusterRebalancer:
    @pytest.mark.asyncio
    async def test_identify_keys_to_move(self, rebalancer, mock_redis):
        """Test identification of keys that need to be moved."""
        # Setup mock scan results
        mock_redis.scan.side_effect = [
            (1, ["test:key1", "test:key2"]),
            (0, ["test:key3"])
        ]
        
        keys_to_move = await rebalancer._identify_keys_to_move()
        
        assert isinstance(keys_to_move, dict)
        assert len(keys_to_move) > 0
        assert all(isinstance(k, str) for k in keys_to_move.keys())
        assert all(isinstance(v, str) for v in keys_to_move.values())

    @pytest.mark.asyncio
    async def test_immediate_rebalance(self, rebalancer, mock_redis):
        """Test immediate rebalancing strategy."""
        # Setup test data
        keys_to_move = {
            "test:key1": "node2",
            "test:key2": "node3"
        }
        mock_redis.get.return_value = "test_value"
        mock_redis.ttl.return_value = 3000
        
        await rebalancer._rebalance_immediate(keys_to_move)
        
        # Verify key transfers
        assert mock_redis.get.call_count == len(keys_to_move)
        assert mock_redis.ttl.call_count == len(keys_to_move)
        assert mock_redis.set.call_count == len(keys_to_move)
        assert mock_redis.pipeline.called

    @pytest.mark.asyncio
    async def test_gradual_rebalance(self, rebalancer, mock_redis):
        """Test gradual rebalancing strategy."""
        # Setup test data
        keys_to_move = {
            "test:key1": "node2",
            "test:key2": "node3"
        }
        mock_redis.get.return_value = "test_value"
        mock_redis.ttl.return_value = 3000
        
        await rebalancer._rebalance_gradual(keys_to_move)
        
        # Verify key transfers
        assert mock_redis.get.call_count == len(keys_to_move)
        assert mock_redis.ttl.call_count == len(keys_to_move)
        assert mock_redis.set.call_count == len(keys_to_move)
        assert mock_redis.delete.call_count == len(keys_to_move)

    @pytest.mark.asyncio
    async def test_off_peak_rebalance(self, rebalancer, mock_redis):
        """Test off-peak rebalancing strategy."""
        # Setup test data
        keys_to_move = {
            "test:key1": "node2",
            "test:key2": "node3"
        }
        
        # Mock datetime to simulate off-peak hours
        with patch('datetime.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2023, 1, 1, 3, 0)  # 3 AM
            
            await rebalancer._rebalance_off_peak(keys_to_move)
            
            # Verify rebalancing occurred during off-peak
            assert mock_redis.get.called
            assert mock_redis.set.called

    @pytest.mark.asyncio
    async def test_start_stop_rebalance(self, rebalancer):
        """Test starting and stopping rebalance process."""
        # Start rebalance in background
        start_task = asyncio.create_task(rebalancer.start_rebalance())
        
        # Wait briefly then stop
        await asyncio.sleep(0.1)
        await rebalancer.stop_rebalance()
        
        await start_task
        
        assert rebalancer._rebalancing is False
        assert rebalancer._cancel_rebalancing is True

    @pytest.mark.asyncio
    async def test_error_handling(self, rebalancer, mock_redis):
        """Test error handling during rebalancing."""
        # Simulate Redis error
        mock_redis.get.side_effect = Exception("Redis error")
        
        keys_to_move = {"test:key1": "node2"}
        
        # Should handle errors gracefully
        await rebalancer._rebalance_gradual(keys_to_move)
        
        assert mock_redis.get.called
        assert not mock_redis.set.called  # Should not attempt to set after error

    @pytest.mark.asyncio
    async def test_concurrent_rebalance_prevention(self, rebalancer):
        """Test prevention of concurrent rebalancing."""
        # Start first rebalance
        rebalancer._rebalancing = True
        
        # Attempt second rebalance
        await rebalancer.start_rebalance()
        
        # Should log warning and not proceed
        assert rebalancer._rebalancing is True 