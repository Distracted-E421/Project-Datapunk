"""
Nexus Service Configuration Module

This module configures the Nexus Gateway's service mesh integration, implementing
circuit breakers and retry policies for resilient communication with Lake and Stream
services. It handles service registration, health monitoring, and load balancing.

NOTE: This is a critical component for maintaining system stability during service
failures or high load conditions.
"""

import os
from fastapi import FastAPI
from datapunk_shared.mesh.service import ServiceMesh, ServiceConfig
from datapunk_shared.mesh.circuit_breaker import CircuitBreaker, circuit_breaker
import aiohttp
import asyncio
from datapunk_shared.mesh.retry import with_retry, RetryConfig

app = FastAPI()
service_mesh = ServiceMesh(
    consul_host=os.getenv("CONSUL_HOST", "consul")  # Service discovery endpoint
)

# Circuit breakers prevent cascade failures by failing fast when services are unhealthy
# TODO: Add configuration for circuit breaker thresholds based on service patterns
lake_circuit = CircuitBreaker()  # Protects Lake service communication
stream_circuit = CircuitBreaker()  # Protects Stream service communication

# Retry policies ensure transient failures don't affect service availability
# NOTE: Values chosen based on observed recovery patterns in production
default_retry_config = RetryConfig(
    max_attempts=3,    # Balance between reliability and user experience
    initial_delay=0.1, # Start with quick retries
    max_delay=2.0,     # Cap delay to maintain responsiveness
    jitter=True        # Prevent thundering herd problem
)

@app.on_event("startup")
async def startup_event():
    """
    Registers Nexus service with the service mesh during startup.
    Enables service discovery and health monitoring.
    
    NOTE: Service metadata influences load balancing decisions
    TODO: Add more detailed service capabilities to metadata
    """
    config = ServiceConfig(
        name="nexus",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        tags=["gateway", "api"],  # Used for service discovery filtering
        meta={
            "version": os.getenv("SERVICE_VERSION", "0.1.0"),
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )
    
    service_mesh.register_service(config)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Gracefully removes service from mesh during shutdown.
    Prevents routing of requests to terminating instance.
    """
    service_mesh.deregister_service(f"nexus-{os.getenv('HOST', '0.0.0.0')}-{os.getenv('PORT', 8000)}")

@circuit_breaker(lake_circuit)
@with_retry(
    retry_config=default_retry_config,
    retry_on=(aiohttp.ClientError, asyncio.TimeoutError),
    service_name="lake"
)
async def call_lake_service(path: str):
    """
    Makes resilient calls to Lake service with circuit breaking and retries.
    
    NOTE: Order of decorators matters - circuit breaker should be outside retry
    FIXME: Consider implementing request timeout configuration
    """
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
    """
    Makes resilient calls to Stream service with circuit breaking and retries.
    
    NOTE: Instance release ensures proper load balancing
    TODO: Add metrics collection for service call patterns
    """
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