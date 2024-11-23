from typing import Optional, Dict, Any
import asyncio
from datetime import datetime
import structlog
from prometheus_client import Counter, Gauge, Histogram
from .database import DatabasePool
from .cache import CacheManager
from .messaging import MessageBroker
from .monitoring import MetricsCollector
from .health import HealthCheck
from .monitoring.volume_monitor import VolumeMonitor

logger = structlog.get_logger(__name__)

class BaseService:
    """Base class for all Datapunk services"""
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        self.service_name = service_name
        self.config = config
        self.logger = logger.bind(service=service_name)
        self.started_at = datetime.utcnow()
        
        # Core components
        self.db: Optional[DatabasePool] = None
        self.cache: Optional[CacheManager] = None
        self.broker: Optional[MessageBroker] = None
        self.metrics = MetricsCollector(service_name)
        self.health = HealthCheck(service_name)
        self.volume_monitor = VolumeMonitor(config.get('volumes', {}))
        
        # Prometheus metrics
        self.request_counter = Counter(
            f'{service_name}_requests_total',
            'Total requests processed'
        )
        self.error_counter = Counter(
            f'{service_name}_errors_total',
            'Total errors encountered'
        )
        self.processing_time = Histogram(
            f'{service_name}_processing_seconds',
            'Time spent processing requests'
        )
        self.active_connections = Gauge(
            f'{service_name}_active_connections',
            'Number of active connections'
        )
    
    async def initialize(self):
        """Initialize service components"""
        try:
            if self.config.get('database_enabled'):
                self.db = await DatabasePool.create(self.config['database'])
                
            if self.config.get('cache_enabled'):
                self.cache = await CacheManager.create(self.config['cache'])
                
            if self.config.get('messaging_enabled'):
                self.broker = await MessageBroker.create(self.config['messaging'])
                
            await self.health.register_check(self.check_health)
            self.logger.info("Service initialized successfully")
            
            # Start volume monitoring
            volume_status = await self.volume_monitor.check_volumes()
            self.logger.info("Volume status", status=volume_status)
            
        except Exception as e:
            self.logger.error("Failed to initialize service", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup service resources"""
        try:
            if self.db:
                await self.db.close()
            if self.cache:
                await self.cache.close()
            if self.broker:
                await self.broker.close()
        except Exception as e:
            self.logger.error("Error during cleanup", error=str(e))
    
    async def check_health(self) -> Dict[str, Any]:
        """Check service health"""
        health_status = {
            "service": self.service_name,
            "status": "healthy",
            "uptime": (datetime.utcnow() - self.started_at).total_seconds(),
            "checks": {}
        }
        
        try:
            if self.db:
                health_status["checks"]["database"] = await self.db.check_health()
            if self.cache:
                health_status["checks"]["cache"] = await self.cache.check_health()
            if self.broker:
                health_status["checks"]["messaging"] = await self.broker.check_health()
            
            volume_status = await self.volume_monitor.check_volumes()
            health_status["checks"]["volumes"] = volume_status
            
            # Update overall status if volumes are unhealthy
            if any(v.get('status') == 'error' for v in volume_status.values()):
                health_status["status"] = "unhealthy"
                
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def handle_error(self, error: Exception, context: Dict[str, Any] = None):
        """Standardized error handling"""
        self.error_counter.inc()
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context
        )