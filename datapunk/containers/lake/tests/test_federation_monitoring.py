import pytest
import asyncio
from datetime import datetime, timedelta
from ..src.query.federation.monitoring import (
    FederationMonitor,
    QueryProfiler,
    QueryMetrics,
    SourceMetrics
)
from ..src.query.federation.core import QueryPlan

@pytest.fixture
def monitor():
    return FederationMonitor()

@pytest.fixture
def profiler():
    return QueryProfiler()

@pytest.fixture
def sample_query_plan():
    return QueryPlan(
        query_id="test_query",
        sources=["source1", "source2"],
        operations=[{"type": "join", "params": {}}]
    )

@pytest.mark.asyncio
async def test_monitor_query_lifecycle(monitor, sample_query_plan):
    """Test complete query monitoring lifecycle."""
    query_id = "test_query_1"
    
    # Start query
    await monitor.start_query(query_id, sample_query_plan)
    assert query_id in monitor.active_queries
    
    # Update metrics
    await monitor.update_query_metrics(query_id, {
        'cpu_usage': 50.0,
        'memory_usage': 100.0,
        'io_reads': 1000,
        'io_writes': 500,
        'network_sent': 5000,
        'network_received': 3000,
        'cache_hits': 100,
        'cache_misses': 20,
        'errors': 0,
        'source_metrics': {
            'source1': {'latency_ms': 50.0},
            'source2': {'latency_ms': 75.0}
        }
    })
    
    # Verify metrics update
    metrics = monitor.get_query_metrics(query_id)
    assert metrics.cpu_usage_percent == 50.0
    assert metrics.memory_usage_mb == 100.0
    assert metrics.io_reads == 1000
    assert metrics.cache_hits == 100
    
    # End query
    await monitor.end_query(query_id)
    assert query_id not in monitor.active_queries
    assert len(monitor.history) == 1

@pytest.mark.asyncio
async def test_source_metrics(monitor):
    """Test source metrics tracking."""
    source_id = "test_source"
    
    await monitor.update_source_metrics(source_id, {
        'avg_response_time': 100.0,
        'error_rate': 0.05,
        'throughput': 1000.0,
        'active_connections': 5,
        'cache_hit_ratio': 0.8,
        'resource_usage': {'cpu': 60.0, 'memory': 80.0}
    })
    
    metrics = monitor.get_source_metrics(source_id)
    assert isinstance(metrics, SourceMetrics)
    assert metrics.avg_response_time_ms == 100.0
    assert metrics.error_rate == 0.05
    assert metrics.throughput_qps == 1000.0
    assert metrics.cache_hit_ratio == 0.8

@pytest.mark.asyncio
async def test_performance_summary(monitor, sample_query_plan):
    """Test performance summary generation."""
    # Add some test data
    for i in range(5):
        query_id = f"test_query_{i}"
        await monitor.start_query(query_id, sample_query_plan)
        await monitor.update_query_metrics(query_id, {
            'cpu_usage': 50.0,
            'memory_usage': 100.0,
            'cache_hits': 10,
            'cache_misses': 2,
            'errors': i % 2  # Some queries with errors
        })
        await monitor.end_query(query_id)
    
    summary = monitor.get_performance_summary()
    assert 'avg_execution_time_ms' in summary
    assert 'error_rate' in summary
    assert 'cache_hit_ratio' in summary
    assert 'qps' in summary
    assert summary['error_rate'] == 0.4  # 2 out of 5 queries had errors

@pytest.mark.asyncio
async def test_source_health(monitor):
    """Test source health status monitoring."""
    # Add sources with different health states
    await monitor.update_source_metrics("healthy_source", {
        'error_rate': 0.001,
        'avg_response_time': 50.0
    })
    await monitor.update_source_metrics("degraded_source", {
        'error_rate': 0.05,
        'avg_response_time': 1500.0
    })
    await monitor.update_source_metrics("unhealthy_source", {
        'error_rate': 0.15,
        'avg_response_time': 2000.0
    })
    
    health = monitor.get_source_health()
    assert health["healthy_source"] == "healthy"
    assert health["degraded_source"] == "degraded"
    assert health["unhealthy_source"] == "unhealthy"

@pytest.mark.asyncio
async def test_query_profiler_lifecycle(profiler, sample_query_plan):
    """Test complete query profiling lifecycle."""
    query_id = "test_query_1"
    
    # Start profiling
    await profiler.start_profiling(query_id, sample_query_plan)
    
    # Profile stages
    await profiler.start_stage(query_id, "parse", "parsing")
    await asyncio.sleep(0.1)
    await profiler.update_stage_metrics(query_id, {'parsed_nodes': 100})
    await profiler.end_stage(query_id)
    
    await profiler.start_stage(query_id, "join", "join")
    await asyncio.sleep(0.1)
    await profiler.update_stage_metrics(query_id, {'rows_processed': 1500000})
    await profiler.end_stage(query_id)
    
    # End profiling
    await profiler.end_profiling(query_id)
    
    # Check profile
    profile = profiler.get_profile(query_id)
    assert len(profile['stages']) == 2
    assert profile['stages'][0]['type'] == "parsing"
    assert profile['stages'][1]['type'] == "join"
    
    # Check bottlenecks
    bottlenecks = profiler.get_bottlenecks(query_id)
    assert len(bottlenecks) > 0
    
    # Check optimization suggestions
    suggestions = profiler.get_optimization_suggestions(query_id)
    assert len(suggestions) > 0
    assert any(s['issue'] == 'Large join operation' for s in suggestions)

@pytest.mark.asyncio
async def test_historical_metrics(monitor, sample_query_plan):
    """Test historical metrics retrieval."""
    # Add queries at different times
    now = datetime.utcnow()
    
    # Old query (25 hours ago)
    old_query = "old_query"
    monitor.history.append(QueryMetrics(
        query_id=old_query,
        start_time=now - timedelta(hours=25),
        end_time=now - timedelta(hours=24),
        execution_time_ms=1000.0
    ))
    
    # Recent query (1 hour ago)
    recent_query = "recent_query"
    await monitor.start_query(recent_query, sample_query_plan)
    await monitor.end_query(recent_query)
    
    # Get historical metrics
    recent_metrics = monitor.get_historical_metrics(
        start_time=now - timedelta(hours=2)
    )
    assert len(recent_metrics) == 1
    assert recent_metrics[0].query_id == recent_query
    
    # Verify old query is trimmed
    monitor._trim_history()
    assert old_query not in [m.query_id for m in monitor.history]

@pytest.mark.asyncio
async def test_error_handling(monitor, profiler, sample_query_plan):
    """Test error handling in monitoring and profiling."""
    query_id = "error_test"
    
    # Test monitor error handling
    await monitor.start_query(query_id, sample_query_plan)
    await monitor.update_query_metrics(query_id, {'invalid': 'metric'})
    await monitor.end_query(query_id)
    
    # Test profiler error handling
    await profiler.start_profiling(query_id, sample_query_plan)
    await profiler.start_stage(query_id, "error_stage", "error")
    await profiler.update_stage_metrics(query_id, {'invalid': 'metric'})
    await profiler.end_stage(query_id)
    await profiler.end_profiling(query_id)
    
    # Verify system remains stable
    assert monitor.get_performance_summary() is not None
    assert profiler.get_profile(query_id) is not None 