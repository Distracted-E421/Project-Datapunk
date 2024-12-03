import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime, timedelta

from datapunk_shared.cache.invalidation_manager import (
    InvalidationManager,
    CacheConfig,
    InvalidationStrategy,
    CacheEntry,
    CacheStrategy
)

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock()
    redis.delete = AsyncMock()
    redis.scan = AsyncMock()
    return redis

@pytest.fixture
def mock_metrics():
    """Mock metrics client."""
    metrics = Mock()
    metrics.increment_counter = AsyncMock()
    metrics.record_histogram = AsyncMock()
    return metrics

@pytest.fixture
def ttl_config():
    """Create TTL-based cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=3600,
        namespace="test"
    )

@pytest.fixture
def lru_config():
    """Create LRU-based cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.LRU,
        ttl=3600,
        namespace="test"
    )

@pytest.fixture
def lfu_config():
    """Create LFU-based cache configuration."""
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.LFU,
        ttl=3600,
        namespace="test"
    )

@pytest.fixture
async def invalidation_manager(ttl_config, mock_redis, mock_metrics):
    """Create invalidation manager instance."""
    manager = InvalidationManager(ttl_config, mock_redis, mock_metrics)
    await manager.start()
    yield manager
    await manager.stop()

class TestInvalidationManager:
    @pytest.mark.asyncio
    async def test_start_stop(self, invalidation_manager):
        """Test manager startup and shutdown."""
        assert invalidation_manager._running is True
        
        await invalidation_manager.stop()
        assert invalidation_manager._running is False
        assert invalidation_manager._cleanup_task is None

    @pytest.mark.asyncio
    async def test_ttl_invalidation(self, invalidation_manager):
        """Test TTL-based invalidation strategy."""
        # Test expired entry
        expired_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() - timedelta(hours=1)).isoformat()
        )
        should_invalidate = await invalidation_manager.should_invalidate(expired_entry)
        assert should_invalidate is True
        
        # Test valid entry
        valid_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        should_invalidate = await invalidation_manager.should_invalidate(valid_entry)
        assert should_invalidate is False

    @pytest.mark.asyncio
    async def test_lru_invalidation(self, lru_config, mock_redis, mock_metrics):
        """Test LRU-based invalidation strategy."""
        manager = InvalidationManager(lru_config, mock_redis, mock_metrics)
        
        # Test old access
        old_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat(),
            last_accessed=(datetime.now() - timedelta(hours=2)).isoformat()
        )
        should_invalidate = await manager.should_invalidate(old_entry)
        assert should_invalidate is True
        
        # Test recent access
        recent_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat(),
            last_accessed=datetime.now().isoformat()
        )
        should_invalidate = await manager.should_invalidate(recent_entry)
        assert should_invalidate is False

    @pytest.mark.asyncio
    async def test_lfu_invalidation(self, lfu_config, mock_redis, mock_metrics):
        """Test LFU-based invalidation strategy."""
        manager = InvalidationManager(lfu_config, mock_redis, mock_metrics)
        
        # Test unused entry
        unused_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat(),
            access_count=0
        )
        should_invalidate = await manager.should_invalidate(unused_entry)
        assert should_invalidate is True
        
        # Test frequently used entry
        used_entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat(),
            access_count=10
        )
        should_invalidate = await manager.should_invalidate(used_entry)
        assert should_invalidate is False

    @pytest.mark.asyncio
    async def test_cleanup_process(self, invalidation_manager, mock_redis):
        """Test cleanup process execution."""
        # Setup mock scan results
        mock_redis.scan.side_effect = [
            (1, ["test:key1", "test:key2"]),
            (0, ["test:key3"])
        ]
        
        # Setup mock get results
        expired_entry = CacheEntry(
            key="key1",
            value="value1",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() - timedelta(hours=1)).isoformat()
        )
        valid_entry = CacheEntry(
            key="key2",
            value="value2",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=1)).isoformat()
        )
        
        mock_redis.get.side_effect = [
            json.dumps(expired_entry.__dict__),
            json.dumps(valid_entry.__dict__),
            None  # Simulate missing key
        ]
        
        count = await invalidation_manager._cleanup_entries()
        
        assert count == 1  # Only expired entry should be removed
        assert mock_redis.delete.call_count == 1

    @pytest.mark.asyncio
    async def test_error_handling(self, invalidation_manager, mock_redis):
        """Test error handling during cleanup."""
        # Simulate Redis error
        mock_redis.scan.side_effect = Exception("Redis error")
        
        count = await invalidation_manager._cleanup_entries()
        assert count == 0  # Should handle error gracefully

    @pytest.mark.asyncio
    async def test_metrics_recording(self, invalidation_manager, mock_redis, mock_metrics):
        """Test metrics recording during cleanup."""
        # Setup mock scan results
        mock_redis.scan.return_value = (0, ["test:key1"])
        mock_redis.get.return_value = json.dumps(CacheEntry(
            key="key1",
            value="value1",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() - timedelta(hours=1)).isoformat()
        ).__dict__)
        
        await invalidation_manager._cleanup_entries()
        
        assert mock_metrics.increment_counter.called
        assert mock_metrics.record_histogram.called 