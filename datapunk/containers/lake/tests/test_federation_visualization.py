import pytest
from datetime import datetime, timedelta
import plotly.graph_objects as go
from ..src.query.federation.fed_visualization import FederationVisualizer
from ..src.query.federation.query_fed_monitoring import (
    FederationMonitor,
    QueryMetrics,
    SourceMetrics
)
from ..src.query.federation.fed_alerting import (
    AlertManager,
    Alert,
    AlertSeverity,
    AlertType
)

@pytest.fixture
def monitor():
    return FederationMonitor()

@pytest.fixture
def alert_manager():
    return AlertManager()

@pytest.fixture
def visualizer(monitor, alert_manager):
    return FederationVisualizer(monitor, alert_manager)

@pytest.fixture
def sample_metrics():
    now = datetime.utcnow()
    metrics = []
    
    # Generate sample metrics over last 24 hours
    for i in range(24):
        metrics.append(QueryMetrics(
            query_id=f"query_{i}",
            start_time=now - timedelta(hours=24-i),
            end_time=now - timedelta(hours=23-i),
            execution_time_ms=100 + i * 10,
            cpu_usage_percent=50 + i,
            memory_usage_mb=200 + i * 5,
            io_reads=1000 + i * 100,
            io_writes=500 + i * 50,
            network_bytes_sent=5000 + i * 500,
            network_bytes_received=3000 + i * 300,
            cache_hits=100 + i * 10,
            cache_misses=20 + i * 2,
            error_count=i % 3,
            source_metrics={
                'source1': {'latency_ms': 50 + i},
                'source2': {'latency_ms': 75 + i}
            }
        ))
    
    return metrics

@pytest.fixture
def sample_source_metrics():
    return {
        'source1': SourceMetrics(
            source_id='source1',
            avg_response_time_ms=100.0,
            error_rate=0.01,
            throughput_qps=1000.0,
            active_connections=5,
            cache_hit_ratio=0.8,
            resource_usage={'cpu': 60.0, 'memory': 80.0}
        ),
        'source2': SourceMetrics(
            source_id='source2',
            avg_response_time_ms=150.0,
            error_rate=0.05,
            throughput_qps=800.0,
            active_connections=3,
            cache_hit_ratio=0.7,
            resource_usage={'cpu': 70.0, 'memory': 90.0}
        )
    }

def test_performance_dashboard(visualizer, monitor, sample_metrics):
    """Test performance dashboard creation."""
    # Add metrics to monitor
    monitor.history.extend(sample_metrics)
    
    # Generate dashboard
    dashboard = visualizer.create_performance_dashboard(hours=24)
    
    assert 'figures' in dashboard
    assert 'summary' in dashboard
    
    figures = dashboard['figures']
    assert 'execution_time' in figures
    assert 'resources' in figures
    assert 'cache' in figures
    assert 'errors' in figures
    
    # Verify figure types
    assert isinstance(figures['execution_time'], go.Figure)
    assert isinstance(figures['resources'], go.Figure)
    assert isinstance(figures['cache'], go.Figure)
    assert isinstance(figures['errors'], go.Figure)
    
    # Verify summary
    summary = dashboard['summary']
    assert 'total_queries' in summary
    assert 'avg_execution_time_ms' in summary
    assert 'total_errors' in summary
    assert summary['total_queries'] == len(sample_metrics)

def test_source_dashboard(visualizer, monitor, sample_source_metrics):
    """Test source dashboard creation."""
    # Add source metrics to monitor
    monitor.source_metrics = sample_source_metrics
    
    # Generate dashboard
    dashboard = visualizer.create_source_dashboard()
    
    assert 'figures' in dashboard
    assert 'summary' in dashboard
    
    figures = dashboard['figures']
    assert 'response_times' in figures
    assert 'error_rates' in figures
    assert 'throughput' in figures
    assert 'health' in figures
    
    # Verify figure types
    assert isinstance(figures['response_times'], go.Figure)
    assert isinstance(figures['error_rates'], go.Figure)
    assert isinstance(figures['throughput'], go.Figure)
    assert isinstance(figures['health'], go.Figure)
    
    # Verify summary
    summary = dashboard['summary']
    assert 'total_sources' in summary
    assert 'avg_response_time_ms' in summary
    assert 'total_throughput_qps' in summary
    assert summary['total_sources'] == len(sample_source_metrics)

def test_alert_dashboard(visualizer, alert_manager):
    """Test alert dashboard creation."""
    # Add sample alerts
    now = datetime.utcnow()
    alerts = []
    
    for i in range(5):
        alert = Alert(
            rule_name=f"rule_{i}",
            severity=AlertSeverity.WARNING if i % 2 else AlertSeverity.ERROR,
            alert_type=AlertType.PERFORMANCE if i % 2 else AlertType.ERROR,
            message=f"Test alert {i}",
            timestamp=now - timedelta(hours=i),
            context={},
            resolved=i < 3,
            resolved_at=now if i < 3 else None
        )
        alerts.append(alert)
    
    alert_manager.alert_history.extend(alerts)
    
    # Generate dashboard
    dashboard = visualizer.create_alert_dashboard(hours=24)
    
    assert 'figures' in dashboard
    assert 'summary' in dashboard
    
    figures = dashboard['figures']
    assert 'severity' in figures
    assert 'type' in figures
    
    # Verify figure types
    assert isinstance(figures['severity'], go.Figure)
    assert isinstance(figures['type'], go.Figure)
    
    # Verify summary
    summary = dashboard['summary']
    assert 'total_alerts' in summary
    assert 'alerts_by_severity' in summary
    assert 'alerts_by_type' in summary
    assert summary['total_alerts'] == len(alerts)

def test_error_handling(visualizer):
    """Test visualization error handling."""
    # Test with no data
    perf_dashboard = visualizer.create_performance_dashboard()
    assert 'error' in perf_dashboard
    
    source_dashboard = visualizer.create_source_dashboard()
    assert 'error' in source_dashboard
    
    alert_dashboard = visualizer.create_alert_dashboard()
    assert 'error' in alert_dashboard

def test_summary_calculations(visualizer, monitor, sample_metrics):
    """Test summary statistics calculations."""
    # Add metrics to monitor
    monitor.history.extend(sample_metrics)
    
    # Get performance summary
    dashboard = visualizer.create_performance_dashboard()
    summary = dashboard['summary']
    
    # Verify calculations
    assert summary['total_queries'] == len(sample_metrics)
    assert summary['avg_execution_time_ms'] > 0
    assert summary['p95_execution_time_ms'] > 0
    assert summary['total_errors'] == sum(m.error_count for m in sample_metrics)
    assert summary['avg_cpu_usage'] > 0
    assert summary['avg_memory_usage_mb'] > 0
    assert summary['total_cache_hits'] > 0
    assert summary['total_cache_misses'] > 0

def test_visualization_updates(visualizer, monitor, alert_manager):
    """Test visualization updates with changing data."""
    # Add initial metrics
    initial_metrics = [
        QueryMetrics(
            query_id="query_1",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=1),
            execution_time_ms=100,
            cpu_usage_percent=50,
            memory_usage_mb=200,
            cache_hits=100,
            cache_misses=20,
            error_count=0
        )
    ]
    monitor.history.extend(initial_metrics)
    
    # Get initial dashboard
    initial_dashboard = visualizer.create_performance_dashboard()
    initial_summary = initial_dashboard['summary']
    
    # Add more metrics
    additional_metrics = [
        QueryMetrics(
            query_id="query_2",
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=2),
            execution_time_ms=200,
            cpu_usage_percent=60,
            memory_usage_mb=300,
            cache_hits=150,
            cache_misses=30,
            error_count=1
        )
    ]
    monitor.history.extend(additional_metrics)
    
    # Get updated dashboard
    updated_dashboard = visualizer.create_performance_dashboard()
    updated_summary = updated_dashboard['summary']
    
    # Verify updates
    assert updated_summary['total_queries'] > initial_summary['total_queries']
    assert updated_summary['total_errors'] > initial_summary['total_errors']
    assert updated_summary['total_cache_hits'] > initial_summary['total_cache_hits'] 