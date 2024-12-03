"""
Context-Aware Retry Management

Implements intelligent retry strategies based on request context,
error types, and system state.
"""

from typing import Dict, List, Optional, Any, Type, Set, Tuple
from enum import Enum
import structlog
from datetime import datetime, timedelta
from dataclasses import dataclass
import random
import math
from collections import defaultdict

logger = structlog.get_logger()

class RetryOutcome(Enum):
    """Possible outcomes of retry decision"""
    RETRY = "retry"
    FAIL_FAST = "fail_fast"
    BACKOFF = "backoff"
    REDIRECT = "redirect"

class ErrorCategory(Enum):
    """Categories of errors for retry decisions"""
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    INVALID_REQUEST = "invalid_request"
    INTERNAL_ERROR = "internal_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN = "unknown"

@dataclass
class RetryContext:
    """Context information for retry decisions"""
    error_type: Type[Exception]
    error_message: str
    attempt_number: int
    elapsed_time_ms: float
    resource_path: str
    method: str
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class RetryPolicy:
    """Configuration for retry behavior"""
    def __init__(self,
                 max_attempts: int = 3,
                 base_delay_ms: float = 100.0,
                 max_delay_ms: float = 5000.0,
                 jitter_factor: float = 0.2,
                 timeout_factor: float = 1.5):
        self.max_attempts = max_attempts
        self.base_delay_ms = base_delay_ms
        self.max_delay_ms = max_delay_ms
        self.jitter_factor = jitter_factor
        self.timeout_factor = timeout_factor
        
        # Error category configurations
        self.retryable_categories = {
            ErrorCategory.TIMEOUT,
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.RESOURCE_EXHAUSTED,
            ErrorCategory.NETWORK_ERROR
        }
        
        # Method-specific configurations
        self.method_configs = {
            "GET": {"max_attempts": 5},
            "POST": {"max_attempts": 2},
            "PUT": {"max_attempts": 2},
            "DELETE": {"max_attempts": 1}
        }
        
        # Priority-specific configurations
        self.priority_configs = {
            "HIGH": {"max_attempts": 5},
            "MEDIUM": {"max_attempts": 3},
            "LOW": {"max_attempts": 1}
        }

class ErrorClassifier:
    """Classifies errors into categories for retry decisions"""
    
    def __init__(self):
        # Error type mappings
        self.error_mappings = {
            TimeoutError: ErrorCategory.TIMEOUT,
            ConnectionError: ErrorCategory.NETWORK_ERROR,
            ValueError: ErrorCategory.INVALID_REQUEST,
            RuntimeError: ErrorCategory.INTERNAL_ERROR
        }
        
        # Error message patterns
        self.message_patterns = {
            "rate limit": ErrorCategory.RATE_LIMIT,
            "too many requests": ErrorCategory.RATE_LIMIT,
            "resource exhausted": ErrorCategory.RESOURCE_EXHAUSTED,
            "out of memory": ErrorCategory.RESOURCE_EXHAUSTED,
            "connection refused": ErrorCategory.NETWORK_ERROR,
            "invalid": ErrorCategory.INVALID_REQUEST
        }
        
    def classify(self, error: Exception) -> ErrorCategory:
        """Classify an error into a category"""
        # Check error type mapping
        for error_type, category in self.error_mappings.items():
            if isinstance(error, error_type):
                return category
                
        # Check error message patterns
        error_message = str(error).lower()
        for pattern, category in self.message_patterns.items():
            if pattern in error_message:
                return category
                
        return ErrorCategory.UNKNOWN

class RetryStrategy:
    """Base class for retry strategies"""
    
    def should_retry(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> RetryOutcome:
        """Determine if request should be retried"""
        raise NotImplementedError

    def get_delay_ms(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> float:
        """Calculate delay before next retry"""
        raise NotImplementedError

class ExponentialBackoffStrategy(RetryStrategy):
    """Implements exponential backoff with jitter"""
    
    def should_retry(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> RetryOutcome:
        """Determine if request should be retried"""
        # Check attempt limit
        method_config = policy.method_configs.get(
            context.method,
            {"max_attempts": policy.max_attempts}
        )
        
        if context.priority:
            priority_config = policy.priority_configs.get(
                context.priority,
                {"max_attempts": policy.max_attempts}
            )
            max_attempts = max(
                method_config["max_attempts"],
                priority_config["max_attempts"]
            )
        else:
            max_attempts = method_config["max_attempts"]
            
        if context.attempt_number >= max_attempts:
            return RetryOutcome.FAIL_FAST
            
        return RetryOutcome.RETRY
        
    def get_delay_ms(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> float:
        """Calculate delay before next retry"""
        # Calculate base exponential delay
        delay = min(
            policy.base_delay_ms * (2 ** (context.attempt_number - 1)),
            policy.max_delay_ms
        )
        
        # Add jitter
        jitter = random.uniform(
            -policy.jitter_factor * delay,
            policy.jitter_factor * delay
        )
        
        return delay + jitter

class AdaptiveRetryStrategy(RetryStrategy):
    """Adapts retry behavior based on error patterns"""
    
    def __init__(self):
        self.error_classifier = ErrorClassifier()
        self.error_history: List[Tuple[datetime, ErrorCategory]] = []
        self.error_window = timedelta(minutes=5)
        
    def should_retry(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> RetryOutcome:
        """Determine if request should be retried"""
        # Classify error
        error_category = self.error_classifier.classify(
            context.error_type(context.error_message)
        )
        
        # Update error history
        now = datetime.utcnow()
        self.error_history.append((now, error_category))
        
        # Clean old entries
        cutoff = now - self.error_window
        self.error_history = [
            (t, c) for t, c in self.error_history
            if t >= cutoff
        ]
        
        # Check if error is retryable
        if error_category not in policy.retryable_categories:
            return RetryOutcome.FAIL_FAST
            
        # Check for error patterns
        if self._detect_rate_limiting():
            return RetryOutcome.BACKOFF
            
        if self._detect_resource_exhaustion():
            return RetryOutcome.REDIRECT
            
        return RetryOutcome.RETRY
        
    def get_delay_ms(self,
                    context: RetryContext,
                    policy: RetryPolicy) -> float:
        """Calculate delay before next retry"""
        error_category = self.error_classifier.classify(
            context.error_type(context.error_message)
        )
        
        # Adjust delay based on error category
        if error_category == ErrorCategory.RATE_LIMIT:
            # Increase delay for rate limiting
            base_delay = policy.base_delay_ms * 2
        elif error_category == ErrorCategory.RESOURCE_EXHAUSTED:
            # Add more delay for resource issues
            base_delay = policy.base_delay_ms * 3
        else:
            base_delay = policy.base_delay_ms
            
        # Calculate exponential delay
        delay = min(
            base_delay * (2 ** (context.attempt_number - 1)),
            policy.max_delay_ms
        )
        
        # Add jitter
        jitter = random.uniform(
            -policy.jitter_factor * delay,
            policy.jitter_factor * delay
        )
        
        return delay + jitter
        
    def _detect_rate_limiting(self) -> bool:
        """Check for rate limiting pattern"""
        rate_limit_count = sum(
            1 for _, c in self.error_history
            if c == ErrorCategory.RATE_LIMIT
        )
        return rate_limit_count >= 3
        
    def _detect_resource_exhaustion(self) -> bool:
        """Check for resource exhaustion pattern"""
        resource_count = sum(
            1 for _, c in self.error_history
            if c == ErrorCategory.RESOURCE_EXHAUSTED
        )
        return resource_count >= 2

class ContextRetryManager:
    """
    Manages context-aware retry decisions.
    
    Features:
    - Multiple retry strategies
    - Error classification
    - Pattern detection
    - Adaptive delays
    - Priority handling
    """
    
    def __init__(self,
                 policy: Optional[RetryPolicy] = None,
                 strategy: Optional[RetryStrategy] = None,
                 metrics_client = None):
        self.policy = policy or RetryPolicy()
        self.strategy = strategy or AdaptiveRetryStrategy()
        self.metrics = metrics_client
        self.logger = logger.bind(component="context_retry")
        
    async def should_retry(self,
                         context: RetryContext) -> Tuple[bool, float]:
        """
        Determine if request should be retried.
        
        Returns:
            Tuple[bool, float]: (should_retry, delay_ms)
        """
        outcome = self.strategy.should_retry(context, self.policy)
        
        if self.metrics:
            await self.metrics.increment(
                "circuit_breaker_retry_decision",
                {
                    "outcome": outcome.value,
                    "attempt": str(context.attempt_number)
                }
            )
            
        if outcome == RetryOutcome.RETRY:
            delay = self.strategy.get_delay_ms(context, self.policy)
            
            if self.metrics:
                await self.metrics.gauge(
                    "circuit_breaker_retry_delay",
                    delay
                )
                
            return True, delay
            
        return False, 0.0
        
    def get_retry_metrics(self) -> Dict[str, Any]:
        """Get current retry metrics"""
        if not isinstance(self.strategy, AdaptiveRetryStrategy):
            return {}
            
        # Calculate error distribution
        error_counts = defaultdict(int)
        for _, category in self.strategy.error_history:
            error_counts[category.value] += 1
            
        return {
            "error_counts": dict(error_counts),
            "total_errors": len(self.strategy.error_history)
        } 