from typing import Dict, List, Optional, Any
import structlog
import aiohttp
import asyncio
import socket
import ssl
import psutil
import os
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

logger = structlog.get_logger()

"""
Core Health Check Types for Datapunk Service Mesh

This module defines the foundational types for health monitoring:
- Health status definitions
- Check result structures
- Base check interfaces
- Common check implementations

These types provide a consistent framework for health
monitoring across the service mesh.

TODO: Add health score calculation
TODO: Implement check aggregation
FIXME: Improve error detail standardization
"""

class HealthStatus(Enum):
    """
    Service health status levels with routing implications.
    
    Status progression:
    HEALTHY -> DEGRADED -> UNHEALTHY
    
    Used for:
    - Load balancing decisions
    - Alert triggering
    - Metric categorization
    
    NOTE: Status changes affect service routing
    """
    HEALTHY = "healthy"    # Full service capability
    DEGRADED = "degraded"  # Limited functionality
    UNHEALTHY = "unhealthy"  # Service failure

@dataclass
class HealthCheckResult:
    """
    Standardized health check result structure.
    
    Provides:
    - Consistent status reporting
    - Detailed failure context
    - Timing information
    - Extended metrics
    
    NOTE: Details should be JSON-serializable
    TODO: Add result validation
    """
    status: HealthStatus
    message: str
    details: Optional[Dict] = None
    timestamp: datetime = datetime.utcnow()

class BaseHealthCheck:
    """
    Abstract base for all health checks.
    
    Defines contract for:
    - Async execution
    - Standard result format
    - Error handling
    - Timeout behavior
    
    NOTE: All checks must handle timeouts
    FIXME: Add check cancellation support
    """
    
    async def check(self) -> HealthCheckResult:
        raise NotImplementedError

class DatabaseHealthCheck(BaseHealthCheck):
    """
    Database connectivity and operation verification.
    
    Checks:
    - Connection status
    - Basic query execution
    - Timeout handling
    
    NOTE: Uses simple query to minimize impact
    TODO: Add connection pool monitoring
    """
    
    def __init__(self, db_client, timeout: float = 5.0):
        self.db = db_client
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        try:
            # Test query with timeout
            async with asyncio.timeout(self.timeout):
                await self.db.execute("SELECT 1")
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Database connection successful"
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}"
            )

class MessageQueueHealthCheck(BaseHealthCheck):
    """
    Message queue health and performance monitoring.
    
    Monitors:
    - Connection state
    - Queue depth
    - Processing backlog
    
    Status determination:
    - HEALTHY: Normal operation
    - DEGRADED: High queue depth
    - UNHEALTHY: Connection failure
    
    NOTE: Queue depth threshold affects status
    FIXME: Add consumer lag monitoring
    """
    
    def __init__(self, mq_client, timeout: float = 5.0):
        self.mq = mq_client
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        try:
            async with asyncio.timeout(self.timeout):
                # Check connection and queue status
                status = await self.mq.check_status()
                queue_depth = await self.mq.get_queue_depth()
                
                if queue_depth > 10000:  # Example threshold
                    return HealthCheckResult(
                        status=HealthStatus.DEGRADED,
                        message="High queue depth",
                        details={"queue_depth": queue_depth}
                    )
                
                return HealthCheckResult(
                    status=HealthStatus.HEALTHY,
                    message="Message queue operational",
                    details={"queue_depth": queue_depth}
                )
                
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Message queue check failed: {str(e)}"
            )

class ResourceHealthCheck(BaseHealthCheck):
    """
    System resource utilization monitoring.
    
    Tracks:
    - CPU usage
    - Memory consumption
    - Disk utilization
    
    Thresholds trigger status changes:
    - Above 90%: DEGRADED
    - Resource exhaustion: UNHEALTHY
    
    NOTE: Thresholds should match capacity planning
    TODO: Add network resource monitoring
    """
    
    def __init__(self,
                 cpu_threshold: float = 0.9,
                 memory_threshold: float = 0.9,
                 disk_threshold: float = 0.9):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
    
    async def check(self) -> HealthCheckResult:
        try:
            # Get resource usage
            cpu_percent = psutil.cpu_percent() / 100
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            details = {
                "cpu_usage": cpu_percent,
                "memory_usage": memory.percent / 100,
                "disk_usage": disk.percent / 100
            }
            
            # Check thresholds
            if (cpu_percent > self.cpu_threshold or
                memory.percent/100 > self.memory_threshold or
                disk.percent/100 > self.disk_threshold):
                return HealthCheckResult(
                    status=HealthStatus.DEGRADED,
                    message="Resource usage high",
                    details=details
                )
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY,
                message="Resource usage normal",
                details=details
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Resource check failed: {str(e)}"
            )

class DependencyHealthCheck(BaseHealthCheck):
    """
    External dependency availability monitoring.
    
    Status mapping:
    - 2xx/3xx: HEALTHY
    - 4xx: DEGRADED (service error)
    - 5xx: UNHEALTHY (service unavailable)
    
    Features:
    - Custom HTTP methods
    - Header support
    - Timeout handling
    
    NOTE: Consider security in header config
    FIXME: Add retry support for flaky dependencies
    """
    
    def __init__(self,
                 name: str,
                 url: str,
                 method: str = "GET",
                 timeout: float = 5.0,
                 headers: Optional[Dict] = None):
        self.name = name
        self.url = url
        self.method = method
        self.timeout = timeout
        self.headers = headers or {}
    
    async def check(self) -> HealthCheckResult:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status >= 500:
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            message=f"Dependency {self.name} unavailable",
                            details={"status_code": response.status}
                        )
                    elif response.status >= 400:
                        return HealthCheckResult(
                            status=HealthStatus.DEGRADED,
                            message=f"Dependency {self.name} returning errors",
                            details={"status_code": response.status}
                        )
                    return HealthCheckResult(
                        status=HealthStatus.HEALTHY,
                        message=f"Dependency {self.name} operational",
                        details={"status_code": response.status}
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Dependency {self.name} check failed: {str(e)}"
            ) 