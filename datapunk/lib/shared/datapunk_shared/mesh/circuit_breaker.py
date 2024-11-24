from enum import Enum
from typing import Callable, Any, Optional
import time
import asyncio
import structlog
from functools import wraps
from ..tracing import trace_method

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"     # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 half_open_max_calls: int = 3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.half_open_calls = 0
        
        self.logger = logger.bind(component="circuit_breaker")
    
    @trace_method("can_execute")
    def can_execute(self) -> bool:
        """Check if the circuit allows execution."""
        current_time = time.time()
        
        with self.tracer.start_span("check_circuit_state") as span:
            span.set_attribute("current_state", self.state.value)
            span.set_attribute("failure_count", self.failure_count)
            
            if self.state == CircuitState.OPEN:
                time_since_failure = current_time - self.last_failure_time
                span.set_attribute("time_since_failure", time_since_failure)
                
                if time_since_failure > self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                    self.logger.info("circuit_half_open")
                    span.add_event("circuit_half_open")
                else:
                    return False
                    
            if self.state == CircuitState.HALF_OPEN:
                span.set_attribute("half_open_calls", self.half_open_calls)
                return self.half_open_calls < self.half_open_max_calls
                
            return True
    
    @trace_method("record_success")
    def record_success(self):
        """Record a successful execution."""
        with self.tracer.start_span("update_circuit_state") as span:
            span.set_attribute("previous_state", self.state.value)
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
                span.set_attribute("half_open_calls", self.half_open_calls)
                
                if self.half_open_calls >= self.half_open_max_calls:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.logger.info("circuit_closed")
                    span.add_event("circuit_closed")
            
            self.failure_count = 0
            span.set_attribute("new_state", self.state.value)
    
    @trace_method("record_failure")
    def record_failure(self):
        """Record a failed execution."""
        with self.tracer.start_span("update_circuit_state") as span:
            span.set_attribute("previous_state", self.state.value)
            span.set_attribute("previous_failure_count", self.failure_count)
            
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN or \
               self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                self.logger.warning("circuit_opened")
                span.add_event("circuit_opened")
            
            span.set_attribute("new_state", self.state.value)
            span.set_attribute("new_failure_count", self.failure_count)

def circuit_breaker(breaker: CircuitBreaker):
    """Decorator for circuit breaker pattern."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not breaker.can_execute():
                raise Exception("Circuit breaker is open")
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        return wrapper
    return decorator
    