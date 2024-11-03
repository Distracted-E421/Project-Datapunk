from datetime import datetime, timezone
from typing import Dict
import redis
from core.config import get_settings

settings = get_settings()

class QuotaManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.daily_quota = settings.PLAY_STORE_DAILY_QUOTA
        
    async def check_quota(self, api_name: str, cost: int = 1) -> bool:
        """Check if operation is within quota limits"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        key = f"quota:{api_name}:{today}"
        
        pipe = self.redis_client.pipeline()
        pipe.incr(key, cost)
        pipe.expire(key, 86400)  # 24 hours
        current_usage = pipe.execute()[0]
        
        return current_usage <= self.daily_quota

    async def get_quota_usage(self, api_name: str) -> Dict[str, int]:
        """Get current quota usage"""
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
        key = f"quota:{api_name}:{today}"
        
        usage = self.redis_client.get(key) or 0
        return {
            'used': int(usage),
            'remaining': self.daily_quota - int(usage),
            'total': self.daily_quota
        } 