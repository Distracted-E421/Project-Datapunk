import pytest
from unittest.mock import patch, MagicMock
from prometheus_client import REGISTRY
from datapunk.lib.metrics import MetricsCollector

@pytest.fixture
def metrics_collector():
    return MetricsCollector("test-service")

def test_metrics_collector_initialization(metrics_collector):
    """Test metrics collector initialization and metric creation"""
    # Verify all required metrics were created
    assert 'requests_total' in REGISTRY._names_to_collectors
    assert 'request_duration_seconds' in REGISTRY._names_to_collectors
    assert 'resource_usage' in REGISTRY._names_to_collectors
    assert 'operations_total' in REGISTRY._names_to_collectors
    
    # Verify service name was set
    assert metrics_collector.service_name == "test-service"

def test_track_request(metrics_collector):
    """Test request tracking with counts and duration"""
    # Track a test request
    metrics_collector.track_request(
        endpoint="/api/test",
        method="GET",
        status=200,
        duration=0.5
    )
    
    # Verify request counter
    counter = REGISTRY.get_sample_value(
        'requests_total',
        {
            'service': 'test-service',
            'endpoint': '/api/test',
            'method': 'GET',
            'status': '200'
        }
    )
    assert counter == 1.0
    
    # Verify duration histogram
    histogram_count = REGISTRY.get_sample_value(
        'request_duration_seconds_count',
        {
            'service': 'test-service',
            'endpoint': '/api/test'
        }
    )
    assert histogram_count == 1.0
    
    # Verify duration was recorded in appropriate bucket
    histogram_bucket = REGISTRY.get_sample_value(
        'request_duration_seconds_bucket',
        {
            'service': 'test-service',
            'endpoint': '/api/test',
            'le': '1.0'
        }
    )
    assert histogram_bucket == 1.0

def test_track_multiple_requests(metrics_collector):
    """Test tracking multiple requests with different parameters"""
    # Track multiple requests
    requests = [
        ("/api/test", "GET", 200, 0.1),
        ("/api/test", "POST", 201, 0.3),
        ("/api/test", "GET", 404, 0.2),
        ("/api/other", "GET", 200, 0.4)
    ]
    
    for endpoint, method, status, duration in requests:
        metrics_collector.track_request(endpoint, method, status, duration)
    
    # Verify request counts
    get_200_count = REGISTRY.get_sample_value(
        'requests_total',
        {
            'service': 'test-service',
            'endpoint': '/api/test',
            'method': 'GET',
            'status': '200'
        }
    )
    assert get_200_count == 1.0
    
    post_201_count = REGISTRY.get_sample_value(
        'requests_total',
        {
            'service': 'test-service',
            'endpoint': '/api/test',
            'method': 'POST',
            'status': '201'
        }
    )
    assert post_201_count == 1.0

def test_track_operation(metrics_collector):
    """Test business operation tracking"""
    # Track some operations
    metrics_collector.track_operation("data_processing", "success")
    metrics_collector.track_operation("data_processing", "failure")
    metrics_collector.track_operation("user_authentication", "success")
    
    # Verify operation counts
    success_count = REGISTRY.get_sample_value(
        'operations_total',
        {
            'service': 'test-service',
            'operation_type': 'data_processing',
            'status': 'success'
        }
    )
    assert success_count == 1.0
    
    failure_count = REGISTRY.get_sample_value(
        'operations_total',
        {
            'service': 'test-service',
            'operation_type': 'data_processing',
            'status': 'failure'
        }
    )
    assert failure_count == 1.0

def test_update_resource_usage(metrics_collector):
    """Test resource usage metrics updates"""
    # Update resource metrics
    metrics = {
        'cpu_percent': 45.2,
        'memory_percent': 60.5,
        'disk_percent': 75.8
    }
    
    metrics_collector.update_resource_usage(metrics)
    
    # Verify resource metrics
    for resource_type, expected_value in metrics.items():
        value = REGISTRY.get_sample_value(
            'resource_usage',
            {
                'service': 'test-service',
                'resource_type': resource_type
            }
        )
        assert value == expected_value

def test_request_duration_buckets(metrics_collector):
    """Test request duration histogram buckets"""
    durations = [0.05, 0.3, 0.8, 1.5, 6.0]  # Test various duration ranges
    
    for duration in durations:
        metrics_collector.track_request(
            endpoint="/api/test",
            method="GET",
            status=200,
            duration=duration
        )
    
    # Verify histogram buckets
    buckets = [0.1, 0.5, 1.0, 2.0, 5.0]
    for bucket in buckets:
        count = REGISTRY.get_sample_value(
            'request_duration_seconds_bucket',
            {
                'service': 'test-service',
                'endpoint': '/api/test',
                'le': str(bucket)
            }
        )
        # Count how many durations are less than or equal to this bucket
        expected_count = len([d for d in durations if d <= bucket])
        assert count == expected_count

def test_track_request_with_errors(metrics_collector):
    """Test request tracking with error status codes"""
    error_requests = [
        ("/api/test", "GET", 400, 0.1),
        ("/api/test", "POST", 500, 0.2),
        ("/api/test", "GET", 403, 0.1)
    ]
    
    for endpoint, method, status, duration in error_requests:
        metrics_collector.track_request(endpoint, method, status, duration)
    
    # Verify error request counts
    for endpoint, method, status, _ in error_requests:
        count = REGISTRY.get_sample_value(
            'requests_total',
            {
                'service': 'test-service',
                'endpoint': endpoint,
                'method': method,
                'status': str(status)
            }
        )
        assert count == 1.0

def test_resource_usage_updates(metrics_collector):
    """Test multiple resource usage updates"""
    # Initial update
    initial_metrics = {
        'cpu_percent': 30.0,
        'memory_percent': 50.0
    }
    metrics_collector.update_resource_usage(initial_metrics)
    
    # Verify initial values
    for resource_type, expected_value in initial_metrics.items():
        value = REGISTRY.get_sample_value(
            'resource_usage',
            {
                'service': 'test-service',
                'resource_type': resource_type
            }
        )
        assert value == expected_value
    
    # Update with new values
    updated_metrics = {
        'cpu_percent': 45.0,
        'memory_percent': 65.0
    }
    metrics_collector.update_resource_usage(updated_metrics)
    
    # Verify updated values
    for resource_type, expected_value in updated_metrics.items():
        value = REGISTRY.get_sample_value(
            'resource_usage',
            {
                'service': 'test-service',
                'resource_type': resource_type
            }
        )
        assert value == expected_value

def test_operation_status_tracking(metrics_collector):
    """Test operation tracking with various status values"""
    operations = [
        ("data_processing", "success"),
        ("data_processing", "failure"),
        ("data_processing", "partial"),
        ("user_authentication", "success"),
        ("user_authentication", "failure")
    ]
    
    # Track each operation
    for operation_type, status in operations:
        metrics_collector.track_operation(operation_type, status)
    
    # Verify operation counts for each combination
    operation_counts = {}
    for operation_type, status in operations:
        key = (operation_type, status)
        operation_counts[key] = operation_counts.get(key, 0) + 1
    
    for (operation_type, status), expected_count in operation_counts.items():
        count = REGISTRY.get_sample_value(
            'operations_total',
            {
                'service': 'test-service',
                'operation_type': operation_type,
                'status': status
            }
        )
        assert count == expected_count 