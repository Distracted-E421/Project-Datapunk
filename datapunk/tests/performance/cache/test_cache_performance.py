"""Performance testing suite for distributed cache system
Validates cache performance metrics against infrastructure requirements
defined in sys-arch.mmd and project_status.md
"""

import pytest
import asyncio
import time
import random
import string
from typing import List, Dict
import statistics
import aioredis
from datapunk_shared.cache.cache_types import (
    CacheConfig, CacheStrategy, InvalidationStrategy
)
from datapunk_shared.cache.cache_manager import CacheManager
from datapunk_shared.cache.cluster_manager import ClusterNode
from datapunk_shared.cache.cache_features import CacheFeatureManager

class PerformanceMetrics:
    """Tracks and analyzes cache performance metrics
    
    Collects operation timings, error rates, and resource utilization
    for performance analysis and optimization.
    
    TODO: Add metrics for:
    - Memory pressure analysis
    - Network latency impact
    - Cluster rebalancing overhead
    - Cache eviction performance
    - Write-through vs write-behind comparison
    
    FIXME: Improve accuracy of timing measurements under load
    NOTE: Consider implementing histogram metrics for better distribution analysis
    """
    
    def __init__(self):
        self.operations: List[float] = []  # Operation timing history
        self.errors: int = 0  # Error counter for reliability analysis
        self.start_time: float = 0  # Test start timestamp
        self.end_time: float = 0  # Test end timestamp

    @property
    def total_time(self) -> float:
        """Total test duration in seconds
        Used for throughput calculations and performance trending
        """
        return self.end_time - self.start_time

    @property
    def ops_per_second(self) -> float:
        return len(self.operations) / self.total_time

    @property
    def avg_latency(self) -> float:
        return statistics.mean(self.operations) if self.operations else 0

    @property
    def p95_latency(self) -> float:
        return statistics.quantiles(self.operations, n=20)[18] if self.operations else 0

    def report(self) -> Dict[str, float]:
        return {
            'total_operations': len(self.operations),
            'total_errors': self.errors,
            'total_time_seconds': self.total_time,
            'operations_per_second': self.ops_per_second,
            'average_latency_ms': self.avg_latency * 1000,
            'p95_latency_ms': self.p95_latency * 1000
        }

@pytest.fixture
async def benchmark_cache():
    """Setup cache manager for benchmarking"""
    config = CacheConfig(
        strategy=CacheStrategy.WRITE_THROUGH,
        invalidation_strategy=InvalidationStrategy.TTL,
        ttl=300,
        namespace="benchmark"
    )
    
    manager = CacheManager(
        config=config,
        redis_url="redis://localhost:6379"
    )
    
    yield manager
    await manager.stop()

@pytest.fixture
def random_data(size: int = 1000) -> str:
    """Generate random data of specified size"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=size))

class TestCachePerformance:
    @pytest.mark.asyncio
    async def test_write_performance(self, benchmark_cache, random_data):
        """Benchmark write performance"""
        metrics = PerformanceMetrics()
        operations = 10000
        
        metrics.start_time = time.time()
        
        for i in range(operations):
            try:
                start = time.time()
                await benchmark_cache.set(f"key_{i}", random_data)
                metrics.operations.append(time.time() - start)
            except Exception:
                metrics.errors += 1
        
        metrics.end_time = time.time()
        
        # Report results
        results = metrics.report()
        print("\nWrite Performance Results:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        # Assertions
        assert results['operations_per_second'] > 1000  # At least 1K ops/sec
        assert results['p95_latency_ms'] < 10  # P95 latency under 10ms

    @pytest.mark.asyncio
    async def test_read_performance(self, benchmark_cache, random_data):
        """Benchmark read performance"""
        # Setup: Write test data
        key = "test_key"
        await benchmark_cache.set(key, random_data)
        
        metrics = PerformanceMetrics()
        operations = 100000
        
        metrics.start_time = time.time()
        
        for _ in range(operations):
            try:
                start = time.time()
                await benchmark_cache.get(key)
                metrics.operations.append(time.time() - start)
            except Exception:
                metrics.errors += 1
        
        metrics.end_time = time.time()
        
        # Report results
        results = metrics.report()
        print("\nRead Performance Results:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        # Assertions
        assert results['operations_per_second'] > 5000  # At least 5K ops/sec
        assert results['p95_latency_ms'] < 5  # P95 latency under 5ms

    @pytest.mark.asyncio
    async def test_concurrent_performance(self, benchmark_cache, random_data):
        """Benchmark concurrent operations performance"""
        metrics = PerformanceMetrics()
        operations_per_worker = 1000
        num_workers = 10
        
        async def worker(worker_id: int):
            for i in range(operations_per_worker):
                try:
                    start = time.time()
                    key = f"worker_{worker_id}_key_{i}"
                    await benchmark_cache.set(key, random_data)
                    await benchmark_cache.get(key)
                    metrics.operations.append(time.time() - start)
                except Exception:
                    metrics.errors += 1

        metrics.start_time = time.time()
        
        # Run workers concurrently
        workers = [worker(i) for i in range(num_workers)]
        await asyncio.gather(*workers)
        
        metrics.end_time = time.time()
        
        # Report results
        results = metrics.report()
        print("\nConcurrent Operations Results:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        # Assertions
        assert results['operations_per_second'] > 2000  # At least 2K ops/sec
        assert results['p95_latency_ms'] < 15  # P95 latency under 15ms

    @pytest.mark.asyncio
    async def test_feature_performance(self, benchmark_cache, random_data):
        """Benchmark compression and encryption performance"""
        feature_manager = CacheFeatureManager(
            compression_enabled=True,
            encryption_enabled=True,
            encryption_key="test_key_123"
        )
        
        metrics = PerformanceMetrics()
        operations = 1000
        
        metrics.start_time = time.time()
        
        for i in range(operations):
            try:
                start = time.time()
                processed = await feature_manager.process_for_cache(random_data)
                await benchmark_cache.set(f"key_{i}", processed)
                cached = await benchmark_cache.get(f"key_{i}")
                recovered = await feature_manager.process_from_cache(cached)
                assert recovered == random_data
                metrics.operations.append(time.time() - start)
            except Exception:
                metrics.errors += 1
        
        metrics.end_time = time.time()
        
        # Report results
        results = metrics.report()
        print("\nFeature Performance Results:")
        for key, value in results.items():
            print(f"{key}: {value}")
        
        # Assertions
        assert results['operations_per_second'] > 100  # At least 100 ops/sec
        assert results['p95_latency_ms'] < 50  # P95 latency under 50ms 