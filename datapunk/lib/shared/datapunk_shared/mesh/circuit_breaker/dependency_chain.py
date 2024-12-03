"""
Dependency Chain Management for Circuit Breaker

Provides dependency tracking and management for service dependencies,
helping prevent cascading failures and coordinate recovery across
dependent services.
"""

from typing import Dict, Set, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
import structlog
from enum import Enum

logger = structlog.get_logger()

class DependencyType(Enum):
    """Types of service dependencies"""
    CRITICAL = "critical"      # Service cannot function without this dependency
    REQUIRED = "required"      # Service needs this for core functionality
    OPTIONAL = "optional"      # Service can operate with degraded functionality
    FALLBACK = "fallback"      # Used only when primary dependency fails

class HealthStatus(Enum):
    """Health status of a dependency"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class DependencyConfig:
    """Configuration for dependency management"""
    health_check_interval: float = 30.0  # Seconds between health checks
    failure_threshold: int = 3           # Failures before marking unhealthy
    recovery_threshold: int = 2          # Successes before marking healthy
    cascade_delay: float = 1.0           # Delay before cascading actions
    max_retry_interval: float = 300.0    # Maximum retry interval

@dataclass
class DependencyInfo:
    """Information about a service dependency"""
    dependency_type: DependencyType
    health_status: HealthStatus = HealthStatus.UNKNOWN
    failure_count: int = 0
    success_count: int = 0
    last_check: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_success: Optional[datetime] = None
    retry_count: int = 0
    impact_score: float = 1.0  # 0-1 score of dependency importance

class DependencyChain:
    """
    Manages service dependencies and their health status.
    
    Features:
    - Dependency tracking and health monitoring
    - Cascading failure prevention
    - Coordinated recovery
    - Impact analysis
    - Health status propagation
    """
    
    def __init__(self, config: Optional[DependencyConfig] = None):
        """Initialize dependency chain manager"""
        self.config = config or DependencyConfig()
        self.logger = logger.bind(component="dependency_chain")
        
        # Dependency tracking
        self.dependencies: Dict[str, Dict[str, DependencyInfo]] = {}
        self.reverse_deps: Dict[str, Set[str]] = {}
        
        # Health tracking
        self.health_checks: Dict[str, asyncio.Task] = {}
        self.health_status_cache: Dict[str, HealthStatus] = {}
        
        # Recovery tracking
        self.recovery_tasks: Dict[str, asyncio.Task] = {}
        self.recovery_state: Dict[str, bool] = {}
        
    async def start(self):
        """Start dependency monitoring"""
        # Start health check tasks for all services
        for service_id in self.dependencies:
            if service_id not in self.health_checks:
                self.health_checks[service_id] = asyncio.create_task(
                    self._health_check_loop(service_id)
                )
                
    async def stop(self):
        """Stop dependency monitoring"""
        # Cancel all health check tasks
        for task in self.health_checks.values():
            task.cancel()
        self.health_checks.clear()
        
        # Cancel all recovery tasks
        for task in self.recovery_tasks.values():
            task.cancel()
        self.recovery_tasks.clear()
        
    def add_dependency(self,
                      service_id: str,
                      dependency_id: str,
                      dependency_type: DependencyType,
                      impact_score: float = 1.0):
        """Add a service dependency"""
        # Initialize dependency tracking if needed
        if service_id not in self.dependencies:
            self.dependencies[service_id] = {}
            
        # Add dependency
        self.dependencies[service_id][dependency_id] = DependencyInfo(
            dependency_type=dependency_type,
            impact_score=impact_score
        )
        
        # Update reverse dependency mapping
        if dependency_id not in self.reverse_deps:
            self.reverse_deps[dependency_id] = set()
        self.reverse_deps[dependency_id].add(service_id)
        
        self.logger.info(
            "Added dependency",
            service=service_id,
            dependency=dependency_id,
            type=dependency_type.value
        )
        
    def remove_dependency(self,
                         service_id: str,
                         dependency_id: str):
        """Remove a service dependency"""
        if (service_id in self.dependencies and
            dependency_id in self.dependencies[service_id]):
            del self.dependencies[service_id][dependency_id]
            
            # Update reverse mapping
            if dependency_id in self.reverse_deps:
                self.reverse_deps[dependency_id].discard(service_id)
                if not self.reverse_deps[dependency_id]:
                    del self.reverse_deps[dependency_id]
                    
            self.logger.info(
                "Removed dependency",
                service=service_id,
                dependency=dependency_id
            )
            
    async def update_health(self,
                          service_id: str,
                          status: HealthStatus,
                          failure_info: Optional[Dict[str, Any]] = None):
        """Update service health status"""
        if service_id not in self.health_status_cache:
            self.health_status_cache[service_id] = HealthStatus.UNKNOWN
            
        old_status = self.health_status_cache[service_id]
        self.health_status_cache[service_id] = status
        
        # Log status change
        if old_status != status:
            self.logger.info(
                "Service health changed",
                service=service_id,
                old_status=old_status.value,
                new_status=status.value,
                failure_info=failure_info
            )
            
        # Handle status change
        if status == HealthStatus.UNHEALTHY:
            await self._handle_service_failure(service_id, failure_info)
        elif status == HealthStatus.HEALTHY:
            await self._handle_service_recovery(service_id)
            
    async def check_dependency_health(self,
                                    service_id: str,
                                    dependency_id: str) -> bool:
        """Check if dependency is healthy enough for use"""
        if (service_id not in self.dependencies or
            dependency_id not in self.dependencies[service_id]):
            return False
            
        dep_info = self.dependencies[service_id][dependency_id]
        status = self.health_status_cache.get(
            dependency_id,
            HealthStatus.UNKNOWN
        )
        
        # Critical dependencies must be healthy
        if dep_info.dependency_type == DependencyType.CRITICAL:
            return status == HealthStatus.HEALTHY
            
        # Required dependencies can be degraded
        if dep_info.dependency_type == DependencyType.REQUIRED:
            return status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
            
        # Optional dependencies can be in any state
        return True
        
    async def get_dependency_status(self,
                                  service_id: str) -> Dict[str, HealthStatus]:
        """Get health status of all dependencies"""
        if service_id not in self.dependencies:
            return {}
            
        return {
            dep_id: self.health_status_cache.get(
                dep_id,
                HealthStatus.UNKNOWN
            )
            for dep_id in self.dependencies[service_id]
        }
        
    async def _health_check_loop(self, service_id: str):
        """Background task for health checking"""
        while True:
            try:
                # Check all dependencies
                if service_id in self.dependencies:
                    for dep_id, dep_info in self.dependencies[service_id].items():
                        status = self.health_status_cache.get(
                            dep_id,
                            HealthStatus.UNKNOWN
                        )
                        
                        # Update last check time
                        dep_info.last_check = datetime.utcnow()
                        
                        if status == HealthStatus.UNHEALTHY:
                            dep_info.failure_count += 1
                            dep_info.success_count = 0
                            dep_info.last_failure = datetime.utcnow()
                        else:
                            dep_info.success_count += 1
                            dep_info.failure_count = 0
                            dep_info.last_success = datetime.utcnow()
                            
                # Sleep until next check
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Error in health check loop",
                    service=service_id,
                    error=str(e)
                )
                await asyncio.sleep(1)  # Brief pause before retry
        
    async def _handle_service_failure(self,
                                    service_id: str,
                                    failure_info: Optional[Dict[str, Any]]):
        """Handle service failure and its impact"""
        # Check for cascading impact
        impacted_services = self.reverse_deps.get(service_id, set())
        
        if impacted_services:
            self.logger.warning(
                "Service failure may impact dependents",
                failed_service=service_id,
                impacted_services=list(impacted_services),
                failure_info=failure_info
            )
            
            # Add small delay to allow for transient failures
            await asyncio.sleep(self.config.cascade_delay)
            
            # Update dependent services
            for dependent in impacted_services:
                if dependent in self.dependencies:
                    dep_info = self.dependencies[dependent].get(service_id)
                    if dep_info:
                        if dep_info.dependency_type == DependencyType.CRITICAL:
                            # Mark dependent as unhealthy
                            await self.update_health(
                                dependent,
                                HealthStatus.UNHEALTHY,
                                {
                                    "reason": "critical_dependency_failed",
                                    "dependency": service_id
                                }
                            )
                        elif dep_info.dependency_type == DependencyType.REQUIRED:
                            # Mark dependent as degraded
                            await self.update_health(
                                dependent,
                                HealthStatus.DEGRADED,
                                {
                                    "reason": "required_dependency_failed",
                                    "dependency": service_id
                                }
                            )
                            
        # Start recovery task if not already running
        if (service_id not in self.recovery_tasks or
            self.recovery_tasks[service_id].done()):
            self.recovery_tasks[service_id] = asyncio.create_task(
                self._recovery_loop(service_id)
            )
            
    async def _handle_service_recovery(self, service_id: str):
        """Handle service recovery"""
        # Update recovery state
        self.recovery_state[service_id] = True
        
        # Check impacted services
        impacted_services = self.reverse_deps.get(service_id, set())
        
        if impacted_services:
            self.logger.info(
                "Service recovered, checking dependents",
                recovered_service=service_id,
                impacted_services=list(impacted_services)
            )
            
            # Check each dependent
            for dependent in impacted_services:
                if dependent in self.dependencies:
                    # Check if all critical/required deps are healthy
                    all_deps_healthy = True
                    for dep_id, dep_info in self.dependencies[dependent].items():
                        if dep_info.dependency_type in (
                            DependencyType.CRITICAL,
                            DependencyType.REQUIRED
                        ):
                            if not await self.check_dependency_health(
                                dependent,
                                dep_id
                            ):
                                all_deps_healthy = False
                                break
                                
                    # Update dependent status
                    if all_deps_healthy:
                        await self.update_health(
                            dependent,
                            HealthStatus.HEALTHY,
                            {
                                "reason": "dependencies_recovered",
                                "recovered_dependency": service_id
                            }
                        )
                        
    async def _recovery_loop(self, service_id: str):
        """Background task for service recovery"""
        retry_interval = 1.0  # Start with 1 second
        
        while True:
            try:
                # Check if service has recovered
                if self.recovery_state.get(service_id, False):
                    break
                    
                # Exponential backoff for retries
                retry_interval = min(
                    retry_interval * 2,
                    self.config.max_retry_interval
                )
                
                # Wait before next retry
                await asyncio.sleep(retry_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    "Error in recovery loop",
                    service=service_id,
                    error=str(e)
                )
                await asyncio.sleep(1)
                
    async def get_metrics(self) -> Dict[str, Any]:
        """Get dependency chain metrics"""
        metrics = {
            "services": {},
            "dependencies": {},
            "health_summary": {
                status.value: 0 for status in HealthStatus
            }
        }
        
        # Collect service metrics
        for service_id in self.dependencies:
            service_metrics = {
                "dependency_count": len(self.dependencies[service_id]),
                "dependent_count": len(
                    self.reverse_deps.get(service_id, set())
                ),
                "health_status": self.health_status_cache.get(
                    service_id,
                    HealthStatus.UNKNOWN
                ).value,
                "dependencies": {}
            }
            
            # Add dependency details
            for dep_id, dep_info in self.dependencies[service_id].items():
                service_metrics["dependencies"][dep_id] = {
                    "type": dep_info.dependency_type.value,
                    "health": dep_info.health_status.value,
                    "impact_score": dep_info.impact_score,
                    "failure_count": dep_info.failure_count,
                    "success_count": dep_info.success_count,
                    "last_check": (
                        dep_info.last_check.isoformat()
                        if dep_info.last_check else None
                    )
                }
                
            metrics["services"][service_id] = service_metrics
            
        # Count health status
        for status in self.health_status_cache.values():
            metrics["health_summary"][status.value] += 1
            
        return metrics