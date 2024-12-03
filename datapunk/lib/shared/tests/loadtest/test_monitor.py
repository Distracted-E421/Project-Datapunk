import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import curses
import psutil
from datapunk_shared.loadtest.monitor import (
    LoadTestMonitor,
    RealTimeMetrics
)

@pytest.fixture
def sample_metrics():
    return RealTimeMetrics(
        active_users=5,
        requests_per_second=100.0,
        current_error_rate=0.02,
        avg_response_time=0.1,
        p95_response_time=0.2,
        memory_usage=60.0,
        cpu_usage=45.0,
        timestamp=datetime.utcnow()
    )

@pytest.fixture
def monitor():
    with patch('curses.initscr'):
        monitor = LoadTestMonitor()
        yield monitor
        monitor.cleanup()

def test_metrics_initialization(sample_metrics):
    assert sample_metrics.active_users == 5
    assert sample_metrics.requests_per_second == 100.0
    assert sample_metrics.current_error_rate == 0.02
    assert sample_metrics.memory_usage == 60.0
    assert sample_metrics.cpu_usage == 45.0

@pytest.mark.asyncio
async def test_monitor_initialization(monitor):
    assert monitor.is_running == False
    assert len(monitor.metrics_history) == 0

@pytest.mark.asyncio
async def test_system_metrics_collection(monitor):
    with patch('psutil.cpu_percent') as mock_cpu:
        with patch('psutil.virtual_memory') as mock_memory:
            mock_cpu.return_value = 50.0
            mock_memory.return_value.percent = 70.0
            
            metrics = await monitor.collect_system_metrics()
            assert metrics['cpu_usage'] == 50.0
            assert metrics['memory_usage'] == 70.0

@pytest.mark.asyncio
async def test_metrics_aggregation(monitor, sample_metrics):
    # Add some test metrics
    monitor.metrics_history.append(sample_metrics)
    monitor.metrics_history.append(sample_metrics)
    
    aggregated = monitor.aggregate_metrics(duration_seconds=1)
    assert aggregated.requests_per_second == 100.0
    assert aggregated.avg_response_time == 0.1

@pytest.mark.asyncio
async def test_real_time_update(monitor):
    with patch.object(monitor, 'update_display') as mock_update:
        await monitor.update(
            active_users=5,
            response_time=0.1,
            is_error=False
        )
        
        mock_update.assert_called_once()
        assert len(monitor.metrics_history) == 1

@pytest.mark.asyncio
async def test_error_rate_calculation(monitor):
    # Simulate some requests with errors
    for _ in range(8):
        await monitor.update(active_users=1, response_time=0.1, is_error=False)
    for _ in range(2):
        await monitor.update(active_users=1, response_time=0.1, is_error=True)
    
    metrics = monitor.aggregate_metrics(duration_seconds=1)
    assert metrics.current_error_rate == 0.2  # 2 errors out of 10 requests

@pytest.mark.asyncio
async def test_metrics_persistence(monitor, sample_metrics):
    test_file = "test_metrics.json"
    
    # Add test metrics
    monitor.metrics_history.append(sample_metrics)
    
    with patch('pathlib.Path.write_text') as mock_write:
        await monitor.save_metrics(test_file)
        mock_write.assert_called_once()

@pytest.mark.asyncio
async def test_display_update(monitor):
    with patch('curses.newwin') as mock_window:
        mock_win = Mock()
        mock_window.return_value = mock_win
        
        monitor.initialize_display()
        monitor.update_display(RealTimeMetrics(
            active_users=5,
            requests_per_second=100.0,
            current_error_rate=0.02,
            avg_response_time=0.1,
            p95_response_time=0.2,
            memory_usage=60.0,
            cpu_usage=45.0,
            timestamp=datetime.utcnow()
        ))
        
        mock_win.addstr.assert_called()
        mock_win.refresh.assert_called_once()

@pytest.mark.asyncio
async def test_monitor_cleanup(monitor):
    with patch('curses.endwin') as mock_endwin:
        monitor.initialize_display()
        monitor.cleanup()
        
        mock_endwin.assert_called_once()
        assert monitor.is_running == False

@pytest.mark.asyncio
async def test_threshold_alerts(monitor):
    # Test CPU threshold alert
    with patch.object(monitor, 'trigger_alert') as mock_alert:
        await monitor.update(
            active_users=5,
            response_time=0.1,
            is_error=False,
            cpu_usage=95.0  # High CPU usage
        )
        
        mock_alert.assert_called_with("High CPU Usage Alert")

@pytest.mark.asyncio
async def test_metrics_export(monitor, sample_metrics):
    # Add test metrics
    monitor.metrics_history.append(sample_metrics)
    
    # Test CSV export
    with patch('pathlib.Path.write_text') as mock_write:
        await monitor.export_metrics("test_metrics.csv", format="csv")
        mock_write.assert_called_once()
    
    # Test JSON export
    with patch('pathlib.Path.write_text') as mock_write:
        await monitor.export_metrics("test_metrics.json", format="json")
        mock_write.assert_called_once() 