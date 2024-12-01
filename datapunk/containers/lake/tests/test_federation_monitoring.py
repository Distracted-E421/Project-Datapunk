import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from ..src.query.federation.monitoring import (
    QueryMetrics,
    MetricsCollector,
    PerformanceMonitor,
    ResourceMonitor,
    QueryProfiler
)

class TestMetricsCollector:
    """Test cases for metrics collection."""
    
    @pytest.fixture
    def collector(self):
        """Create metrics collector instance."""
        return MetricsCollector()
        
    def test_query_lifecycle(self, collector):
        """Test complete query lifecycle tracking."""
        # Start query
        query_id = "test_query_1"
        metrics = collector.start_query(query_id)
        
        assert metrics.query_id == query_id
        assert metrics.start_time is not None
        assert metrics.end_time is None
        
        # Add source metrics
        source_metrics = {'execution_time_ms': 100.0}
        collector.add_source_metrics(query_id, 'source1', source_metrics)
        
        # Add merge metrics
        merge_metrics = {'merge_time_ms': 50.0}
        collector.add_merge_metrics(query_id, merge_metrics)
        
        # End query
        collector.end_query(query_id)
        
        # Verify final metrics
        final_metrics = collector.get_metrics(query_id)
        assert final_metrics.end_time is not None
        assert final_metrics.source_metrics['source1'] == source_metrics
        assert final_metrics.merge_metrics == merge_metrics
        
    def test_error_tracking(self, collector):
        """Test error tracking in metrics."""
        query_id = "test_query_2"
        collector.start_query(query_id)
        
        # Add error
        error_msg = "Test error message"
        collector.add_error(query_id, error_msg)
        
        # Verify error
        metrics = collector.get_metrics(query_id)
        assert len(metrics.errors) == 1
        assert metrics.errors[0] == error_msg
        
    def test_multiple_queries(self, collector):
        """Test tracking multiple queries."""
        # Start multiple queries
        query_ids = ["query1", "query2", "query3"]
        for qid in query_ids:
            collector.start_query(qid)
            
        # Add metrics to each
        for qid in query_ids:
            collector.add_source_metrics(qid, 'source1', {'time': 100.0})
            collector.end_query(qid)
            
        # Verify all metrics
        all_metrics = collector.get_all_metrics()
        assert len(all_metrics) == 3
        assert all(qid in all_metrics for qid in query_ids)

class TestPerformanceMonitor:
    """Test cases for performance monitoring."""
    
    @pytest.fixture
    def monitor(self):
        """Create performance monitor instance."""
        return PerformanceMonitor()
        
    def test_query_monitoring(self, monitor):
        """Test query performance monitoring."""
        query_id = "test_query_3"
        
        with monitor.monitor_query(query_id) as metrics:
            # Simulate work
            time.sleep(0.1)
            metrics.total_rows = 100
            
        # Verify metrics
        final_metrics = monitor.collector.get_metrics(query_id)
        assert final_metrics.execution_time_ms >= 100  # At least 100ms
        assert final_metrics.total_rows == 100
        
    def test_source_monitoring(self, monitor):
        """Test data source monitoring."""
        query_id = "test_query_4"
        
        with monitor.monitor_query(query_id):
            with monitor.monitor_source(query_id, 'source1'):
                # Simulate source operation
                time.sleep(0.1)
                
        # Verify source metrics
        metrics = monitor.collector.get_metrics(query_id)
        assert 'source1' in metrics.source_metrics
        assert metrics.source_metrics['source1']['execution_time_ms'] >= 100
        
    def test_merge_monitoring(self, monitor):
        """Test merge operation monitoring."""
        query_id = "test_query_5"
        
        with monitor.monitor_query(query_id):
            with monitor.monitor_merge(query_id):
                # Simulate merge operation
                time.sleep(0.1)
                
        # Verify merge metrics
        metrics = monitor.collector.get_metrics(query_id)
        assert metrics.merge_metrics is not None
        assert metrics.merge_metrics['merge_time_ms'] >= 100

class TestResourceMonitor:
    """Test cases for resource monitoring."""
    
    @pytest.fixture
    def monitor(self):
        """Create resource monitor instance."""
        return ResourceMonitor()
        
    def test_resource_tracking(self, monitor):
        """Test resource usage tracking."""
        # Start monitoring
        monitor.start_monitoring()
        initial_usage = monitor.start_usage.copy()
        
        # Simulate memory usage
        large_list = [0] * 1000000  # Allocate memory
        
        # Update usage
        current_usage = monitor.update_usage()
        assert current_usage['memory'] > 0
        assert current_usage['cpu'] >= 0
        
        # Check delta
        delta = monitor.get_delta()
        assert delta['memory'] >= 0  # Memory should increase
        assert isinstance(delta['cpu'], float)
        
        # Cleanup
        del large_list

class TestQueryProfiler:
    """Test cases for query profiling."""
    
    @pytest.fixture
    def profiler(self):
        """Create query profiler instance."""
        return QueryProfiler()
        
    def test_operation_profiling(self, profiler):
        """Test operation profiling."""
        query_id = "test_query_6"
        
        # Start operation
        profiler.start_operation(
            query_id,
            'test_op',
            {'type': 'select'}
        )
        
        # Simulate work
        time.sleep(0.1)
        
        # End operation
        profiler.end_operation(query_id, 'test_op')
        
        # Verify profile
        profile = profiler.get_profile(query_id)
        assert len(profile) == 1
        assert profile[0]['operation'] == 'test_op'
        assert profile[0]['duration_ms'] >= 100
        
    def test_nested_operations(self, profiler):
        """Test profiling nested operations."""
        query_id = "test_query_7"
        
        # Start outer operation
        profiler.start_operation(
            query_id,
            'outer',
            {'type': 'join'}
        )
        
        # Start inner operation
        profiler.start_operation(
            query_id,
            'inner',
            {'type': 'select'}
        )
        
        # End operations
        profiler.end_operation(query_id, 'inner')
        profiler.end_operation(query_id, 'outer')
        
        # Verify profile
        profile = profiler.get_profile(query_id)
        assert len(profile) == 2
        assert profile[0]['operation'] == 'outer'
        assert profile[1]['operation'] == 'inner'
        
    def test_multiple_queries_profiling(self, profiler):
        """Test profiling multiple queries."""
        query_ids = ["query8", "query9"]
        
        for qid in query_ids:
            profiler.start_operation(qid, 'op1', {})
            profiler.end_operation(qid, 'op1')
            
        # Verify profiles
        for qid in query_ids:
            profile = profiler.get_profile(qid)
            assert len(profile) == 1
            assert profile[0]['operation'] == 'op1' 