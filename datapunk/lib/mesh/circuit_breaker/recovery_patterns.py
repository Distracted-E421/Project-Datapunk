"""
Service Mesh Circuit Breaker Recovery Patterns

Implements advanced recovery and fallback mechanisms for the circuit breaker
system. Provides configurable patterns for graceful degradation and service
recovery in failure scenarios.

Key features:
- Multiple recovery strategies
- Fallback chain management
- Cache-based degraded operations
- Alternative service routing
- Partial functionality support

See sys-arch.mmd Reliability/CircuitBreakerRecovery for implementation details.
"""

from typing import Optional, Dict, Any, List, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
import asyncio
import structlog
from datetime import datetime, timedelta
from .circuit_breaker_strategies import CircuitState
from ...cache import CacheClient
from ...monitoring import MetricsClient

T = TypeVar('T')
logger = structlog.get_logger()

class FallbackResult(Generic[T]):
    """Result from fallback chain execution"""
    def __init__(self, 
                 value: Optional[T] = None,
                 error: Optional[Exception] = None,
                 fallback_used: bool = False,
                 degraded: bool = False):
        self.value = value
        self.error = error
        self.fallback_used = fallback_used
        self.degraded = degraded

class FallbackChain(Generic[T]):
    """
    Chain of fallback handlers for graceful degradation.
    
    Features:
    - Multiple fallback levels
    - Cached responses
    - Degraded operation modes
    - Error propagation control
    """
    
    def __init__(self, cache: CacheClient, metrics: MetricsClient):
        self.cache = cache
        self.metrics = metrics
        self.fallbacks: List[Callable[..., T]] = []
        self.logger = logger.bind(component="fallback_chain")
        
    def add_fallback(self, handler: Callable[..., T]):
        """Add fallback handler to chain"""
        self.fallbacks.append(handler)
        
    async def execute(self, 
                     primary: Callable[..., T],
                     *args,
                     cache_key: Optional[str] = None,
                     **kwargs) -> FallbackResult[T]:
        """
        Execute request with fallback chain.
        
        Process:
        1. Try primary function
        2. Check cache on failure
        3. Try fallbacks in sequence
        4. Return best available result
        """
        try:
            # Try primary function
            result = await primary(*args, **kwargs)
            
            # Cache successful result
            if cache_key:
                await self.cache.set(cache_key, result, ttl=300)
                
            return FallbackResult(value=result)
            
        except Exception as primary_error:
            self.logger.warning("primary_execution_failed",
                              error=str(primary_error))
            
            # Try cache first
            if cache_key:
                try:
                    cached = await self.cache.get(cache_key)
                    if cached is not None:
                        await self.metrics.increment(
                            "circuit_breaker_cache_fallback_used"
                        )
                        return FallbackResult(
                            value=cached,
                            fallback_used=True,
                            degraded=True
                        )
                except Exception as cache_error:
                    self.logger.warning("cache_fallback_failed",
                                      error=str(cache_error))
                    
            # Try fallbacks in sequence
            for handler in self.fallbacks:
                try:
                    result = await handler(*args, **kwargs)
                    await self.metrics.increment(
                        "circuit_breaker_fallback_used"
                    )
                    return FallbackResult(
                        value=result,
                        fallback_used=True,
                        degraded=True
                    )
                except Exception as fallback_error:
                    self.logger.warning("fallback_execution_failed",
                                      error=str(fallback_error))
                    
            # No fallbacks succeeded
            return FallbackResult(error=primary_error)

class RecoveryPattern(ABC):
    """Base class for circuit breaker recovery patterns"""
    
    @abstractmethod
    async def should_attempt_recovery(self, 
                                    failure_count: int,
                                    last_failure_time: datetime) -> bool:
        """Determine if recovery should be attempted"""
        pass
        
    @abstractmethod
    async def handle_success(self, success_count: int) -> bool:
        """Handle successful request during recovery"""
        pass
        
    @abstractmethod
    async def handle_failure(self, failure_count: int) -> None:
        """Handle failed request during recovery"""
        pass

class ExponentialBackoffPattern(RecoveryPattern):
    """
    Implements exponential backoff for recovery attempts.
    
    Features:
    - Increasing delays between attempts
    - Maximum retry limit
    - Jitter for distributed systems
    """
    
    def __init__(self,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 max_retries: int = 5):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.attempt = 0
        
    async def should_attempt_recovery(self,
                                    failure_count: int,
                                    last_failure_time: datetime) -> bool:
        """Check if enough time has passed for next attempt"""
        if self.attempt >= self.max_retries:
            return False
            
        delay = min(
            self.max_delay,
            self.base_delay * (2 ** self.attempt)
        )
        
        # Add jitter
        import random
        delay *= (0.5 + random.random())
        
        time_since_failure = (datetime.utcnow() - last_failure_time).total_seconds()
        return time_since_failure >= delay
        
    async def handle_success(self, success_count: int) -> bool:
        """Reset attempt counter on success"""
        if success_count >= 3:  # Require stable success
            self.attempt = 0
            return True
        return False
        
    async def handle_failure(self, failure_count: int) -> None:
        """Increment attempt counter on failure"""
        self.attempt += 1

class PartialRecoveryPattern(RecoveryPattern):
    """
    Implements partial service recovery with feature flags.
    
    Features:
    - Gradual feature enablement
    - Critical path prioritization
    - Load shedding during recovery
    """
    
    def __init__(self,
                 feature_priorities: Dict[str, int],
                 metrics: MetricsClient):
        self.feature_priorities = feature_priorities
        self.metrics = metrics
        self.enabled_features: Set[str] = set()
        self.stability_window = 60  # seconds
        self.last_enable_time = datetime.utcnow()
        
    async def should_attempt_recovery(self,
                                    failure_count: int,
                                    last_failure_time: datetime) -> bool:
        """Check if ready to enable more features"""
        if not self.enabled_features:
            return True  # Always try to enable highest priority
            
        time_since_enable = (datetime.utcnow() - self.last_enable_time).total_seconds()
        return time_since_enable >= self.stability_window
        
    async def handle_success(self, success_count: int) -> bool:
        """Enable next feature on stable success"""
        if success_count < 5:  # Require more stability for features
            return False
            
        # Find highest priority disabled feature
        available = set(self.feature_priorities.keys())
        disabled = available - self.enabled_features
        
        if not disabled:
            return len(self.enabled_features) == len(available)
            
        next_feature = max(
            disabled,
            key=lambda f: self.feature_priorities[f]
        )
        
        self.enabled_features.add(next_feature)
        self.last_enable_time = datetime.utcnow()
        
        await self.metrics.increment(
            "circuit_breaker_feature_enabled",
            {"feature": next_feature}
        )
        
        return False  # Continue recovery until all features enabled
        
    async def handle_failure(self, failure_count: int) -> None:
        """Disable lower priority features on failure"""
        if not self.enabled_features:
            return
            
        # Find lowest priority enabled feature
        to_disable = min(
            self.enabled_features,
            key=lambda f: self.feature_priorities[f]
        )
        
        self.enabled_features.remove(to_disable)
        await self.metrics.increment(
            "circuit_breaker_feature_disabled",
            {"feature": to_disable}
        )

class AdaptiveRecoveryPattern(RecoveryPattern):
    """
    Implements adaptive recovery based on system metrics.
    
    Features:
    - Load-aware recovery
    - Performance monitoring
    - Resource utilization checks
    - Automatic rate limiting
    """
    
    def __init__(self,
                 metrics: MetricsClient,
                 target_latency_ms: float = 100.0,
                 max_cpu_percent: float = 80.0,
                 max_memory_percent: float = 80.0):
        self.metrics = metrics
        self.target_latency_ms = target_latency_ms
        self.max_cpu_percent = max_cpu_percent
        self.max_memory_percent = max_memory_percent
        self.current_rate = 0.1  # Start at 10%
        
    async def should_attempt_recovery(self,
                                    failure_count: int,
                                    last_failure_time: datetime) -> bool:
        """Check if system metrics allow recovery attempt"""
        try:
            # Get current metrics
            latency = await self.metrics.get_gauge(
                "service_latency_ms"
            )
            cpu = await self.metrics.get_gauge(
                "system_cpu_percent"
            )
            memory = await self.metrics.get_gauge(
                "system_memory_percent"
            )
            
            # Check if metrics are within limits
            return (
                latency <= self.target_latency_ms and
                cpu <= self.max_cpu_percent and
                memory <= self.max_memory_percent
            )
            
        except Exception as e:
            logger.error("metric_check_failed", error=str(e))
            return False
            
    async def handle_success(self, success_count: int) -> bool:
        """Increase rate if metrics stay healthy"""
        if success_count < 10:  # Require more stability
            return False
            
        # Increase rate gradually
        self.current_rate = min(1.0, self.current_rate + 0.1)
        
        await self.metrics.gauge(
            "circuit_breaker_recovery_rate",
            self.current_rate
        )
        
        return self.current_rate >= 1.0
        
    async def handle_failure(self, failure_count: int) -> None:
        """Reduce rate on failure"""
        self.current_rate = max(0.1, self.current_rate - 0.2)
        
        await self.metrics.gauge(
            "circuit_breaker_recovery_rate",
            self.current_rate
        ) 