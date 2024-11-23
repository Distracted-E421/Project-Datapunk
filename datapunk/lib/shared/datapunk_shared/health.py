from typing import Dict, Any, Optional
import asyncio
import aiohttp
from datetime import datetime
import psutil
from prometheus_client import Counter, Gauge

class HealthCheck:
    """Unified health checking for services"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.last_check: Optional[datetime] = None
        
        # Metrics
        self.health_check_counter = Counter(
            'health_check_total',
            'Number of health checks performed',
            ['service', 'status']
        )
        self.health_status = Gauge(
            'health_status',
            'Current health status',
            ['service', 'component']
        )
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        try:
            self.last_check = datetime.utcnow()
            
            # System metrics
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
            
            # Update metrics
            self.health_check_counter.labels(
                service=self.service_name,
                status='success'
            ).inc()
            
            self.health_status.labels(
                service=self.service_name,
                component='system'
            ).set(1)
            
            return health_data
            
        except Exception as e:
            self.health_check_counter.labels(
                service=self.service_name,
                status='failure'
            ).inc()
            
            self.health_status.labels(
                service=self.service_name,
                component='system'
            ).set(0)
            
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'service': self.service_name,
                'error': str(e)
            }
    
    async def check_dependency(self, name: str, url: str) -> Dict[str, Any]:
        """Check health of a dependency"""
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