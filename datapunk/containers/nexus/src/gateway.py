from datapunk_shared.utils.retry import with_retry, RetryConfig
import aiohttp
import asyncio

class NexusGateway:
    def __init__(self):
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=0.1,
            max_delay=1.0
        )
    
    @with_retry(
        exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
        config=RetryConfig(max_attempts=3)
    )
    async def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route requests to appropriate services with retry logic"""
        service = self._determine_service(request)
        return await self._forward_request(service, request)
    
    @with_retry(exceptions=(Exception,))
    async def _forward_request(
        self,
        service: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Forward request to service with retry logic"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{service}/api",
                json=request
            ) as response:
                return await response.json() 