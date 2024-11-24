import os
from fastapi import FastAPI
from datapunk_shared.mesh.service import ServiceMesh, ServiceConfig
from datapunk_shared.mesh.circuit_breaker import CircuitBreaker, circuit_breaker
import aiohttp
import asyncio
from datapunk_shared.mesh.retry import with_retry, RetryConfig

app = FastAPI()
service_mesh = ServiceMesh(
    consul_host=os.getenv("CONSUL_HOST", "consul")
)

# Circuit breakers for dependencies
lake_circuit = CircuitBreaker()
stream_circuit = CircuitBreaker()

# Configure retry policies
default_retry_config = RetryConfig(
    max_attempts=3,
    initial_delay=0.1,
    max_delay=2.0,
    jitter=True
)

@app.on_event("startup")
async def startup_event():
    # Register with service mesh
    config = ServiceConfig(
        name="nexus",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        tags=["gateway", "api"],
        meta={
            "version": os.getenv("SERVICE_VERSION", "0.1.0"),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )
    
    service_mesh.register_service(config)

@app.on_event("shutdown")
async def shutdown_event():
    service_mesh.deregister_service(f"nexus-{os.getenv('HOST', '0.0.0.0')}-{os.getenv('PORT', 8000)}")

@circuit_breaker(lake_circuit)
@with_retry(
    retry_config=default_retry_config,
    retry_on=(aiohttp.ClientError, asyncio.TimeoutError),
    service_name="lake"
)
async def call_lake_service(path: str):
    """Call Lake service with circuit breaker, load balancing, and retries."""
    instance = await service_mesh.get_service_instance("lake")
    if not instance:
        raise Exception("Lake service not available")
    
    try:
        url = f"http://{instance['address']}:{instance['port']}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    finally:
        await service_mesh.release_service_instance("lake", instance["id"])

@circuit_breaker(stream_circuit)
@with_retry(
    retry_config=default_retry_config,
    retry_on=(aiohttp.ClientError, asyncio.TimeoutError),
    service_name="stream"
)
async def call_stream_service(path: str):
    """Call Stream service with circuit breaker, load balancing, and retries."""
    instance = await service_mesh.get_service_instance("stream")
    if not instance:
        raise Exception("Stream service not available")
    
    try:
        url = f"http://{instance['address']}:{instance['port']}{path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()
    finally:
        await service_mesh.release_service_instance("stream", instance["id"])