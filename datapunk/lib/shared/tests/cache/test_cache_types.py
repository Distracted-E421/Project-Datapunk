import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from datapunk_shared.cache.cache_types import (
    CacheStrategy,
    InvalidationStrategy,
    CacheConfig,
    CacheEntry
)

class TestCacheStrategy:
    def test_cache_strategy_values(self):
        """Test cache strategy enum values."""
        assert CacheStrategy.WRITE_THROUGH.value == "write_through"
        assert CacheStrategy.WRITE_BEHIND.value == "write_behind"
        assert CacheStrategy.WRITE_AROUND.value == "write_around"
        assert CacheStrategy.READ_THROUGH.value == "read_through"
        assert CacheStrategy.CACHE_ASIDE.value == "cache_aside"

class TestInvalidationStrategy:
    def test_invalidation_strategy_values(self):
        """Test invalidation strategy enum values."""
        assert InvalidationStrategy.TTL.value == "ttl"
        assert InvalidationStrategy.LRU.value == "lru"
        assert InvalidationStrategy.LFU.value == "lfu"
        assert InvalidationStrategy.FIFO.value == "fifo"

class TestCacheConfig:
    @pytest.fixture
    def default_config(self):
        """Create default cache configuration."""
        return CacheConfig(
            strategy=CacheStrategy.WRITE_THROUGH,
            invalidation_strategy=InvalidationStrategy.TTL
        )

    @pytest.fixture
    def custom_config(self):
        """Create custom cache configuration."""
        return CacheConfig(
            strategy=CacheStrategy.WRITE_BEHIND,
            invalidation_strategy=InvalidationStrategy.LRU,
            ttl=7200,
            max_size=1000,
            write_buffer_size=100,
            write_interval=60,
            compression=True,
            namespace="custom"
        )

    def test_default_config_values(self, default_config):
        """Test default configuration values."""
        assert default_config.strategy == CacheStrategy.WRITE_THROUGH
        assert default_config.invalidation_strategy == InvalidationStrategy.TTL
        assert default_config.ttl == 3600
        assert default_config.max_size is None
        assert default_config.write_buffer_size is None
        assert default_config.write_interval is None
        assert default_config.compression is False
        assert default_config.namespace == "default"

    def test_custom_config_values(self, custom_config):
        """Test custom configuration values."""
        assert custom_config.strategy == CacheStrategy.WRITE_BEHIND
        assert custom_config.invalidation_strategy == InvalidationStrategy.LRU
        assert custom_config.ttl == 7200
        assert custom_config.max_size == 1000
        assert custom_config.write_buffer_size == 100
        assert custom_config.write_interval == 60
        assert custom_config.compression is True
        assert custom_config.namespace == "custom"

class TestCacheEntry:
    @pytest.fixture
    def current_time(self):
        """Get current time for testing."""
        return datetime.utcnow()

    @pytest.fixture
    def basic_entry(self, current_time):
        """Create basic cache entry."""
        return CacheEntry(
            key="test_key",
            value="test_value",
            created_at=current_time,
            expires_at=current_time + timedelta(hours=1)
        )

    @pytest.fixture
    def complex_entry(self, current_time):
        """Create complex cache entry with all fields."""
        return CacheEntry(
            key="complex_key",
            value={"nested": "data"},
            created_at=current_time,
            expires_at=current_time + timedelta(hours=2),
            access_count=5,
            last_accessed=current_time - timedelta(minutes=30),
            version=2,
            metadata={
                "source": "test",
                "checksum": "abc123",
                "compression_type": "zlib",
                "priority": 1
            }
        )

    def test_basic_entry_creation(self, basic_entry, current_time):
        """Test basic cache entry creation."""
        assert basic_entry.key == "test_key"
        assert basic_entry.value == "test_value"
        assert basic_entry.created_at == current_time
        assert basic_entry.expires_at == current_time + timedelta(hours=1)
        assert basic_entry.access_count == 0
        assert basic_entry.last_accessed is None
        assert basic_entry.version == 1
        assert basic_entry.metadata is None

    def test_complex_entry_creation(self, complex_entry, current_time):
        """Test complex cache entry creation with all fields."""
        assert complex_entry.key == "complex_key"
        assert complex_entry.value == {"nested": "data"}
        assert complex_entry.created_at == current_time
        assert complex_entry.expires_at == current_time + timedelta(hours=2)
        assert complex_entry.access_count == 5
        assert complex_entry.last_accessed == current_time - timedelta(minutes=30)
        assert complex_entry.version == 2
        assert complex_entry.metadata["source"] == "test"
        assert complex_entry.metadata["checksum"] == "abc123"
        assert complex_entry.metadata["compression_type"] == "zlib"
        assert complex_entry.metadata["priority"] == 1

    def test_entry_with_no_expiration(self, current_time):
        """Test cache entry creation without expiration."""
        entry = CacheEntry(
            key="no_expiry",
            value="test",
            created_at=current_time,
            expires_at=None
        )
        assert entry.expires_at is None

    def test_entry_with_custom_metadata(self, current_time):
        """Test cache entry with custom metadata fields."""
        custom_metadata: Dict[str, Any] = {
            "custom_field": "value",
            "numeric_field": 123,
            "nested": {
                "field": "value"
            }
        }
        entry = CacheEntry(
            key="metadata_test",
            value="test",
            created_at=current_time,
            expires_at=None,
            metadata=custom_metadata
        )
        assert entry.metadata == custom_metadata
        assert entry.metadata["custom_field"] == "value"
        assert entry.metadata["numeric_field"] == 123
        assert entry.metadata["nested"]["field"] == "value" 