"""
Health-Aware Circuit Breaking

Implements health-aware decision making based on:
- Service health metrics
- System resource utilization
- Historical performance data
- Dependencies health status
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
import structlog
from enum import Enum
import statistics

logger = structlog.get_logger()

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class ResourceType(Enum):
    """Types of resources to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CONNECTIONS = "connections"

@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    utilization: float
    threshold: float
    trend: float  # Rate of change
    last_updated: datetime

@dataclass
class ServiceHealth:
    """Service health information"""
    status: HealthStatus
    response_time_ms: float
    error_rate: float
    resource_metrics: Dict[ResourceType, ResourceMetrics]
    dependencies: Dict[str, HealthStatus]
    last_check: datetime

class HealthConfig:
    """Configuration for health checks"""
    def __init__(
        self,
        check_interval_ms: float = 5000.0,
        response_time_threshold_ms: float = 1000.0,
        error_rate_threshold: float = 0.1,
        resource_thresholds: Dict[ResourceType, float] = None,
        dependency_timeout_ms: float = 500.0
    ):
        self.check_interval_ms = check_interval_ms
        self.response_time_threshold_ms = response_time_threshold_ms
        self.error_rate_threshold = error_rate_threshold
        self.resource_thresholds = resource_thresholds or {
            ResourceType.CPU: 0.8,
            ResourceType.MEMORY: 0.85,
            ResourceType.DISK: 0.9,
            ResourceType.NETWORK: 0.7,
            ResourceType.CONNECTIONS: 0.75
        }
        self.dependency_timeout_ms = dependency_timeout_ms

class HealthAwareBreaker:
    """
    Health-aware circuit breaker component that makes decisions
    based on service and system health metrics.
    """
    
    def __init__(
        self,
        config: Optional[HealthConfig] = None,
        metrics_client = None
    ):
        self.config = config or HealthConfig()
        self.metrics = metrics_client
        self.logger = logger.bind(component="health_aware_breaker")
        
        # Health tracking
        self.service_health: Dict[str, ServiceHealth] = {}
        self.response_times: Dict[str, List[float]] = {}
        self.error_counts: Dict[str, int] = {}
        self.request_counts: Dict[str, int] = {}
        
        # Resource tracking
        self.resource_history: Dict[str, Dict[ResourceType, List[ResourceMetrics]]] = {}
        self.resource_window = timedelta(minutes=5)
        
        # Dependency tracking
        self.dependency_health: Dict[str, Dict[str, HealthStatus]] = {}
        self.critical_dependencies: Dict[str, Set[str]] = {}
        
    async def check_health(self, service_id: str) -> ServiceHealth:
        """Check health of a service"""
        # Get latest metrics
        resource_metrics = await self._get_resource_metrics(service_id)
        response_time = self._calculate_response_time(service_id)
        error_rate = self._calculate_error_rate(service_id)
        
        # Check dependencies
        dependencies = await self._check_dependencies(service_id)
        
        # Determine status
        status = self._determine_health_status(
            service_id,
            response_time,
            error_rate,
            resource_metrics,
            dependencies
        )
        
        # Create health info
        health = ServiceHealth(
            status=status,
            response_time_ms=response_time,
            error_rate=error_rate,
            resource_metrics=resource_metrics,
            dependencies=dependencies,
            last_check=datetime.utcnow()
        )
        
        # Update tracking
        self.service_health[service_id] = health
        
        # Record metrics
        if self.metrics:
            await self._record_health_metrics(service_id, health)
            
        return health
        
    async def should_allow_request(
        self,
        service_id: str,
        request_priority: Optional[str] = None
    ) -> bool:
        """Determine if request should be allowed based on health"""
        health = await self.check_health(service_id)
        
        if health.status == HealthStatus.HEALTHY:
            return True
            
        if health.status == HealthStatus.UNHEALTHY:
            return False
            
        # For degraded status, consider priority
        if request_priority == "HIGH":
            return True
            
        # Check specific metrics
        if (health.response_time_ms > self.config.response_time_threshold_ms * 2 or
            health.error_rate > self.config.error_rate_threshold * 2):
            return False
            
        # Check resource exhaustion
        for resource, metrics in health.resource_metrics.items():
            if metrics.utilization > metrics.threshold * 1.5:
                return False
                
        return True
        
    def record_request(
        self,
        service_id: str,
        response_time_ms: float,
        is_error: bool
    ) -> None:
        """Record request metrics"""
        # Update response times
        if service_id not in self.response_times:
            self.response_times[service_id] = []
        self.response_times[service_id].append(response_time_ms)
        
        # Keep last 100 response times
        if len(self.response_times[service_id]) > 100:
            self.response_times[service_id] = self.response_times[service_id][-100:]
            
        # Update error counts
        if service_id not in self.error_counts:
            self.error_counts[service_id] = 0
        if service_id not in self.request_counts:
            self.request_counts[service_id] = 0
            
        if is_error:
            self.error_counts[service_id] += 1
        self.request_counts[service_id] += 1
        
    def add_critical_dependency(
        self,
        service_id: str,
        dependency_id: str
    ) -> None:
        """Add critical dependency for a service"""
        if service_id not in self.critical_dependencies:
            self.critical_dependencies[service_id] = set()
        self.critical_dependencies[service_id].add(dependency_id)
        
    async def _get_resource_metrics(
        self,
        service_id: str
    ) -> Dict[ResourceType, ResourceMetrics]:
        """Get current resource metrics"""
        metrics = {}
        
        for resource_type in ResourceType:
            if self.metrics:
                utilization = await self.metrics.get_gauge(
                    f"{service_id}_{resource_type.value}_utilization"
                )
            else:
                utilization = 0.0
                
            # Calculate trend
            trend = self._calculate_resource_trend(
                service_id,
                resource_type,
                utilization
            )
            
            metrics[resource_type] = ResourceMetrics(
                utilization=utilization,
                threshold=self.config.resource_thresholds[resource_type],
                trend=trend,
                last_updated=datetime.utcnow()
            )
            
        return metrics
        
    def _calculate_response_time(self, service_id: str) -> float:
        """Calculate average response time"""
        if not self.response_times.get(service_id):
            return 0.0
            
        return statistics.mean(self.response_times[service_id])
        
    def _calculate_error_rate(self, service_id: str) -> float:
        """Calculate error rate"""
        if not self.request_counts.get(service_id):
            return 0.0
            
        return (
            self.error_counts.get(service_id, 0) /
            self.request_counts[service_id]
        )
        
    async def _check_dependencies(
        self,
        service_id: str
    ) -> Dict[str, HealthStatus]:
        """Check health of dependencies"""
        dependencies = {}
        
        for dep_id in self.critical_dependencies.get(service_id, set()):
            if self.metrics:
                try:
                    async with asyncio.timeout(
                        self.config.dependency_timeout_ms / 1000
                    ):
                        health = await self.check_health(dep_id)
                        dependencies[dep_id] = health.status
                except asyncio.TimeoutError:
                    dependencies[dep_id] = HealthStatus.UNKNOWN
            else:
                dependencies[dep_id] = HealthStatus.UNKNOWN
                
        return dependencies
        
    def _determine_health_status(
        self,
        service_id: str,
        response_time: float,
        error_rate: float,
        resource_metrics: Dict[ResourceType, ResourceMetrics],
        dependencies: Dict[str, HealthStatus]
    ) -> HealthStatus:
        """Determine overall health status"""
        # Check critical dependencies
        if any(
            status == HealthStatus.UNHEALTHY
            for status in dependencies.values()
        ):
            return HealthStatus.UNHEALTHY
            
        # Check response time
        if response_time > self.config.response_time_threshold_ms * 2:
            return HealthStatus.UNHEALTHY
        elif response_time > self.config.response_time_threshold_ms:
            return HealthStatus.DEGRADED
            
        # Check error rate
        if error_rate > self.config.error_rate_threshold * 2:
            return HealthStatus.UNHEALTHY
        elif error_rate > self.config.error_rate_threshold:
            return HealthStatus.DEGRADED
            
        # Check resources
        for resource_type, metrics in resource_metrics.items():
            if metrics.utilization > metrics.threshold * 1.5:
                return HealthStatus.UNHEALTHY
            elif metrics.utilization > metrics.threshold:
                return HealthStatus.DEGRADED
                
        return HealthStatus.HEALTHY
        
    def _calculate_resource_trend(
        self,
        service_id: str,
        resource_type: ResourceType,
        current_value: float
    ) -> float:
        """Calculate resource utilization trend"""
        if service_id not in self.resource_history:
            self.resource_history[service_id] = {}
            
        if resource_type not in self.resource_history[service_id]:
            self.resource_history[service_id][resource_type] = []
            
        history = self.resource_history[service_id][resource_type]
        now = datetime.utcnow()
        
        # Add current value
        history.append(ResourceMetrics(
            utilization=current_value,
            threshold=self.config.resource_thresholds[resource_type],
            trend=0.0,
            last_updated=now
        ))
        
        # Clean old entries
        cutoff = now - self.resource_window
        history = [m for m in history if m.last_updated >= cutoff]
        self.resource_history[service_id][resource_type] = history
        
        if len(history) < 2:
            return 0.0
            
        # Calculate trend (rate of change per minute)
        time_diff = (history[-1].last_updated - history[0].last_updated).total_seconds() / 60
        if time_diff == 0:
            return 0.0
            
        value_diff = history[-1].utilization - history[0].utilization
        return value_diff / time_diff
        
    async def _record_health_metrics(
        self,
        service_id: str,
        health: ServiceHealth
    ) -> None:
        """Record health metrics"""
        await self.metrics.gauge(
            f"{service_id}_response_time",
            health.response_time_ms
        )
        
        await self.metrics.gauge(
            f"{service_id}_error_rate",
            health.error_rate
        )
        
        for resource_type, metrics in health.resource_metrics.items():
            await self.metrics.gauge(
                f"{service_id}_{resource_type.value}_utilization",
                metrics.utilization
            )
            
            await self.metrics.gauge(
                f"{service_id}_{resource_type.value}_trend",
                metrics.trend
            )
            
        await self.metrics.increment(
            f"{service_id}_health_status",
            {"status": health.status.value}
        ) 