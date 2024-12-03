"""
Partial Recovery Management

Implements gradual service recovery by selectively enabling features
based on health metrics, priorities, and dependencies.
"""

from typing import Dict, List, Set, Optional, Any
from enum import Enum
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict

logger = structlog.get_logger()

class FeatureState(Enum):
    """Feature availability states"""
    DISABLED = "disabled"
    TESTING = "testing"
    ENABLED = "enabled"

class FeatureHealth(Enum):
    """Feature health states"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

@dataclass
class FeatureConfig:
    """Configuration for a feature"""
    name: str
    priority: int
    dependencies: Set[str]
    min_health_threshold: float = 0.8
    test_duration_seconds: int = 30
    required: bool = False

class FeatureStatus:
    """Tracks feature status and metrics"""
    def __init__(self, config: FeatureConfig):
        self.config = config
        self.state = FeatureState.DISABLED
        self.health = FeatureHealth.UNKNOWN
        self.success_count = 0
        self.error_count = 0
        self.last_test_start = None
        self.last_state_change = datetime.utcnow()
        
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.error_count
        if total == 0:
            return 1.0
        return self.success_count / total
        
    def reset_counters(self):
        """Reset success/error counters"""
        self.success_count = 0
        self.error_count = 0
        
    def update_health(self):
        """Update health status based on metrics"""
        if self.success_rate >= self.config.min_health_threshold:
            self.health = FeatureHealth.HEALTHY
        elif self.success_rate >= self.config.min_health_threshold * 0.7:
            self.health = FeatureHealth.DEGRADED
        else:
            self.health = FeatureHealth.UNHEALTHY

class PartialRecoveryManager:
    """
    Manages partial service recovery through feature-level control.
    
    Features:
    - Priority-based recovery
    - Dependency management
    - Health monitoring
    - Gradual enablement
    - Automatic rollback
    """
    
    def __init__(self,
                 features: Dict[str, FeatureConfig],
                 metrics_client = None):
        self.features = features
        self.metrics = metrics_client
        self.logger = logger.bind(component="partial_recovery")
        
        # Initialize feature status tracking
        self.status: Dict[str, FeatureStatus] = {
            name: FeatureStatus(config)
            for name, config in features.items()
        }
        
        # Build dependency graph
        self.dependents: Dict[str, Set[str]] = defaultdict(set)
        for name, config in features.items():
            for dep in config.dependencies:
                self.dependents[dep].add(name)
                
        # Track recovery progress
        self.recovery_start_time = None
        self.recovery_phase = 0
        
    async def start_recovery(self):
        """Begin partial recovery process"""
        self.recovery_start_time = datetime.utcnow()
        self.recovery_phase = 1
        
        # Start with highest priority features
        await self._enable_priority_features()
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_recovery_started"
            )
            
    async def _enable_priority_features(self):
        """Enable features by priority"""
        # Group features by priority
        by_priority = defaultdict(list)
        for name, config in self.features.items():
            by_priority[config.priority].append(name)
            
        # Enable in priority order
        for priority in sorted(by_priority.keys()):
            features = by_priority[priority]
            for name in features:
                await self.test_feature(name)
                
    async def test_feature(self, feature_name: str):
        """Begin testing a feature"""
        status = self.status[feature_name]
        config = status.config
        
        # Check dependencies
        for dep in config.dependencies:
            dep_status = self.status[dep]
            if dep_status.state != FeatureState.ENABLED:
                self.logger.warning(
                    "Cannot test feature - dependency not enabled",
                    feature=feature_name,
                    dependency=dep,
                    dep_state=dep_status.state
                )
                return
                
        # Start testing
        status.state = FeatureState.TESTING
        status.last_test_start = datetime.utcnow()
        status.reset_counters()
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_feature_testing",
                {"feature": feature_name}
            )
            
    async def record_result(self,
                          feature_name: str,
                          success: bool):
        """Record feature test result"""
        status = self.status[feature_name]
        
        if success:
            status.success_count += 1
        else:
            status.error_count += 1
            
        # Update health status
        status.update_health()
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_feature_result",
                {
                    "feature": feature_name,
                    "success": str(success),
                    "health": status.health.value
                }
            )
            
        # Check if test period is complete
        if status.state == FeatureState.TESTING:
            test_duration = datetime.utcnow() - status.last_test_start
            if test_duration.total_seconds() >= status.config.test_duration_seconds:
                await self._complete_test(feature_name)
                
    async def _complete_test(self, feature_name: str):
        """Complete feature test period"""
        status = self.status[feature_name]
        
        if status.health == FeatureHealth.HEALTHY:
            # Enable feature
            status.state = FeatureState.ENABLED
            status.last_state_change = datetime.utcnow()
            
            # Test dependent features
            for dependent in self.dependents[feature_name]:
                await self.test_feature(dependent)
                
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_feature_enabled",
                    {"feature": feature_name}
                )
        else:
            # Disable feature
            status.state = FeatureState.DISABLED
            status.last_state_change = datetime.utcnow()
            
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_feature_disabled",
                    {"feature": feature_name}
                )
                
            # Check if required feature
            if status.config.required:
                await self._rollback_recovery()
                
    async def _rollback_recovery(self):
        """Rollback recovery due to required feature failure"""
        self.logger.warning("Rolling back partial recovery")
        
        # Disable all features
        for status in self.status.values():
            if status.state != FeatureState.DISABLED:
                status.state = FeatureState.DISABLED
                status.last_state_change = datetime.utcnow()
                
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_recovery_rollback"
            )
            
    def is_feature_available(self, feature_name: str) -> bool:
        """Check if feature is available"""
        return self.status[feature_name].state == FeatureState.ENABLED
        
    def get_feature_metrics(self) -> Dict[str, Any]:
        """Get current feature metrics"""
        metrics = {}
        
        for name, status in self.status.items():
            metrics[f"feature_{name}"] = {
                "state": status.state.value,
                "health": status.health.value,
                "success_rate": status.success_rate,
                "success_count": status.success_count,
                "error_count": status.error_count
            }
            
        return metrics 