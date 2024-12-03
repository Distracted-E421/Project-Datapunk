"""
Advanced Service Mesh Circuit Breaker

Implements an enhanced circuit breaker pattern for the Datapunk service mesh
with distributed state management and adaptive failure detection. Provides
robust service protection with minimal false positives.

Key features:
- Distributed state management
- Adaptive failure thresholds
- Half-open state testing
- Metric integration
- Cache-based state sharing
- Multiple recovery patterns
- Fallback chain support
- Request prioritization
- Resource reservation
"""

from typing import Optional, Dict, Any, TYPE_CHECKING, List, Callable
import structlog
from datetime import datetime, timedelta

from .circuit_breaker import CircuitBreaker
from .circuit_breaker_strategies import CircuitState, GradualRecoveryStrategy
from .recovery_patterns import (
    FallbackChain,
    RecoveryPattern,
    ExponentialBackoffPattern,
    PartialRecoveryPattern,
    AdaptiveRecoveryPattern
)
from .request_priority import (
    RequestPriority,
    PriorityConfig,
    PriorityManager
)
from datapunk_shared.exceptions import CircuitBreakerError
from .failure_prediction import FailurePredictor, PredictionMetric
from .adaptive_timeout import AdaptiveTimeout, TimeoutConfig
from .partial_recovery import PartialRecoveryManager, FeatureConfig
from .context_retry import (
    ContextRetryManager,
    RetryContext,
    RetryPolicy,
    AdaptiveRetryStrategy
)
from .health_aware import HealthAwareBreaker, HealthConfig
from .discovery_integration import ServiceDiscoveryIntegration, DiscoveryConfig

if TYPE_CHECKING:
    from datapunk_shared.monitoring import MetricsClient
    from datapunk_shared.cache import CacheClient

logger = structlog.get_logger()

class AdvancedCircuitBreaker(CircuitBreaker):
    """
    Enhanced circuit breaker with distributed state management.
    
    Extends basic circuit breaker with cache-based state sharing,
    advanced failure detection, multiple recovery patterns, and
    request prioritization. Designed for high-availability
    environments with multiple service instances.
    """
    
    def __init__(self,
                 service_name: str,
                 metrics: 'MetricsClient',
                 cache: 'CacheClient',
                 failure_threshold: int = 5,
                 recovery_timeout: int = 30,
                 half_open_timeout: int = 5,
                 strategy: Optional['CircuitBreakerStrategy'] = None,
                 recovery_pattern: Optional[RecoveryPattern] = None,
                 feature_priorities: Optional[Dict[str, int]] = None,
                 priority_config: Optional[PriorityConfig] = None,
                 reset_timeout: float = 60.0,
                 timeout_config: Optional[TimeoutConfig] = None,
                 features: Optional[Dict[str, FeatureConfig]] = None,
                 health_config: Optional[HealthConfig] = None,
                 discovery_config: Optional[DiscoveryConfig] = None):
        """
        Initialize advanced circuit breaker.
        
        Parameters are tuned for typical microservice behavior:
        - failure_threshold: Trips after 5 failures
        - recovery_timeout: 30s cool-down period
        - half_open_timeout: 5s test window
        
        Args:
            strategy: Custom circuit breaker strategy
            recovery_pattern: Custom recovery pattern
            feature_priorities: Feature priorities for partial recovery
            priority_config: Request priority configuration
            reset_timeout: Circuit breaker reset timeout
            timeout_config: Adaptive timeout configuration
        """
        super().__init__(service_name, metrics)
        self.cache = cache
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_timeout = half_open_timeout
        self.logger = logger.bind(component="advanced_circuit_breaker")
        
        # Initialize with gradual recovery by default
        self.strategy = strategy or GradualRecoveryStrategy(
            metrics=metrics,
            base_recovery_rate=0.1,  # Start with 10% traffic
            recovery_step=0.1,       # Increase by 10% per window
            error_threshold=0.1      # Max 10% errors during recovery
        )
        
        # Initialize recovery pattern
        if recovery_pattern:
            self.recovery_pattern = recovery_pattern
        elif feature_priorities:
            self.recovery_pattern = PartialRecoveryPattern(
                feature_priorities=feature_priorities,
                metrics=metrics
            )
        else:
            self.recovery_pattern = AdaptiveRecoveryPattern(
                metrics=metrics
            )
            
        # Initialize priority management
        self.priority_manager = PriorityManager(
            priority_config or PriorityConfig(),
            metrics
        )
            
        # Initialize fallback chain
        self.fallback_chain = FallbackChain(cache, metrics)
        self._fallbacks: List[Callable] = []
        
        # Initialize failure predictor
        self.failure_predictor = FailurePredictor(metrics)
        
        # Initialize adaptive timeout
        self.timeout_manager = AdaptiveTimeout(
            config=timeout_config,
            metrics_client=metrics
        )
        
        # Initialize partial recovery
        self.recovery_manager = (
            PartialRecoveryManager(features, metrics)
            if features else None
        )
        
        # Track metrics for prediction
        self.request_start_time = None
        self.request_count = 0
        self.error_count = 0
        self.last_metrics_update = datetime.utcnow()
        self.metrics_update_interval = timedelta(seconds=10)
        
        # State management
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        
        # Enhanced components
        self.failure_predictor = FailurePredictor()
        self.timeout_manager = AdaptiveTimeout(
            config=timeout_config,
            metrics_client=metrics
        )
        self.recovery_manager = PartialRecoveryManager()
        self.retry_manager = ContextRetryManager(
            policy=retry_policy,
            strategy=AdaptiveRetryStrategy(),
            metrics_client=metrics
        )
        self.health_manager = HealthAwareBreaker(
            config=health_config,
            metrics_client=metrics
        )
        self.discovery_manager = ServiceDiscoveryIntegration(
            config=discovery_config,
            metrics_client=metrics
        )
        
    def add_fallback(self, handler: Callable):
        """Add fallback handler for degraded operation"""
        self.fallback_chain.add_fallback(handler)
        
    async def execute_with_fallback(self,
                                  func: Callable,
                                  *args,
                                  priority: RequestPriority = RequestPriority.NORMAL,
                                  cache_key: Optional[str] = None,
                                  timeout_ms: Optional[int] = None,
                                  **kwargs):
        """
        Execute function with circuit breaking and fallbacks.
        
        Provides full protection with:
        1. Circuit breaker state checks
        2. Priority-based admission control
        3. Recovery pattern management
        4. Fallback chain execution
        5. Metric collection
        """
        # Check priority admission
        if not await self.priority_manager.start_request(
            priority,
            timeout_ms
        ):
            raise CircuitBreakerError(
                f"Request rejected (priority: {priority.name})"
            )
            
        try:
            if not await self.allow_request():
                raise CircuitBreakerError("Circuit is open")
                
            result = await self.fallback_chain.execute(
                func,
                *args,
                cache_key=cache_key,
                **kwargs
            )
            
            if result.error:
                await self.record_failure()
                raise result.error
                
            if result.fallback_used:
                await self.metrics.increment(
                    "circuit_breaker_fallback_success",
                    {"service": self.service_name}
                )
            else:
                await self.record_success()
                
            return result.value
            
        except Exception as e:
            await self.record_failure()
            raise
            
        finally:
            # Always complete request tracking
            await self.priority_manager.finish_request(priority)
            
    async def allow_request(self) -> bool:
        """
        Check if request should be allowed through circuit.
        
        Implements:
        1. Basic circuit state checks
        2. Recovery pattern verification
        3. Distributed state management
        4. Metric collection
        """
        # Get current state from cache
        state = await self._get_cached_state()
        
        if state == CircuitState.OPEN:
            # Check recovery pattern
            should_attempt = await self.recovery_pattern.should_attempt_recovery(
                self.failure_count,
                self.last_failure_time
            )
            
            if should_attempt:
                await self._transition_state(CircuitState.HALF_OPEN)
            else:
                await self.metrics.increment(
                    "circuit_breaker_rejections",
                    {"service": self.service_name}
                )
                return False
                
        if state == CircuitState.HALF_OPEN:
            # Use strategy to determine request allowance
            allowed_rate = await self.strategy.get_allowed_request_rate()
            
            # Randomly allow requests based on rate
            import random
            if random.random() > allowed_rate:
                await self.metrics.increment(
                    "circuit_breaker_recovery_rejections",
                    {"service": self.service_name}
                )
                return False
                
        return True
        
    async def record_success(self):
        """Record successful request and update recovery state."""
        await super().record_success()
        
        if self.state == CircuitState.HALF_OPEN:
            if await self.recovery_pattern.handle_success(self.success_count):
                await self._transition_state(CircuitState.CLOSED)
                await self.strategy.reset_recovery()
                
    async def record_failure(self):
        """Record failed request and check for circuit opening."""
        await super().record_failure()
        
        # Update recovery pattern
        await self.recovery_pattern.handle_failure(self.failure_count)
        
        # Check if circuit should open
        if await self.strategy.should_open(
            self.failure_count,
            await self._calculate_error_rate()
        ):
            await self._transition_state(CircuitState.OPEN)
            await self.strategy.reset_recovery()
            
            # Adjust priority threshold during outage
            await self.priority_manager.adjust_min_priority(
                RequestPriority.HIGH.value
            )
            
    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate for strategy decisions."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.failure_count / total
        
    async def _get_cached_state(self) -> CircuitState:
        """Get circuit state from distributed cache."""
        try:
            state = await self.cache.get(
                f"circuit:{self.service_name}:state"
            )
            return CircuitState(state) if state else CircuitState.CLOSED
        except Exception as e:
            self.logger.error("Failed to get circuit state", error=str(e))
            return self.state  # Fallback to local state
            
    async def _transition_state(self, new_state: CircuitState):
        """Update circuit state in both cache and local memory."""
        self.state = new_state
        try:
            await self.cache.set(
                f"circuit:{self.service_name}:state",
                new_state.value,
                expire=self.recovery_timeout * 2
            )
            
            # Record state change metric
            await self.metrics.increment(
                "circuit_breaker_state_change",
                {
                    "service": self.service_name,
                    "new_state": new_state.value
                }
            )
            
            # Adjust priority thresholds based on state
            if new_state == CircuitState.OPEN:
                await self.priority_manager.adjust_min_priority(
                    RequestPriority.HIGH.value
                )
            elif new_state == CircuitState.CLOSED:
                await self.priority_manager.adjust_min_priority(0)
                
        except Exception as e:
            self.logger.error("Failed to update circuit state", error=str(e))
            
    async def _check_recovery_timeout(self) -> bool:
        """Check if enough time has passed for recovery attempt."""
        try:
            last_failure = await self.cache.get(
                f"circuit:{self.service_name}:last_failure"
            )
            if not last_failure:
                return True
                
            elapsed = datetime.utcnow() - datetime.fromisoformat(last_failure)
            return elapsed.total_seconds() >= self.recovery_timeout
            
        except Exception as e:
            self.logger.error("Failed to check recovery timeout", error=str(e))
            return True  # Fail open on cache errors
        
    async def _update_metrics(self):
        """Update metrics for failure prediction"""
        now = datetime.utcnow()
        if now - self.last_metrics_update < self.metrics_update_interval:
            return
            
        # Calculate error rate
        total_requests = max(1, self.request_count)
        error_rate = self.error_count / total_requests
        await self.failure_predictor.record_metric(
            PredictionMetric.ERROR_RATE,
            error_rate
        )
        
        # Reset counters
        self.request_count = 0
        self.error_count = 0
        self.last_metrics_update = now
        
        # Update dynamic thresholds
        await self.failure_predictor.update_thresholds()
        
    async def before_request(self,
                           feature: Optional[str] = None):
        """Called before each request"""
        self.request_start_time = datetime.utcnow()
        self.request_count += 1
        
        # Check circuit state
        if self.state == CircuitState.OPEN:
            if self.strategy.should_attempt_reset(self):
                self.state = CircuitState.HALF_OPEN
                if self.metrics:
                    await self.metrics.increment(
                        "circuit_breaker_state_change",
                        {"from": "open", "to": "half_open"}
                    )
                    
                # Start partial recovery if configured
                if self.recovery_manager:
                    await self.recovery_manager.start_recovery()
            else:
                raise CircuitBreakerError("Circuit is OPEN")
                
        # Check feature availability
        if (feature and self.recovery_manager and
            not self.recovery_manager.is_feature_available(feature)):
            raise CircuitBreakerError(
                f"Feature {feature} is not available"
            )
                
        # Check failure prediction
        will_fail, confidence = await self.failure_predictor.predict_failure()
        if will_fail and confidence > 0.8:  # High confidence threshold
            self.logger.warning("Failure predicted",
                              confidence=confidence)
            if self.state == CircuitState.CLOSED:
                self.state = CircuitState.OPEN
                if self.metrics:
                    await self.metrics.increment(
                        "circuit_breaker_state_change",
                        {"from": "closed", "to": "open",
                         "reason": "predicted_failure"}
                    )
                raise CircuitBreakerError(
                    "Circuit opened due to predicted failure"
                )
                
        # Get current timeout value
        timeout = await self.timeout_manager.get_timeout()
        return timeout

    async def after_request(self,
                          feature: Optional[str] = None):
        """Called after successful request"""
        if self.request_start_time:
            latency = (datetime.utcnow() - 
                      self.request_start_time).total_seconds() * 1000
                      
            # Record response time for both systems
            await self.failure_predictor.record_metric(
                PredictionMetric.LATENCY,
                latency
            )
            await self.timeout_manager.record_response_time(
                latency,
                is_success=True
            )
            
            # Record feature success if applicable
            if feature and self.recovery_manager:
                await self.recovery_manager.record_result(
                    feature,
                    success=True
                )
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_state_change",
                    {"from": "half_open", "to": "closed"}
                )
                
        await self._update_metrics()

    async def on_failure(self,
                        exception: Exception,
                        feature: Optional[str] = None):
        """Called when request fails"""
        self.error_count += 1
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        # Record timeout failure if applicable
        if isinstance(exception, TimeoutError):
            current_timeout = await self.timeout_manager.get_timeout()
            await self.timeout_manager.record_response_time(
                current_timeout * 1.1,  # Slightly higher than timeout
                is_success=False
            )
            
        # Record feature failure if applicable
        if feature and self.recovery_manager:
            await self.recovery_manager.record_result(
                feature,
                success=False
            )
        
        if (self.state == CircuitState.CLOSED and
            self.failure_count >= self.failure_threshold):
            self.state = CircuitState.OPEN
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_state_change",
                    {"from": "closed", "to": "open",
                     "reason": "failure_threshold"}
                )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            if self.metrics:
                await self.metrics.increment(
                    "circuit_breaker_state_change",
                    {"from": "half_open", "to": "open",
                     "reason": "test_failed"}
                )
                
        await self._update_metrics()

    async def get_metrics(self) -> Dict[str, Any]:
        """Get combined metrics from all systems"""
        metrics = await super().get_metrics()
        
        # Add timeout metrics
        timeout_metrics = self.timeout_manager.get_timeout_metrics()
        metrics.update({
            f"timeout_{k}": v
            for k, v in timeout_metrics.items()
        })
        
        # Add feature metrics if applicable
        if self.recovery_manager:
            feature_metrics = self.recovery_manager.get_feature_metrics()
            metrics.update(feature_metrics)
            
        return metrics

    def add_critical_dependency(
        self,
        service_id: str,
        dependency_id: str
    ) -> None:
        """Add critical dependency for health tracking"""
        self.health_manager.add_critical_dependency(service_id, dependency_id)

    async def check_service_health(
        self,
        service_id: str
    ) -> ServiceHealth:
        """Check health status of a service"""
        return await self.health_manager.check_health(service_id)

    async def start(self) -> None:
        """Start background tasks"""
        await self.discovery_manager.start()

    async def stop(self) -> None:
        """Stop background tasks"""
        await self.discovery_manager.stop()

    async def call(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        service_id: Optional[str] = None,
        instance_id: Optional[str] = None,
        retry_context: Optional[Dict[str, Any]] = None,
        metadata_requirements: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        Execute function with circuit breaker protection and service discovery.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            service_id: Optional service identifier for discovery
            instance_id: Optional specific instance ID to use
            retry_context: Optional context for retry decisions
            metadata_requirements: Optional metadata requirements for instance selection
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
            Exception: If function execution fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if not await self._should_attempt_recovery():
                raise CircuitBreakerError("Circuit breaker is open")
                
            self.state = CircuitBreakerState.HALF_OPEN
            
        # Check service health if ID provided
        if service_id:
            if not await self.health_manager.should_allow_request(
                service_id,
                retry_context.get("priority") if retry_context else None
            ):
                raise CircuitBreakerError(f"Service {service_id} is unhealthy")
                
            # Get instance if not specified
            if not instance_id:
                instance = await self.discovery_manager.get_instance(
                    service_id,
                    metadata_requirements
                )
                if not instance:
                    raise CircuitBreakerError(f"No available instances for service {service_id}")
                instance_id = instance.instance_id
            
        # Create retry context if not provided
        if retry_context is None:
            retry_context = {}
            
        attempt = 1
        start_time = datetime.utcnow()
        connection = None
        
        while True:
            try:
                # Get connection if using discovery
                if service_id and instance_id:
                    connection = await self.discovery_manager.get_connection(
                        service_id,
                        instance_id
                    )
                    if not connection:
                        raise CircuitBreakerError("Failed to get connection")
                    
                    # Add connection to kwargs
                    kwargs["connection"] = connection
                
                # Check for predicted failures
                if await self.failure_predictor.predict_failure():
                    self.logger.warning("Failure predicted, applying preventive measures")
                    await self._handle_predicted_failure()
                
                # Get adaptive timeout
                timeout = await self.timeout_manager.get_timeout()
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
                
                # Record success metrics
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                if service_id:
                    self.health_manager.record_request(
                        service_id,
                        elapsed_ms,
                        is_error=False
                    )
                    
                    # Update instance health
                    if instance_id:
                        await self.discovery_manager.update_instance_health(
                            service_id,
                            instance_id,
                            1.0  # Success score
                        )
                
                # Handle success
                await self._handle_success()
                return result
                
            except Exception as e:
                elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                
                # Record error metrics
                if service_id:
                    self.health_manager.record_request(
                        service_id,
                        elapsed_ms,
                        is_error=True
                    )
                    
                    # Update instance health
                    if instance_id:
                        await self.discovery_manager.update_instance_health(
                            service_id,
                            instance_id,
                            0.0  # Error score
                        )
                
                # Create retry context
                context = RetryContext(
                    error_type=type(e),
                    error_message=str(e),
                    attempt_number=attempt,
                    elapsed_time_ms=elapsed_ms,
                    resource_path=retry_context.get("resource_path", ""),
                    method=retry_context.get("method", ""),
                    priority=retry_context.get("priority"),
                    metadata=retry_context.get("metadata")
                )
                
                # Check if we should retry
                should_retry, delay = await self.retry_manager.should_retry(context)
                
                if should_retry:
                    attempt += 1
                    # Release connection if using discovery
                    if connection:
                        await self.discovery_manager.release_connection(
                            service_id,
                            instance_id,
                            connection
                        )
                        connection = None
                    await asyncio.sleep(delay / 1000)  # Convert ms to seconds
                    continue
                    
                # Handle failure if we shouldn't retry
                await self._handle_failure(e)
                raise
                
            finally:
                # Always release connection if using discovery
                if connection:
                    await self.discovery_manager.release_connection(
                        service_id,
                        instance_id,
                        connection
                    )

    def register_instance(
        self,
        service_id: str,
        instance: ServiceInstance
    ) -> None:
        """Register a service instance"""
        await self.discovery_manager.register_instance(service_id, instance)

    def deregister_instance(
        self,
        service_id: str,
        instance_id: str
    ) -> None:
        """Deregister a service instance"""
        await self.discovery_manager.deregister_instance(service_id, instance_id)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current circuit breaker metrics"""
        metrics = {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
        }
        
        # Add metrics from components
        metrics.update(await self.timeout_manager.get_metrics())
        metrics.update(await self.recovery_manager.get_metrics())
        metrics.update(await self.failure_predictor.get_metrics())
        metrics.update(self.retry_manager.get_retry_metrics())
        
        return metrics