import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from datapunk_shared.monitoring.volume_monitor import VolumeMonitor, VolumeConfig
from datapunk_shared.monitoring import MetricsClient
from datapunk.lib.tracing import TracingManager

@pytest.fixture
def volume_config():
    return VolumeConfig(
        name="test_monitor",
        check_interval=5,  # seconds
        warning_threshold=0.8,  # 80%
        critical_threshold=0.9,  # 90%
        volume_paths=["/data", "/logs"],
        retention_days=30
    )

@pytest.fixture
def mock_metrics():
    return MagicMock(spec=MetricsClient)

@pytest.fixture
def mock_tracing():
    return MagicMock(spec=TracingManager)

@pytest.fixture
async def volume_monitor(volume_config, mock_metrics, mock_tracing):
    monitor = VolumeMonitor(volume_config, mock_metrics, mock_tracing)
    await monitor.initialize()
    return monitor

@pytest.mark.asyncio
async def test_monitor_initialization(volume_monitor, volume_config):
    """Test volume monitor initialization"""
    assert volume_monitor.config == volume_config
    assert not volume_monitor.is_stopped
    assert len(volume_monitor.volume_stats) == 0

@pytest.mark.asyncio
async def test_volume_check(volume_monitor):
    """Test volume space check"""
    with patch('os.statvfs') as mock_statvfs:
        # Mock filesystem stats
        mock_stats = MagicMock()
        mock_stats.f_blocks = 1000  # Total blocks
        mock_stats.f_bfree = 300    # Free blocks
        mock_stats.f_frsize = 4096  # Block size
        mock_statvfs.return_value = mock_stats
        
        # Check volume space
        stats = await volume_monitor.check_volume_space("/data")
        
        # Verify calculations
        assert stats.total_space == 1000 * 4096
        assert stats.free_space == 300 * 4096
        assert stats.used_space == (1000 - 300) * 4096
        assert stats.usage_percent == 70.0  # (700/1000) * 100

@pytest.mark.asyncio
async def test_threshold_alerts(volume_monitor):
    """Test threshold alerts"""
    with patch('os.statvfs') as mock_statvfs:
        # Mock critical usage
        mock_stats = MagicMock()
        mock_stats.f_blocks = 1000
        mock_stats.f_bfree = 50  # 95% used
        mock_stats.f_frsize = 4096
        mock_statvfs.return_value = mock_stats
        
        # Check volume
        await volume_monitor.check_volumes()
        
        # Verify alerts
        volume_monitor.metrics.increment.assert_any_call(
            'volume_critical_alerts_total',
            {'monitor': volume_monitor.config.name, 'path': '/data'}
        )

@pytest.mark.asyncio
async def test_retention_cleanup(volume_monitor):
    """Test retention cleanup"""
    with patch('os.walk') as mock_walk, \
         patch('os.path.getmtime') as mock_getmtime, \
         patch('os.remove') as mock_remove:
        
        # Mock file structure
        mock_walk.return_value = [
            ('/data', [], ['old.log', 'new.log']),
        ]
        
        # Mock file timestamps
        def mock_time(path):
            if 'old' in path:
                return (datetime.now() - timedelta(days=40)).timestamp()
            return datetime.now().timestamp()
        
        mock_getmtime.side_effect = mock_time
        
        # Run cleanup
        await volume_monitor.cleanup_old_files()
        
        # Verify old file removal
        mock_remove.assert_called_once_with('/data/old.log')
        
        # Verify metrics
        volume_monitor.metrics.increment.assert_called_with(
            'files_cleaned_total',
            {'monitor': volume_monitor.config.name}
        )

@pytest.mark.asyncio
async def test_monitoring_cycle(volume_monitor):
    """Test complete monitoring cycle"""
    with patch.object(volume_monitor, 'check_volumes') as mock_check, \
         patch.object(volume_monitor, 'cleanup_old_files') as mock_cleanup:
        
        # Start monitoring
        monitor_task = volume_monitor.start_monitoring()
        
        # Wait for one cycle
        await asyncio.sleep(volume_monitor.config.check_interval + 0.1)
        
        # Stop monitoring
        await volume_monitor.stop()
        
        # Verify monitoring cycle
        mock_check.assert_called()
        mock_cleanup.assert_called()

@pytest.mark.asyncio
async def test_error_handling(volume_monitor):
    """Test error handling during monitoring"""
    with patch('os.statvfs') as mock_statvfs:
        # Mock filesystem error
        mock_statvfs.side_effect = OSError("Access denied")
        
        # Check volume
        stats = await volume_monitor.check_volume_space("/data")
        
        # Verify error metrics
        volume_monitor.metrics.increment.assert_called_with(
            'volume_check_errors_total',
            {'monitor': volume_monitor.config.name, 'path': '/data'}
        )
        
        assert stats is None

@pytest.mark.asyncio
async def test_volume_trends(volume_monitor):
    """Test volume usage trend analysis"""
    with patch('os.statvfs') as mock_statvfs:
        # Simulate increasing usage
        usages = [70, 75, 80]  # Percentage used
        for usage in usages:
            mock_stats = MagicMock()
            mock_stats.f_blocks = 1000
            mock_stats.f_bfree = int(1000 * (100 - usage) / 100)
            mock_stats.f_frsize = 4096
            mock_statvfs.return_value = mock_stats
            
            await volume_monitor.check_volumes()
        
        # Verify trend metrics
        volume_monitor.metrics.gauge.assert_any_call(
            'volume_usage_trend',
            5.0,  # Average increase
            {'monitor': volume_monitor.config.name, 'path': '/data'}
        )

@pytest.mark.asyncio
async def test_cleanup_strategies(volume_monitor):
    """Test different cleanup strategies"""
    with patch('os.walk') as mock_walk, \
         patch('os.path.getmtime') as mock_getmtime, \
         patch('os.path.getsize') as mock_getsize, \
         patch('os.remove') as mock_remove:
        
        # Mock file structure with sizes
        mock_walk.return_value = [
            ('/data', [], ['large.log', 'small.log']),
        ]
        
        # Mock file sizes
        def mock_size(path):
            if 'large' in path:
                return 1024 * 1024 * 100  # 100MB
            return 1024 * 10  # 10KB
        
        mock_getsize.side_effect = mock_size
        mock_getmtime.return_value = datetime.now().timestamp()
        
        # Run size-based cleanup
        await volume_monitor.cleanup_by_size(max_size_mb=50)
        
        # Verify large file removal
        mock_remove.assert_called_once_with('/data/large.log')
        
        # Verify metrics
        volume_monitor.metrics.increment.assert_called_with(
            'large_files_cleaned_total',
            {'monitor': volume_monitor.config.name}
        )

@pytest.mark.asyncio
async def test_monitoring_stats(volume_monitor):
    """Test monitoring statistics collection"""
    with patch('os.statvfs') as mock_statvfs:
        # Mock filesystem stats
        mock_stats = MagicMock()
        mock_stats.f_blocks = 1000
        mock_stats.f_bfree = 300
        mock_stats.f_frsize = 4096
        mock_statvfs.return_value = mock_stats
        
        # Collect stats for multiple cycles
        for _ in range(3):
            await volume_monitor.check_volumes()
        
        # Get monitoring stats
        stats = volume_monitor.get_monitoring_stats()
        
        # Verify stats collection
        assert len(stats.volume_stats) == len(volume_monitor.config.volume_paths)
        assert stats.check_count == 3
        assert stats.error_count == 0

@pytest.mark.asyncio
async def test_tracing_integration(volume_monitor):
    """Test tracing integration"""
    with patch('os.statvfs') as mock_statvfs:
        # Mock filesystem stats
        mock_stats = MagicMock()
        mock_stats.f_blocks = 1000
        mock_stats.f_bfree = 300
        mock_stats.f_frsize = 4096
        mock_statvfs.return_value = mock_stats
        
        # Check volumes
        await volume_monitor.check_volumes()
        
        # Verify tracing attributes
        volume_monitor.tracing.set_attribute.assert_any_call(
            'volume.check.paths',
            volume_monitor.config.volume_paths
        )
        volume_monitor.tracing.set_attribute.assert_any_call(
            'volume.usage.percent',
            70.0
        ) 