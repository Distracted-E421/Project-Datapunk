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

"""BaseService: Core foundation for all Datapunk microservices.

This class implements the fundamental infrastructure required by all Datapunk services,
including database connections, caching, message brokering, metrics collection, and
health monitoring. It follows the service mesh architecture outlined in sys-arch.mmd.

Key Features:
- Automatic resource management and cleanup
- Integrated monitoring and metrics collection
- Health check coordination
- Standardized error handling
- Volume monitoring for data storage

Implementation Notes:
- Services should inherit from this class and implement their specific logic
- Resource initialization is lazy and configurable via the config dict
- Health checks are automatically registered and monitored
- Error handling includes standardized logging and metrics collection
"""

class BaseService:
    """Base class for all Datapunk services.
    
    Implements core infrastructure components as defined in the system architecture:
    - Database connection pooling with automatic cleanup
    - Distributed caching with invalidation support
    - Message broker integration for service mesh communication
    - Prometheus metrics for monitoring and alerting
    - Health check system for service mesh coordination
    - Volume monitoring for data storage management
    """
    
    def __init__(self, service_name: str, config: Dict[str, Any]):
        """Initialize service with configuration.
        
        Args:
            service_name: Unique identifier for this service instance
            config: Configuration dictionary containing settings for:
                   - database_enabled: Enable database connection pooling
                   - cache_enabled: Enable distributed caching
                   - messaging_enabled: Enable message broker
                   - volumes: Volume configuration for storage
        """
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
        """Initialize service components based on configuration.
        
        Lazily initializes enabled components in order:
        1. Database connection pool
        2. Cache manager
        3. Message broker
        4. Health check registration
        5. Volume monitoring
        
        Raises:
            Exception: If any component fails to initialize
        """
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
        """Release all service resources in reverse initialization order.
        
        Ensures graceful shutdown of:
        - Message broker connections
        - Cache connections
        - Database connections
        
        Note: Continues cleanup even if individual components fail
        """
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
        """Perform comprehensive health check of all service components.
        
        Checks health status of:
        - Database connections
        - Cache availability
        - Message broker connectivity
        - Storage volume status
        
        Returns:
            Dict containing health status and component-specific metrics
        
        Note: Service is considered unhealthy if any volume reports error status
        """
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
        """Standardized error handling with metrics and logging.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
        
        Note: Automatically increments error counter metric and logs with context
        """
        self.error_counter.inc()
        self.logger.error(
            "Error occurred",
            error=str(error),
            error_type=type(error).__name__,
            context=context
        )