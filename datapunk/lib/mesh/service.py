from typing import Dict, Optional, List
import consul
import structlog
from dataclasses import dataclass
import socket
import json
from .load_balancer.load_balancer import LoadBalancer, LoadBalancerStrategy, ServiceInstance
from datetime import timedelta
from ..tracing import trace_method

logger = structlog.get_logger()

"""
Service management module for Datapunk's service mesh.

This module provides:
- Service registration and deregistration with Consul
- Load balancing integration for service instances
- Health check setup and monitoring
- Caching strategies for service discovery

Part of the service mesh layer, ensuring efficient service communication
and availability through dynamic registration and load balancing.
"""

@dataclass
class ServiceConfig:
    """
    Configuration for a service instance in the mesh.
    
    Encapsulates all necessary details for registering a service with Consul,
    including metadata and health check parameters.
    
    NOTE: Ensure tags and meta are correctly set for service discovery
    """
    name: str
    host: str
    port: int
    tags: List[str]
    meta: Dict[str, str]

class ServiceMesh:
    """
    Manages service lifecycle within the service mesh.
    
    Integrates with Consul for service registration and health monitoring,
    and with a load balancer for distributing requests across healthy instances.
    Also supports caching for efficient service discovery.
    
    TODO: Consider adding support for additional service registries
    """
    
    def __init__(self, consul_host: str = "consul", consul_port: int = 8500,
                 load_balancer_strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN,
                 redis_client = None):
        """
        Initialize the service mesh component.
        
        Sets up connections to Consul, load balancer, and optional Redis cache.
        Configures distributed retry coordination and cache patterns.
        
        NOTE: Default Consul host and port are for local development; update for production
        """
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.cache = redis_client
        self.logger = logger.bind(service="mesh")
        self.load_balancer = LoadBalancer(strategy=load_balancer_strategy)
        
        # Initialize coordination components
        self.retry_coordinator = DistributedRetryCoordinator(
            redis_client,
            DistributedRetryConfig()
        )
        
        # Initialize cache patterns
        self.cache_pattern = CachePattern(redis_client)
        
    def register_service(self, config: ServiceConfig) -> bool:
        """
        Register a service with Consul and load balancer.
        
        Handles the full lifecycle of service registration, including:
        - Consul registration with health checks
        - Load balancer instance registration
        - Logging and error handling
        
        Returns True if registration is successful, False otherwise.
        
        FIXME: Handle edge cases where Consul registration partially succeeds
        """
        try:
            service_id = f"{config.name}-{config.host}-{config.port}"
            
            # Create service definition
            service_def = {
                "Name": config.name,
                "ID": service_id,
                "Address": config.host,
                "Port": config.port,
                "Tags": config.tags,
                "Meta": config.meta,
                "Check": {
                    "HTTP": f"http://{config.host}:{config.port}/health",
                    "Interval": "30s",
                    "Timeout": "10s",
                    "DeregisterCriticalServiceAfter": "1m"
                }
            }
            
            # Register with Consul
            self.consul.agent.service.register(**service_def)
            
            # Register with load balancer
            instance = ServiceInstance(
                id=service_id,
                address=config.host,
                port=config.port,
                weight=int(config.meta.get("weight", "1"))
            )
            self.load_balancer.register_instance(config.name, instance)
            
            self.logger.info("service_registered", 
                           service_name=config.name,
                           service_id=service_id)
            return True
            
        except Exception as e:
            self.logger.error("service_registration_failed",
                            service_name=config.name,
                            error=str(e))
            return False
    
    def deregister_service(self, service_id: str) -> bool:
        """
        Deregister a service from Consul.
        
        Ensures that all associated resources, such as load balancer instances,
        are properly cleaned up upon deregistration.
        
        Returns True if deregistration is successful, False otherwise.
        
        NOTE: Ensure service_id is correctly formatted and registered
        """
        try:
            self.consul.agent.service.deregister(service_id)
            self.logger.info("service_deregistered", service_id=service_id)
            return True
        except Exception as e:
            self.logger.error("service_deregistration_failed",
                            service_id=service_id,
                            error=str(e))
            return False
    
    def get_service(self, service_name: str) -> Optional[Dict]:
        """
        Get service details from Consul.
        
        Queries Consul for service details and returns the first available instance.
        Returns None if no healthy instances are found.
        
        TODO: Optimize for large-scale deployments
        """
        try:
            _, services = self.consul.health.service(service_name, passing=True)
            if services:
                return services[0]
            return None
        except Exception as e:
            self.logger.error("service_lookup_failed",
                            service_name=service_name,
                            error=str(e))
            return None

    def get_healthy_services(self, service_name: str) -> List[Dict]:
        """
        Get all healthy instances of a service.
        
        Queries Consul for all healthy instances of the specified service.
        Returns an empty list if no healthy instances are found.
        
        NOTE: Consider caching results for frequently queried services
        """
        try:
            _, services = self.consul.health.service(service_name, passing=True)
            return services
        except Exception as e:
            self.logger.error("healthy_services_lookup_failed",
                            service_name=service_name,
                            error=str(e))
            return [] 

    @trace_method("get_service_instance")
    async def get_service_instance(self, service_name: str) -> Optional[Dict]:
        """
        Get next available service instance using load balancer.
        
        Utilizes the load balancer to retrieve the next available instance
        for the specified service, ensuring balanced request distribution.
        
        Returns a dictionary with instance details if found, None otherwise.
        
        FIXME: Handle cases where no instances are available
        """
        with self.tracer.start_span("load_balancer_get_instance") as span:
            instance = self.load_balancer.get_next_instance(service_name)
            if not instance:
                span.set_status(Status(StatusCode.ERROR))
                return None
                
            span.set_attribute("instance_id", instance.id)
            span.set_attribute("instance_address", instance.address)
            span.set_attribute("instance_port", instance.port)
            
            self.load_balancer.record_request_start(instance)
            return {
                "id": instance.id,
                "address": instance.address,
                "port": instance.port
            }

    async def release_service_instance(self, service_name: str, instance_id: str):
        """
        Release service instance after request completion.
        
        Updates the load balancer to reflect the completion of a request
        for the specified service instance.
        
        NOTE: Ensure instance_id is valid and registered
        """
        instances = self.load_balancer.instances.get(service_name, [])
        for instance in instances:
            if instance.id == instance_id:
                self.load_balancer.record_request_complete(instance)
                break 

    @trace_method("get_service_with_cache")
    async def get_service_with_cache(self, service_name: str) -> Optional[Dict]:
        """
        Get service details with caching.
        
        Attempts to retrieve service details from cache before querying Consul.
        Utilizes a read-through cache pattern to optimize service discovery.
        
        Returns cached service details if available, None otherwise.
        
        TODO: Implement cache invalidation strategy
        """
        with self.tracer.start_span("cache_lookup") as span:
            # Try cache first
            cached = await self.cache_pattern.read_through(
                key=f"service:{service_name}",
                fetch_func=lambda: self.consul.health.service(service_name, passing=True),
                ttl=timedelta(seconds=30)
            )
            
            span.set_attribute("cache_hit", cached is not None)
            return cached