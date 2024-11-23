from typing import Dict, Any
import aiohttp
from datetime import datetime

async def check_service_health(url: str) -> bool:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{url}/health") as response:
                return response.status == 200
    except Exception:
        return False

async def get_service_metrics() -> Dict[str, Any]:
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'cpu_usage': await get_cpu_metrics(),
        'memory_usage': await get_memory_metrics(),
        'disk_usage': await get_disk_metrics()
    } 