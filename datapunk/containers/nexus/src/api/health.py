from fastapi import APIRouter, Response
from datapunk_shared.monitoring.health import HealthCheck, HealthStatus

router = APIRouter()
health_checker = HealthCheck("nexus")

# Add dependencies to check
health_checker.add_check("redis", "http://redis:6379/health")
health_checker.add_check("postgres", "http://postgres:5432/health")
health_checker.add_check("rabbitmq", "http://rabbitmq:15672/health")

@router.get("/health")
async def health_check(response: Response):
    result = await health_checker.check_health()
    
    # Set response status based on health
    if result["status"] == HealthStatus.UNHEALTHY.value:
        response.status_code = 503
    elif result["status"] == HealthStatus.DEGRADED.value:
        response.status_code = 200  # or 207 for Multi-Status
    else:
        response.status_code = 200
        
    return result 