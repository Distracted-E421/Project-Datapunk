from typing import Dict, Any
import os
import psutil
from pathlib import Path
import structlog
from prometheus_client import Gauge
from ..utils.retry import with_retry, RetryConfig

logger = structlog.get_logger(__name__)

"""
Volume Monitoring System for Datapunk

A comprehensive volume monitoring system that tracks storage usage, health,
and performance metrics across configured volumes. Integrates with Prometheus
for metric collection and supports automated cleanup based on retention policies.

Key Features:
- Volume usage and health monitoring
- IO operation tracking
- Inode usage monitoring
- Retention-based cleanup
- Prometheus metric integration

Design Philosophy:
- Proactive storage management
- Early warning system for storage issues
- Comprehensive metric collection
- Automated maintenance

NOTE: Requires proper volume permissions for monitoring
TODO: Add support for volume-specific monitoring configurations
"""

class VolumeMonitor:
    """
    Monitors volume health and usage metrics with Prometheus integration.
    
    Key Capabilities:
    - Real-time volume metrics collection
    - Automated threshold monitoring
    - IO performance tracking
    - Data retention management
    
    FIXME: Consider adding volume type-specific monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes volume monitor with retry and metric configuration.
        
        Design Decisions:
        - Uses retry for resilient monitoring
        - Implements separate metrics for different aspects
        - Supports volume-specific thresholds
        
        WARNING: Ensure proper permissions for monitored paths
        """
        self.config = config
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0
        )
        
        # Prometheus metrics for comprehensive monitoring
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
        """
        Performs comprehensive volume health check with retry support.
        
        Implementation Notes:
        - Checks multiple health indicators
        - Records detailed metrics
        - Implements threshold monitoring
        - Handles various failure scenarios
        
        NOTE: IO stats may not be available for all volume types
        TODO: Add volume-specific health criteria
        """
        results = {}
        
        for volume_name, volume_config in self.config['volumes'].items():
            path = Path(volume_config['path'])
            if not path.exists():
                logger.warning(f"Volume path does not exist: {path}")
                continue
                
            try:
                # Collect and record various metrics
                usage = psutil.disk_usage(str(path))
                io_stats = psutil.disk_io_counters(perdisk=True)
                
                # Update Prometheus metrics for monitoring
                self._update_metrics(volume_name, path, usage, io_stats)
                
                # Analyze volume health
                results[volume_name] = self._analyze_health(
                    volume_name, usage, volume_config
                )
                
            except Exception as e:
                logger.error(f"Error checking volume {volume_name}: {str(e)}")
                results[volume_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return results
    
    def _get_inode_usage(self, path: str) -> float:
        """
        Calculates inode usage percentage for early capacity warnings.
        
        Why This Matters:
        - Inode exhaustion can prevent file creation
        - Often overlooked in standard monitoring
        - Critical for systems with many small files
        
        WARNING: Some filesystems may not support inode reporting
        """
        try:
            st = os.statvfs(path)
            inode_usage = ((st.f_files - st.f_ffree) / st.f_files) * 100
            return round(inode_usage, 2)
        except Exception as e:
            logger.error(f"Error getting inode usage for {path}: {str(e)}")
            return 0.0
    
    async def cleanup_old_data(self, volume_name: str) -> None:
        """
        Implements retention-based data cleanup for volume management.
        
        Cleanup Strategy:
        - Uses configurable retention period
        - Implements gradual cleanup
        - Logs cleanup actions
        - Handles cleanup failures gracefully
        
        TODO: Add support for custom cleanup strategies per volume
        """
        volume_config = self.config['volumes'].get(volume_name)
        if not volume_config:
            return
            
        retention_days = volume_config.get('retention_days', 30)
        path = Path(volume_config['path'])
        
        try:
            # Implement cleanup based on retention policy
            for item in path.glob('**/*'):
                if item.is_file():
                    age = (time.time() - item.stat().st_mtime) / (24 * 3600)
                    if age > retention_days:
                        item.unlink()
                        logger.info(f"Deleted old file: {item}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up volume {volume_name}: {str(e)}") 