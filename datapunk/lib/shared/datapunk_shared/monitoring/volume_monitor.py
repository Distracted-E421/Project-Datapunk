from typing import Dict, Any
import os
import psutil
from pathlib import Path
import structlog
from prometheus_client import Gauge
from ..utils.retry import with_retry, RetryConfig

logger = structlog.get_logger(__name__)

class VolumeMonitor:
    """Monitor volume usage and health"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        )
        
        # Prometheus metrics
        self.volume_usage = Gauge(
            'volume_usage_bytes',
            'Volume usage in bytes',
            ['volume', 'mount_point']
        )
        self.volume_free = Gauge(
            'volume_free_bytes',
            'Free space in bytes',
            ['volume', 'mount_point']
        )
        self.inode_usage = Gauge(
            'inode_usage_percent',
            'Inode usage percentage',
            ['volume', 'mount_point']
        )
        self.io_operations = Gauge(
            'io_operations',
            'IO operations per second',
            ['volume', 'operation']
        )
    
    @with_retry()
    async def check_volumes(self) -> Dict[str, Any]:
        """Check volume status and metrics"""
        results = {}
        
        for volume_name, volume_config in self.config['volumes'].items():
            path = Path(volume_config['path'])
            if not path.exists():
                logger.warning(f"Volume path does not exist: {path}")
                continue
                
            try:
                usage = psutil.disk_usage(str(path))
                io_stats = psutil.disk_io_counters(perdisk=True)
                
                # Update Prometheus metrics
                self.volume_usage.labels(
                    volume=volume_name,
                    mount_point=str(path)
                ).set(usage.used)
                
                self.volume_free.labels(
                    volume=volume_name,
                    mount_point=str(path)
                ).set(usage.free)
                
                self.inode_usage.labels(
                    volume=volume_name,
                    mount_point=str(path)
                ).set(self._get_inode_usage(str(path)))
                
                # Get IO stats if available
                if io_stats and volume_name in io_stats:
                    disk_io = io_stats[volume_name]
                    self.io_operations.labels(
                        volume=volume_name,
                        operation='read'
                    ).set(disk_io.read_count)
                    self.io_operations.labels(
                        volume=volume_name,
                        operation='write'
                    ).set(disk_io.write_count)
                
                results[volume_name] = {
                    'status': 'healthy',
                    'usage_percent': usage.percent,
                    'free_bytes': usage.free,
                    'total_bytes': usage.total,
                    'inode_usage_percent': self._get_inode_usage(str(path))
                }
                
                # Check thresholds
                if usage.percent > volume_config.get('usage_threshold', 90):
                    results[volume_name]['status'] = 'warning'
                    logger.warning(f"Volume {volume_name} usage above threshold: {usage.percent}%")
                    
            except Exception as e:
                logger.error(f"Error checking volume {volume_name}: {str(e)}")
                results[volume_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def _get_inode_usage(self, path: str) -> float:
        """Get inode usage percentage"""
        try:
            st = os.statvfs(path)
            inode_usage = ((st.f_files - st.f_ffree) / st.f_files) * 100
            return round(inode_usage, 2)
        except Exception as e:
            logger.error(f"Error getting inode usage for {path}: {str(e)}")
            return 0.0
    
    async def cleanup_old_data(self, volume_name: str) -> None:
        """Clean up old data based on retention policy"""
        volume_config = self.config['volumes'].get(volume_name)
        if not volume_config:
            return
            
        retention_days = volume_config.get('retention_days', 30)
        path = Path(volume_config['path'])
        
        try:
            # Implement cleanup logic based on retention policy
            # This is just an example - adjust based on your needs
            for item in path.glob('**/*'):
                if item.is_file():
                    age = (time.time() - item.stat().st_mtime) / (24 * 3600)
                    if age > retention_days:
                        item.unlink()
                        logger.info(f"Deleted old file: {item}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up volume {volume_name}: {str(e)}") 