from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import time
from enum import Enum

class RateLimitType(Enum):
    LOGIN_ATTEMPT = "login_attempt"
    TOKEN_GENERATION = "token_generation"
    API_CALL = "api_call"

@dataclass
class RateLimit:
    max_attempts: int
    window_seconds: int
    block_duration_seconds: int = 3600  # Default 1 hour block

class RateLimiter:
    def __init__(self):
        self._attempts: Dict[Tuple[str, RateLimitType], list[float]] = {}
        self._blocks: Dict[Tuple[str, RateLimitType], float] = {}
        
        # Default rate limits
        self._limits = {
            RateLimitType.LOGIN_ATTEMPT: RateLimit(5, 300),  # 5 attempts per 5 minutes
            RateLimitType.TOKEN_GENERATION: RateLimit(10, 60),  # 10 tokens per minute
            RateLimitType.API_CALL: RateLimit(100, 60)  # 100 calls per minute
        }
        
    def configure_limit(self, limit_type: RateLimitType, max_attempts: int, 
                       window_seconds: int, block_duration_seconds: int = 3600):
        """Configure rate limit for a specific type."""
        self._limits[limit_type] = RateLimit(
            max_attempts=max_attempts,
            window_seconds=window_seconds,
            block_duration_seconds=block_duration_seconds
        )
        
    def is_blocked(self, identifier: str, limit_type: RateLimitType) -> Tuple[bool, Optional[float]]:
        """Check if an identifier is blocked."""
        key = (identifier, limit_type)
        if key in self._blocks:
            block_end = self._blocks[key]
            if time.time() < block_end:
                return True, block_end - time.time()
            else:
                del self._blocks[key]
                if key in self._attempts:
                    del self._attempts[key]
        return False, None
        
    def record_attempt(self, identifier: str, limit_type: RateLimitType) -> Tuple[bool, Optional[float]]:
        """Record an attempt and check if rate limit is exceeded."""
        key = (identifier, limit_type)
        
        # Check if blocked
        blocked, remaining = self.is_blocked(key[0], key[1])
        if blocked:
            return False, remaining
            
        # Get rate limit config
        limit = self._limits[limit_type]
        current_time = time.time()
        
        # Initialize attempts list if needed
        if key not in self._attempts:
            self._attempts[key] = []
            
        # Remove old attempts outside the window
        window_start = current_time - limit.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > window_start]
        
        # Add new attempt
        self._attempts[key].append(current_time)
        
        # Check if limit exceeded
        if len(self._attempts[key]) > limit.max_attempts:
            # Block the identifier
            block_end = current_time + limit.block_duration_seconds
            self._blocks[key] = block_end
            return False, limit.block_duration_seconds
            
        return True, None
        
    def reset(self, identifier: str, limit_type: RateLimitType):
        """Reset attempts and blocks for an identifier."""
        key = (identifier, limit_type)
        if key in self._attempts:
            del self._attempts[key]
        if key in self._blocks:
            del self._blocks[key]
            
    def get_remaining_attempts(self, identifier: str, limit_type: RateLimitType) -> int:
        """Get number of remaining attempts allowed."""
        key = (identifier, limit_type)
        
        # Check if blocked
        if key in self._blocks:
            return 0
            
        # Get rate limit config
        limit = self._limits[limit_type]
        
        # Get current attempts within window
        current_time = time.time()
        window_start = current_time - limit.window_seconds
        current_attempts = len([
            t for t in self._attempts.get(key, [])
            if t > window_start
        ])
        
        return max(0, limit.max_attempts - current_attempts) 