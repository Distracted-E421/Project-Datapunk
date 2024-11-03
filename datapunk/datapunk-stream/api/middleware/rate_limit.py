from fastapi import Request, HTTPException
import time
from typing import Dict, Tuple
from core.config import get_settings
import redis

settings = get_settings()

class RateLimiter:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.rate_limit = settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # 1 minute window

    async def check_rate_limit(self, request: Request):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        
        # Get current timestamp
        current = int(time.time())
        window_start = current - self.window
        
        pipe = self.redis_client.pipeline()
        
        # Remove old requests
        pipe.zremrangebyscore(key, 0, window_start)
        # Add new request
        pipe.zadd(key, {str(current): current})
        # Count requests in window
        pipe.zcount(key, window_start, current)
        # Set expiry on the key
        pipe.expire(key, self.window)
        
        _, _, request_count, _ = pipe.execute()
        
        if request_count > self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )

rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    await rate_limiter.check_rate_limit(request)
    response = await call_next(request)
    return response