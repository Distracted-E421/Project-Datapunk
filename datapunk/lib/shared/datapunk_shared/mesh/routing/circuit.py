from enum import Enum
from typing import Callable, Any
import asyncio
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 3
    ):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = None
        self.half_open_max_calls = half_open_max_calls
        self.half_open_calls = 0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        if not self._can_execute():
            raise Exception("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            self._handle_failure()
            raise e

    def _can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if (datetime.now() - self.last_failure_time) > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
            
        # HALF_OPEN state
        return self.half_open_calls < self.half_open_max_calls 