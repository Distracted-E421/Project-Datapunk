from datapunk_shared.utils.retry import with_retry, RetryConfig
from typing import Dict, Any
import asyncio
import aiohttp

class StreamService:
    def __init__(self):
        self.retry_config = RetryConfig(
            max_attempts=5,
            base_delay=0.1,
            max_delay=2.0,
            exponential_base=2
        )
    
    @with_retry(
        exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
        config=RetryConfig(max_attempts=3)
    )
    async def process_stream(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming stream data with retry logic"""
        try:
            # Process stream data
            processed_data = await self._transform_data(data)
            
            # Forward to Lake service
            return await self._forward_to_lake(processed_data)
            
        except Exception as e:
            self.logger.error(f"Stream processing failed: {str(e)}")
            raise
    
    @with_retry(exceptions=(Exception,))
    async def _transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data with retry logic"""
        # Data transformation logic
        pass
    
    @with_retry(
        exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
        config=RetryConfig(max_attempts=5)
    )
    async def _forward_to_lake(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Forward data to Lake service with retry logic"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{self.lake_host}:{self.lake_port}/ingest",
                json=data
            ) as response:
                return await response.json() 