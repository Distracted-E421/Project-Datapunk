"""Service health monitoring and reporting system.

This module implements the health check component of the service mesh as defined
in sys-arch.mmd. It provides comprehensive health monitoring with Prometheus
metrics integration for automated alerting and visualization in Grafana.

Key Features:
- System resource monitoring (CPU, memory, disk)
- Dependency health checking
- Prometheus metrics integration
- Automated health status reporting
- Historical health tracking

Implementation Notes:
- Uses psutil for system metrics collection
- Integrates with Prometheus for alerting
- Supports async health checks for dependencies
- Maintains last check timestamp for staleness detection
"""

from typing import Dict, Any, Optional
import asyncio
import aiohttp
from datetime import datetime
import psutil
from prometheus_client import Counter, Gauge

class HealthCheck:
    """Unified health monitoring for service mesh coordination.
    
    Implements comprehensive health checking:
    - System resource monitoring
    - External dependency checking
    - Metrics collection for alerting
    - Historical status tracking
    
    Note: Health checks are asynchronous to prevent blocking
    TODO: Add configurable check intervals
    """
    
    def __init__(self, service_name: str):
        """Initialize health checker with service identification.
        
        Args:
            service_name: Unique service identifier for metrics labeling
        
        Note: Metrics are automatically labeled with service_name
        """
        self.service_name = service_name
        self.last_check: Optional[datetime] = None
        
        # Prometheus metrics for automated alerting
        self.health_check_counter = Counter(
            'health_check_total',
            'Number of health checks performed',
            ['service', 'status']  # Enable per-service and status filtering
        )
        self.health_status = Gauge(
            'health_status',
            'Current health status',
            ['service', 'component']  # Enable component-level alerting
        )
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health assessment.
        
        Checks and reports:
        - CPU utilization
        - Memory usage
        - Disk space
        - Last check timestamp
        
        Returns:
            Health status dictionary with system metrics
        
        Note: Updates Prometheus metrics for alerting
        """
        try:
            self.last_check = datetime.utcnow()
            
            # Collect system metrics for resource monitoring
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            health_data = {
                'status': 'healthy',
                'timestamp': self.last_check.isoformat(),
                'service': self.service_name,
                'system': {
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'disk_percent': disk.percent
                }
            }
            
            # Update metrics for alerting
            self.health_check_counter.labels(
                service=self.service_name,
                status='success'
            ).inc()
            
            self.health_status.labels(
                service=self.service_name,
                component='system'
            ).set(1)  # 1 indicates healthy
            
            return health_data
            
        except Exception as e:
            # Record failure metrics for alerting
            self.health_check_counter.labels(
                service=self.service_name,
                status='failure'
            ).inc()
            
            self.health_status.labels(
                service=self.service_name,
                component='system'
            ).set(0)  # 0 indicates unhealthy
            
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': self.service_name,
                'error': str(e)
            }
    
    async def check_dependency(self, name: str, url: str) -> Dict[str, Any]:
        """Check health of external service dependency.
        
        Args:
            name: Dependency identifier for metrics
            url: Health check endpoint URL
        
        Returns:
            Dependency health status with response time
        
        Note: Uses aiohttp for non-blocking HTTP requests
        TODO: Add timeout configuration
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/health") as response:
                    is_healthy = response.status == 200
                    
                    self.health_status.labels(
                        service=self.service_name,
                        component=name
                    ).set(1 if is_healthy else 0)
                    
                    return {
                        'name': name,
                        'status': 'healthy' if is_healthy else 'unhealthy',
                        'response_time': response.elapsed.total_seconds()
                    }
        except Exception as e:
            self.health_status.labels(
                service=self.service_name,
                component=name
            ).set(0)
            
            return {
                'name': name,
                'status': 'unhealthy',
                'error': str(e)
            } 