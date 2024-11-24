import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from datapunk_shared.cache.cluster_manager import ClusterNode, ClusterManager
from datapunk_shared.cache.cluster_rebalancer import (
    ClusterRebalancer,
    RebalanceStrategy
)
from datapunk_shared.cache.cache_types import CacheConfig, InvalidationStrategy

@pytest.fixture
def mock_redis():
    return AsyncMock(
        get=AsyncMock(return_value=b'{"value": "test"}'),
        set=AsyncMock(),
        delete=AsyncMock(),
        scan=AsyncMock(),
        pipeline=AsyncMock(),
        pubsub=AsyncMock(),
        close=AsyncMock()
    )

@pytest.fixture
def test_nodes():
    return [
        ClusterNode("node1", "localhost", 6379, True),
        ClusterNode("node2", "localhost", 6380),
        ClusterNode("node3", "localhost", 6381)
    ]

@pytest.fixture
def cache_config():
    return CacheConfig(
        strategy="write_through",
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=300,
        namespace="test"
    )

class TestClusterManager:
    @pytest.mark.asyncio
    async def test_cluster_initialization(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            
            # Execute
            await manager.start()
            
            # Verify
            assert manager._master_node is not None
            assert len(manager._hash_ring) > 0
            assert all(node.status == "connected" for node in manager.nodes.values())

    @pytest.mark.asyncio
    async def test_consistent_hashing(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            await manager.start()
            
            # Execute
            assignments = {}
            for i in range(1000):
                key = f"test_key_{i}"
                node = await manager.get_node_for_key(key)
                assignments[node.node_id] = assignments.get(node.node_id, 0) + 1
            
            # Verify distribution
            total = sum(assignments.values())
            for count in assignments.values():
                # Each node should get roughly 33% ±10% of keys
                assert 0.23 <= count/total <= 0.43

    @pytest.mark.asyncio
    async def test_node_failure_handling(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            await manager.start()
            
            # Simulate node failure
            mock_redis.ping.side_effect = Exception("Connection lost")
            
            # Execute
            await manager._run_heartbeat()
            
            # Verify
            assert any(node.status == "error" for node in manager.nodes.values())
            assert manager._master_node.status == "connected"

class TestClusterRebalancer:
    @pytest.mark.asyncio
    async def test_rebalance_immediate(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            await manager.start()
            
            rebalancer = ClusterRebalancer(
                manager,
                strategy=RebalanceStrategy.IMMEDIATE
            )
            
            # Mock scan to return some keys
            mock_redis.scan.side_effect = [
                (1, [b"test:key1", b"test:key2"]),
                (0, [b"test:key3"])
            ]
            
            # Execute
            await rebalancer.start_rebalance()
            
            # Verify
            assert mock_redis.get.call_count == 3
            assert mock_redis.set.call_count == 3
            assert mock_redis.delete.call_count == 1  # Pipeline execution

    @pytest.mark.asyncio
    async def test_rebalance_gradual(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            await manager.start()
            
            rebalancer = ClusterRebalancer(
                manager,
                strategy=RebalanceStrategy.GRADUAL,
                batch_size=2
            )
            
            # Mock scan to return some keys
            mock_redis.scan.side_effect = [
                (1, [b"test:key1", b"test:key2"]),
                (0, [b"test:key3"])
            ]
            
            # Execute
            await rebalancer.start_rebalance()
            
            # Verify gradual movement
            assert mock_redis.get.call_count == 3
            assert mock_redis.set.call_count == 3
            assert mock_redis.delete.call_count == 3  # Individual deletes

    @pytest.mark.asyncio
    async def test_rebalance_cancellation(self, test_nodes, cache_config, mock_redis):
        # Setup
        with patch('aioredis.from_url', return_value=mock_redis):
            manager = ClusterManager(cache_config, test_nodes)
            await manager.start()
            
            rebalancer = ClusterRebalancer(manager)
            
            # Mock scan to return many keys
            mock_redis.scan.return_value = (0, [f"test:key{i}".encode() for i in range(100)])
            
            # Execute rebalance in background
            task = asyncio.create_task(rebalancer.start_rebalance())
            
            # Cancel after small delay
            await asyncio.sleep(0.1)
            await rebalancer.stop_rebalance()
            await task
            
            # Verify partial execution
            assert mock_redis.get.call_count < 100
            assert not rebalancer._rebalancing 