from typing import Dict, Any
import aiohttp
from datetime import datetime

async def check_service_health(url: str) -> bool:
    """Check if a service endpoint is responding correctly
    
    Performs a non-blocking HTTP GET request to a service's health endpoint.
    Used by service mesh for load balancing and circuit breaking decisions.
    
    NOTE: Assumes /health endpoint follows standard health check protocol
    TODO: Add timeout configuration
    FIXME: Add support for custom health check paths
    
    Args:
        url: Base URL of the service to check
        
    Returns:
        bool: True if service is healthy, False otherwise
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health") as response:
                return response.status == 200
    except Exception:
        # NOTE: Any connection error is treated as unhealthy
        return False

async def get_service_metrics() -> Dict[str, Any]:
    """Collect comprehensive service metrics
    
    Gathers system-level metrics for monitoring and alerting.
    Metrics are collected asynchronously to prevent blocking.
    
    NOTE: Metrics collection may impact performance
    TODO: Add configurable metric collection intervals
    
    Returns:
        Dict containing:
            - timestamp: ISO format UTC timestamp
            - cpu_usage: CPU utilization metrics
            - memory_usage: Memory utilization metrics
            - disk_usage: Disk space metrics
    """
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_usage': await get_cpu_metrics(),
        'memory_usage': await get_memory_metrics(),
        'disk_usage': await get_disk_metrics()
    } 