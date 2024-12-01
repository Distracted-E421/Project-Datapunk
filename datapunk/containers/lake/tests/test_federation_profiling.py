import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import MagicMock, patch
import time
from ..src.query.federation.profiling import (
    OperationProfile,
    ProfileCollector,
    DetailedProfiler,
    QueryAnalyzer,
    PerformancePredictor
)

@pytest.fixture
def profile_collector():
    """Create profile collector instance."""
    return ProfileCollector()

@pytest.fixture
def detailed_profiler():
    """Create detailed profiler instance."""
    return DetailedProfiler()

@pytest.fixture
def query_analyzer():
    """Create query analyzer instance."""
    return QueryAnalyzer()

@pytest.fixture
def performance_predictor():
    """Create performance predictor instance."""
    return PerformancePredictor()

class TestProfileCollector:
    """Test cases for profile collection."""
    
    def test_operation_lifecycle(self, profile_collector):
        """Test complete operation lifecycle."""
        query_id = "test_query_1"
        operation_type = "test_operation"
        
        # Start operation
        operation_id = profile_collector.start_operation(
            query_id,
            operation_type,
            {'param': 'value'}
        )
        
        assert operation_id is not None
        
        # Add metrics and end operation
        metrics = {
            'cpu_time_ms': 100.0,
            'memory_usage_mb': 50.0,
            'io_operations': 10
        }
        profile_collector.end_operation(query_id, operation_id, metrics)
        
        # Verify profile
        profile = profile_collector.get_profile(query_id)
        assert len(profile) > 0
        assert profile[0].operation_type == operation_type
        assert profile[0].cpu_time_ms == 100.0
        
    def test_nested_operations(self, profile_collector):
        """Test nested operation tracking."""
        query_id = "test_query_2"
        
        # Start parent operation
        parent_id = profile_collector.start_operation(
            query_id,
            "parent_op"
        )
        
        # Start child operation
        child_id = profile_collector.start_operation(
            query_id,
            "child_op"
        )
        
        # End operations
        profile_collector.end_operation(query_id, child_id)
        profile_collector.end_operation(query_id, parent_id)
        
        # Verify profile
        profile = profile_collector.get_profile(query_id)
        assert len(profile) == 2
        assert any(p.operation_type == "parent_op" for p in profile)
        assert any(p.operation_type == "child_op" for p in profile)

class TestDetailedProfiler:
    """Test cases for detailed profiling."""
    
    def test_operation_profiling(self, detailed_profiler):
        """Test detailed operation profiling."""
        query_id = "test_query_3"
        
        with detailed_profiler.profile_operation(
            query_id,
            "test_operation",
            {'param': 'value'}
        ):
            # Simulate work
            time.sleep(0.1)
            large_list = [0] * 100000
            del large_list
            
        # Verify profile
        profile = detailed_profiler.collector.get_profile(query_id)
        assert len(profile) > 0
        assert profile[0].operation_type == "test_operation"
        assert profile[0].cpu_time_ms > 0
        assert profile[0].memory_usage_mb > 0
        
    def test_error_handling(self, detailed_profiler):
        """Test error handling in profiling."""
        query_id = "test_query_4"
        
        try:
            with detailed_profiler.profile_operation(
                query_id,
                "error_operation"
            ):
                raise ValueError("Test error")
        except ValueError:
            pass
            
        # Verify profile was completed
        profile = detailed_profiler.collector.get_profile(query_id)
        assert len(profile) > 0
        assert profile[0].operation_type == "error_operation"
        assert profile[0].end_time is not None

class TestQueryAnalyzer:
    """Test cases for query analysis."""
    
    @pytest.fixture
    def sample_profile(self):
        """Create sample operation profile."""
        return [
            OperationProfile(
                operation_id="op1",
                operation_type="select",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=1),
                cpu_time_ms=500.0,
                memory_usage_mb=100.0,
                io_operations=5
            ),
            OperationProfile(
                operation_id="op2",
                operation_type="join",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=2),
                cpu_time_ms=1000.0,
                memory_usage_mb=200.0,
                io_operations=10
            )
        ]
        
    def test_pattern_analysis(self, query_analyzer, sample_profile):
        """Test execution pattern analysis."""
        query_id = "test_query_5"
        query_analyzer.add_profile(query_id, sample_profile)
        
        analysis = query_analyzer.analyze_patterns()
        
        assert 'operation_stats' in analysis
        assert 'bottlenecks' in analysis
        assert 'recommendations' in analysis
        
        # Verify operation stats
        stats = analysis['operation_stats']
        assert 'select' in stats
        assert 'join' in stats
        assert stats['join']['avg_duration'] > stats['select']['avg_duration']
        
    def test_bottleneck_identification(self, query_analyzer, sample_profile):
        """Test bottleneck identification."""
        # Add profile with slow operation
        slow_profile = [
            OperationProfile(
                operation_id="op3",
                operation_type="aggregate",
                start_time=datetime.now(),
                end_time=datetime.now() + timedelta(seconds=5),
                cpu_time_ms=4000.0,
                memory_usage_mb=800.0,
                io_operations=20
            )
        ]
        
        query_analyzer.add_profile("test_query_6", slow_profile)
        analysis = query_analyzer.analyze_patterns()
        
        bottlenecks = analysis['bottlenecks']
        assert len(bottlenecks) > 0
        assert any(
            b['type'] == 'slow_operation' and
            b['operation'] == 'aggregate'
            for b in bottlenecks
        )
        
    def test_recommendations(self, query_analyzer, sample_profile):
        """Test recommendation generation."""
        query_analyzer.add_profile("test_query_7", sample_profile)
        analysis = query_analyzer.analyze_patterns()
        
        recommendations = analysis['recommendations']
        assert isinstance(recommendations, list)
        assert all(
            'target' in r and 'issue' in r and 'recommendation' in r
            for r in recommendations
        )

class TestPerformancePredictor:
    """Test cases for performance prediction."""
    
    @pytest.fixture
    def sample_metrics(self):
        """Create sample metrics data."""
        return {
            'execution_time_ms': 1000,
            'memory_usage_mb': 100,
            'cpu_time_ms': 800,
            'io_operations': 50
        }
        
    def test_prediction(self, performance_predictor, sample_metrics):
        """Test performance prediction."""
        query_type = "select_query"
        
        # Add historical data
        for _ in range(3):
            performance_predictor.add_execution(query_type, sample_metrics)
            
        # Make prediction
        prediction = performance_predictor.predict_performance(
            query_type,
            {'table': 'users'}
        )
        
        assert 'expected_duration_ms' in prediction
        assert 'expected_memory_mb' in prediction
        assert prediction['expected_duration_ms'] == 1000
        assert prediction['expected_memory_mb'] == 100
        
    def test_no_history_prediction(self, performance_predictor):
        """Test prediction with no historical data."""
        prediction = performance_predictor.predict_performance(
            "unknown_query",
            {}
        )
        
        assert prediction == {} 