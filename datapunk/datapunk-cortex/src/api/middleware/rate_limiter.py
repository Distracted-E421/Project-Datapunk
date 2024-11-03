from fastapi import Request, HTTPException
from typing import Dict, Any
import time
import asyncio

class RateLimiter:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tokens: Dict[str, float] = {}
        self.last_update: Dict[str, float] = {}
        
    async def check_rate_limit(self, request: Request):
        user_id = request.headers.get("X-User-ID", "default")
        tier = request.headers.get("X-User-Tier", "default")
        
        limits = self.config[tier]
        current_time = time.time()
        
        if user_id not in self.tokens:
            self.tokens[user_id] = limits["burst_size"]
            self.last_update[user_id] = current_time
            return
            
        # Update tokens
        time_passed = current_time - self.last_update[user_id]
        new_tokens = time_passed * (limits["requests_per_minute"] / 60.0)
        self.tokens[user_id] = min(
            limits["burst_size"],
            self.tokens[user_id] + new_tokens
        )
        
        if self.tokens[user_id] < 1:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
            
        self.tokens[user_id] -= 1
        self.last_update[user_id] = current_time
