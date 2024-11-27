"""
Nexus Gateway Core Module

This module implements the central routing and request handling logic for the Datapunk platform.
It acts as the primary interface between external clients and internal services, implementing
retry logic and circuit breaking patterns for resilient service communication.

NOTE: This gateway is a critical component in the service mesh architecture,
handling routing decisions and maintaining service reliability.
"""

from datapunk_shared.utils.retry import with_retry, RetryConfig
import aiohttp
import asyncio
from typing import Dict, Any

class NexusGateway:
    """
    Core gateway service implementing intelligent request routing and resilient
    communication patterns within the service mesh architecture.
    
    NOTE: Uses exponential backoff for retries to prevent cascading failures
    TODO: Implement circuit breaker pattern for service failure isolation
    """
    def __init__(self):
        # Configure retry behavior with exponential backoff
        # Values chosen based on observed service recovery patterns
        self.retry_config = RetryConfig(
            max_attempts=3,  # Balance between reliability and user experience
            base_delay=0.1,  # Initial retry delay
            max_delay=1.0    # Cap to prevent excessive waiting
        )
    
    @with_retry(
        exceptions=(aiohttp.ClientError, asyncio.TimeoutError),
        config=RetryConfig(max_attempts=3)
    )
    async def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Routes requests to appropriate services based on content and type.
        Implements retry logic for resilient service communication.
        
        NOTE: Timeout errors are retried to handle temporary service unavailability
        FIXME: Consider implementing request priority queuing for high-load scenarios
        """
        service = self._determine_service(request)
        return await self._forward_request(service, request)
    
    @with_retry(exceptions=(Exception,))
    async def _forward_request(
        self,
        service: str,
        request: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Forwards requests to internal services with retry capability.
        Uses aiohttp for non-blocking HTTP communication.
        
        NOTE: Generic exception handling ensures all errors are retried
        TODO: Add service-specific timeout configurations
        TODO: Implement request tracing for observability
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{service}/api",
                json=request
            ) as response:
                return await response.json() 