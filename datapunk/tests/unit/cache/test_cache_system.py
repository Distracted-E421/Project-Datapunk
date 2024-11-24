import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
import json

from datapunk_shared.cache.cache_types import (
    CacheStrategy, InvalidationStrategy, CacheConfig, CacheEntry
)
from datapunk_shared.cache.cache_manager import CacheManager
from datapunk_shared.cache.invalidation_manager import InvalidationManager

@pytest.fixture
def mock_redis():
    return AsyncMock(
        get=AsyncMock(),
        set=AsyncMock(),
        delete=AsyncMock(),
        scan=AsyncMock(),
        pipeline=AsyncMock(),
        close=AsyncMock()
    )

@pytest.fixture
def mock_metrics():
    return AsyncMock(
        increment_counter=AsyncMock(),
        record_histogram=AsyncMock()
    )

@pytest.fixture
def cache_config():
    return CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=300,
        namespace="test"
    )

@pytest.fixture
def cache_manager(mock_redis, mock_metrics, cache_config):
    manager = CacheManager(cache_config, "redis://dummy", mock_metrics)
    manager.redis = mock_redis
    return manager

@pytest.fixture
def invalidation_manager(mock_redis, mock_metrics, cache_config):
    return InvalidationManager(cache_config, mock_redis, mock_metrics)

class TestCacheSystem:
    @pytest.mark.asyncio
    async def test_cache_get_hit(self, cache_manager, mock_redis):
        # Setup
        key = "test_key"
        value = "test_value"
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(seconds=300)).isoformat()
        )
        mock_redis.get.return_value = json.dumps(entry.__dict__)

        # Execute
        result = await cache_manager.get(key)

        # Verify
        assert result == value
        mock_redis.get.assert_called_once_with(f"test:{key}")

    @pytest.mark.asyncio
    async def test_cache_get_miss_with_fetch(self, cache_manager, mock_redis):
        # Setup
        key = "test_key"
        value = "fetched_value"
        mock_redis.get.return_value = None
        fetch_func = AsyncMock(return_value=value)

        # Execute
        result = await cache_manager.get(key, fetch_func)

        # Verify
        assert result == value
        fetch_func.assert_called_once()
        assert mock_redis.set.called

    @pytest.mark.asyncio
    async def test_write_behind_strategy(self, mock_redis, mock_metrics):
        # Setup
        config = CacheConfig(
            strategy=CacheStrategy.WRITE_BEHIND,
            invalidation_strategy=InvalidationStrategy.TTL,
            ttl=300,
            write_interval=1,
            namespace="test"
        )
        cache_manager = CacheManager(config, "redis://dummy", mock_metrics)
        cache_manager.redis = mock_redis

        # Execute
        await cache_manager.set("key1", "value1")
        await cache_manager.set("key2", "value2")
        await asyncio.sleep(1.5)  # Wait for write-behind

        # Verify
        assert mock_redis.pipeline.called
        
        # Cleanup
        await cache_manager.close()

    @pytest.mark.asyncio
    async def test_invalidation_lru(self, invalidation_manager):
        # Setup
        old_entry = CacheEntry(
            key="old_key",
            value="old_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(seconds=300)).isoformat(),
            last_accessed=(datetime.now() - timedelta(seconds=400)).isoformat()
        )

        new_entry = CacheEntry(
            key="new_key",
            value="new_value",
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(seconds=300)).isoformat(),
            last_accessed=datetime.now().isoformat()
        )

        # Execute & Verify
        assert await invalidation_manager.should_invalidate(old_entry)
        assert not await invalidation_manager.should_invalidate(new_entry)

    @pytest.mark.asyncio
    async def test_cache_clear_namespace(self, cache_manager, mock_redis):
        # Setup
        mock_redis.scan.side_effect = [
            (1, ["test:key1", "test:key2"]),
            (0, ["test:key3"])
        ]

        # Execute
        result = await cache_manager.clear_namespace()

        # Verify
        assert result is True
        assert mock_redis.delete.call_count == 2
        mock_redis.delete.assert_any_call("test:key1", "test:key2")
        mock_redis.delete.assert_any_call("test:key3") 