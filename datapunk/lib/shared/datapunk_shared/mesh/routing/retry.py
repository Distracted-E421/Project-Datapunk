from typing import Callable, Any, Optional
import asyncio
from datetime import datetime, timedelta

class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        attempt = 0
        last_exception = None
        
        while attempt < self.max_attempts:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                last_exception = e
                
                if attempt == self.max_attempts:
                    raise last_exception
                
                delay = min(
                    self.initial_delay * (self.exponential_base ** attempt),
                    self.max_delay
                )
                
                if self.jitter:
                    delay = delay * (0.5 + asyncio.random())
                
                await asyncio.sleep(delay) 