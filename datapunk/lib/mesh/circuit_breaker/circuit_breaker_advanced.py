"""Advanced Circuit Breaker Implementation"""

from typing import Optional, Dict, Any, TYPE_CHECKING
import asyncio
import structlog
from datetime import datetime

from .circuit_breaker_strategies import CircuitBreakerStrategy
from .gradual_recovery import GradualRecoveryStrategy
from .metrics_collector import MetricsCollector
from .adaptive_timeout import AdaptiveTimeout, TimeoutConfig
from .failure_prediction import FailurePredictor, PredictionConfig
from .request_priority import PriorityManager, PriorityConfig
from .partial_recovery import PartialRecoveryManager, RecoveryConfig
from .context_retry import ContextRetryManager, RetryConfig
from .health_aware import HealthAwareBreaker, HealthConfig
from .discovery_integration import ServiceDiscoveryIntegration, DiscoveryConfig
from .dependency_aware_strategy import DependencyAwareStrategy
from .dependency_chain import DependencyConfig
from .rate_limiting_strategy import RateLimitingStrategy, RateLimitConfig

if TYPE_CHECKING:
    from .types import CircuitBreakerMetrics

logger = structlog.get_logger()

class AdvancedCircuitBreaker:
    """
    Advanced circuit breaker implementation with multiple strategies
    and enhanced features.
    """
    
    def __init__(self,
                 service_id: str,
                 strategy_type: str = "basic",
                 failure_threshold: int = 5,
                 success_threshold: int = 3,
                 timeout: float = 30.0,
                 half_open_timeout: float = 5.0,
                 dependency_config: Optional[DependencyConfig] = None,
                 timeout_config: Optional[TimeoutConfig] = None,
                 prediction_config: Optional[PredictionConfig] = None,
                 priority_config: Optional[PriorityConfig] = None,
                 recovery_config: Optional[RecoveryConfig] = None,
                 retry_config: Optional[RetryConfig] = None,
                 health_config: Optional[HealthConfig] = None,
                 discovery_config: Optional[DiscoveryConfig] = None,
                 rate_limit_config: Optional[RateLimitConfig] = None):
        """Initialize advanced circuit breaker"""
        self.service_id = service_id
        
        # Initialize strategy based on type
        if strategy_type == "basic":
            self.strategy = CircuitBreakerStrategy(
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
                half_open_timeout=half_open_timeout
            )
        elif strategy_type == "gradual":
            self.strategy = GradualRecoveryStrategy(
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
                half_open_timeout=half_open_timeout
            )
        elif strategy_type == "dependency":
            self.strategy = DependencyAwareStrategy(
                service_id=service_id,
                failure_threshold=failure_threshold,
                success_threshold=success_threshold,
                timeout=timeout,
                half_open_timeout=half_open_timeout,
                dependency_config=dependency_config
            )
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")
            
        self.logger = logger.bind(
            component="circuit_breaker",
            service=service_id,
            strategy=strategy_type
        )
        
        # Initialize enhanced features
        self.metrics = MetricsCollector(service_id)
        self.timeout_manager = AdaptiveTimeout(timeout_config)
        self.failure_predictor = FailurePredictor(prediction_config)
        self.priority_manager = PriorityManager(priority_config)
        self.recovery_manager = PartialRecoveryManager(recovery_config)
        self.retry_manager = ContextRetryManager(retry_config)
        self.health_manager = HealthAwareBreaker(health_config)
        self.discovery_manager = ServiceDiscoveryIntegration(discovery_config)
        self.rate_limiter = RateLimitingStrategy(rate_limit_config)
        
    async def start(self):
        """Start circuit breaker and its components"""
        await self.strategy.start()
        await self.metrics.start()
        await self.timeout_manager.start()
        await self.failure_predictor.start()
        await self.priority_manager.start()
        await self.recovery_manager.start()
        await self.retry_manager.start()
        await self.health_manager.start()
        await self.discovery_manager.start()
        
    async def stop(self):
        """Stop circuit breaker and its components"""
        await self.strategy.stop()
        await self.metrics.stop()
        await self.timeout_manager.stop()
        await self.failure_predictor.stop()
        await self.priority_manager.stop()
        await self.recovery_manager.stop()
        await self.retry_manager.stop()
        await self.health_manager.stop()
        await self.discovery_manager.stop()
        
    async def should_allow_request(self) -> bool:
        """Determine if request should be allowed"""
        # Check rate limits first
        if not await self.rate_limiter.should_allow_request():
            self.logger.warning("Request blocked by rate limiter")
            return False
            
        # Check failure prediction
        if await self.failure_predictor.predict_failure():
            self.logger.warning("Request blocked by failure prediction")
            return False
            
        # Check priority and resource availability
        if not await self.priority_manager.check_resources():
            self.logger.warning("Request blocked by resource constraints")
            return False
            
        # Check health status
        if not await self.health_manager.is_healthy():
            self.logger.warning("Request blocked by health check")
            return False
            
        # Check service discovery
        if not await self.discovery_manager.is_available():
            self.logger.warning("Request blocked by service discovery")
            return False
            
        # Check circuit breaker strategy
        return await self.strategy.should_allow_request()
        
    async def record_success(self):
        """Record successful request"""
        await self.strategy.record_success()
        await self.metrics.record_success()
        await self.timeout_manager.record_success()
        await self.failure_predictor.record_success()
        await self.priority_manager.record_success()
        await self.recovery_manager.record_success()
        await self.retry_manager.record_success()
        await self.health_manager.record_success()
        await self.discovery_manager.record_success()
        await self.rate_limiter.record_success()
        
    async def record_failure(self, error: Optional[Exception] = None):
        """Record failed request"""
        await self.strategy.record_failure(error)
        await self.metrics.record_failure()
        await self.timeout_manager.record_failure()
        await self.failure_predictor.record_failure()
        await self.priority_manager.record_failure()
        await self.recovery_manager.record_failure()
        await self.retry_manager.record_failure()
        await self.health_manager.record_failure()
        await self.discovery_manager.record_failure()
        await self.rate_limiter.record_failure()
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get circuit breaker metrics"""
        metrics = await self.metrics.get_metrics()
        
        # Add component metrics
        metrics.update({
            "strategy": await self.strategy.get_metrics(),
            "timeout": await self.timeout_manager.get_metrics(),
            "prediction": await self.failure_predictor.get_metrics(),
            "priority": await self.priority_manager.get_metrics(),
            "recovery": await self.recovery_manager.get_metrics(),
            "retry": await self.retry_manager.get_metrics(),
            "health": await self.health_manager.get_metrics(),
            "discovery": await self.discovery_manager.get_metrics(),
            "rate_limiter": await self.rate_limiter.get_metrics()
        })
            
        return metrics
        
    # Dependency management methods (only available with dependency strategy)
    def add_dependency(self, dependency_id: str, dependency_type: str,
                      impact_score: float = 1.0):
        """Add service dependency"""
        if isinstance(self.strategy, DependencyAwareStrategy):
            self.strategy.add_dependency(
                dependency_id,
                dependency_type,
                impact_score
            )
        else:
            raise RuntimeError(
                "Dependency management only available with dependency strategy"
            )
            
    def remove_dependency(self, dependency_id: str):
        """Remove service dependency"""
        if isinstance(self.strategy, DependencyAwareStrategy):
            self.strategy.remove_dependency(dependency_id)
        else:
            raise RuntimeError(
                "Dependency management only available with dependency strategy"
            )