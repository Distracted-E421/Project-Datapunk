import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch
import json
import asyncpg

from ..src.metadata.core import (
    AccessPattern, AccessPatternMetadata,
    DependencyType, Dependency, DependencyMetadata,
    PerformanceMetadata, PerformanceMetric,
    CacheMetadata, ResourceMetadata
)
from ..src.metadata.analyzer import MetadataAnalyzer
from ..src.metadata.cache import MetadataCache, CacheEntry

@pytest.fixture
def metadata_cache():
    """Create metadata cache instance."""
    return MetadataCache(max_size=100, default_ttl=60)

class TestAccessPatternMetadata:
    """Test cases for access pattern metadata."""
    
    @pytest.mark.asyncio
    async def test_access_pattern_analysis(self, metadata_analyzer):
        """Test analyzing access patterns."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock table access statistics
            mock_conn.fetchrow.side_effect = [
                {
                    'reads': 1000,
                    'writes': 100,
                    'updates': 50,
                    'deletes': 10
                },
                {
                    'seq_scan': 10,
                    'seq_tup_read': 1000,
                    'idx_scan': 100,
                    'idx_tup_read': 500
                }
            ]
            
            # Mock index usage statistics
            mock_conn.fetch.side_effect = [
                [
                    {
                        'index_name': 'test_idx',
                        'scan_count': 100,
                        'tuples_read': 500,
                        'tuples_fetched': 400
                    }
                ],
                [
                    {
                        'column_name': 'id',
                        'n_distinct': 1000,
                        'correlation': 0.9
                    }
                ]
            ]
            
            patterns = await metadata_analyzer._analyze_access_patterns("test_table")
            
            assert patterns.table_name == "test_table"
            assert patterns.total_reads == 1000
            assert patterns.total_writes == 160  # writes + updates + deletes
            assert len(patterns.patterns) == 2  # read and seek patterns
            assert len(patterns.hot_spots) == 1  # one column with high correlation

class TestDependencyMetadata:
    """Test cases for dependency metadata."""
    
    @pytest.mark.asyncio
    async def test_dependency_analysis(self, metadata_analyzer):
        """Test analyzing dependencies."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock foreign key dependencies
            mock_conn.fetch.side_effect = [
                [
                    {
                        'source_table': 'orders',
                        'target_table': 'customers',
                        'source_column': 'customer_id',
                        'target_column': 'id'
                    }
                ],
                [
                    {
                        'dependent_schema': 'public',
                        'dependent_view': 'order_summary',
                        'source_schema': 'public',
                        'source_table': 'orders'
                    }
                ]
            ]
            
            deps = await metadata_analyzer._analyze_dependencies("orders")
            
            assert deps.table_name == "orders"
            assert len(deps.upstream) == 1  # One foreign key dependency
            assert len(deps.downstream) == 1  # One view dependency
            assert deps.upstream[0].dependency_type == DependencyType.FOREIGN_KEY
            assert deps.downstream[0].dependency_type == DependencyType.VIEW

class TestPerformanceMetadata:
    """Test cases for performance metadata."""
    
    @pytest.mark.asyncio
    async def test_performance_analysis(self, metadata_analyzer):
        """Test analyzing performance metrics."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock basic performance metrics
            mock_conn.fetchrow.side_effect = [
                {
                    'table_size': 1024 * 1024,  # 1MB
                    'index_size': 512 * 1024,  # 512KB
                    'active_queries': 5
                }
            ]
            
            # Mock query performance metrics
            mock_conn.fetch.return_value = [
                {
                    'calls': 100,
                    'avg_exec_time': 50.0,
                    'shared_blks_hit': 1000,
                    'shared_blks_read': 100,
                    'shared_blks_written': 50,
                    'temp_blks_read': 10,
                    'temp_blks_written': 5
                }
            ]
            
            perf = await metadata_analyzer._analyze_performance("test_table")
            
            assert perf.table_name == "test_table"
            assert len(perf.metrics) == 1
            assert perf.avg_query_time_ms == 50.0
            assert len(perf.bottlenecks) == 0  # No bottlenecks detected

class TestCacheMetadata:
    """Test cases for cache metadata."""
    
    @pytest.mark.asyncio
    async def test_cache_analysis(self, metadata_analyzer):
        """Test analyzing cache behavior."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock buffer cache statistics
            mock_conn.fetchrow.return_value = {
                'heap_blks_read': 100,
                'heap_blks_hit': 900,
                'idx_blks_read': 50,
                'idx_blks_hit': 450
            }
            
            # Mock cached rows estimate
            mock_conn.fetchval.return_value = 1000
            
            cache_meta = await metadata_analyzer._analyze_cache("test_table")
            
            assert cache_meta.table_name == "test_table"
            assert cache_meta.hit_rate == 0.9  # (900 + 450) / (1000 + 500)
            assert cache_meta.miss_rate == 0.1
            assert cache_meta.cached_rows == 1000

class TestResourceMetadata:
    """Test cases for resource metadata."""
    
    @pytest.mark.asyncio
    async def test_resource_analysis(self, metadata_analyzer):
        """Test analyzing resource usage."""
        with patch('asyncpg.Connection') as mock_conn:
            # Mock resource statistics
            mock_conn.fetchrow.side_effect = [
                {
                    'total_size': 2 * 1024 * 1024,  # 2MB
                    'table_size': 1.5 * 1024 * 1024,  # 1.5MB
                    'index_size': 0.5 * 1024 * 1024,  # 0.5MB
                    'xid_age': 1000000
                },
                {
                    'last_vacuum': datetime.utcnow(),
                    'last_autovacuum': None,
                    'last_analyze': datetime.utcnow(),
                    'last_autoanalyze': None
                },
                {
                    'dead_tuple_ratio': 0.05,
                    'n_mod_since_analyze': 100
                },
                {
                    'connections': 5
                }
            ]
            
            resources = await metadata_analyzer._analyze_resource("test_table")
            
            assert resources.table_name == "test_table"
            assert resources.disk_usage_mb == 1.5
            assert resources.index_size_mb == 0.5
            assert resources.peak_connections == 5
            assert resources.bloat_ratio == 0.05

class TestMetadataCache:
    """Test cases for metadata caching."""
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, metadata_cache):
        """Test basic cache operations."""
        # Create test metadata
        schema = AccessPatternMetadata(
            table_name="test_table",
            patterns=[
                AccessPattern(
                    pattern_type="read",
                    frequency=100,
                    avg_latency_ms=10.0,
                    peak_latency_ms=50.0,
                    bytes_accessed=1024,
                    timestamp=datetime.utcnow(),
                    query_pattern=None,
                    index_used=None
                )
            ],
            last_updated=datetime.utcnow(),
            total_reads=1000,
            total_writes=100,
            hot_spots={},
            cold_spots={}
        )
        
        # Test set and get
        metadata_cache.set_access_patterns("test_table", schema)
        cached = metadata_cache.get_access_patterns("test_table")
        
        assert cached is not None
        assert cached.table_name == schema.table_name
        assert len(cached.patterns) == len(schema.patterns)
        
        # Test cache hit counting
        assert metadata_cache.hits == 1
        assert metadata_cache.misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, metadata_cache):
        """Test cache entry expiration."""
        schema = AccessPatternMetadata(
            table_name="test_table",
            patterns=[],
            last_updated=datetime.utcnow(),
            total_reads=0,
            total_writes=0,
            hot_spots={},
            cold_spots={}
        )
        
        # Set with short TTL
        metadata_cache.set_access_patterns("test_table", schema, ttl=1)
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        # Should be expired
        cached = metadata_cache.get_access_patterns("test_table")
        assert cached is None
        assert metadata_cache.misses == 1
        assert metadata_cache.evictions == 1
    
    @pytest.mark.asyncio
    async def test_cache_size_limit(self, metadata_cache):
        """Test cache size limiting."""
        # Set small cache size
        metadata_cache.max_size = 2
        
        # Add three entries
        base_schema = AccessPatternMetadata(
            table_name="test_table",
            patterns=[],
            last_updated=datetime.utcnow(),
            total_reads=0,
            total_writes=0,
            hot_spots={},
            cold_spots={}
        )
        
        for i in range(3):
            schema = base_schema.copy()
            schema.table_name = f"table_{i}"
            metadata_cache.set_access_patterns(schema.table_name, schema)
        
        # Should have evicted oldest entry
        assert len(metadata_cache.access_pattern_cache) == 2
        assert metadata_cache.evictions == 1
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self, metadata_cache):
        """Test background cache cleanup."""
        # Start cleanup task
        await metadata_cache.start()
        
        # Add entry with short TTL
        schema = AccessPatternMetadata(
            table_name="test_table",
            patterns=[],
            last_updated=datetime.utcnow(),
            total_reads=0,
            total_writes=0,
            hot_spots={},
            cold_spots={}
        )
        metadata_cache.set_access_patterns("test_table", schema, ttl=1)
        
        # Wait for cleanup
        await asyncio.sleep(2)
        
        # Should be cleaned up
        assert len(metadata_cache.access_pattern_cache) == 0
        
        # Stop cleanup task
        await metadata_cache.stop() 