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

@dataclass
class ServiceConfig:
    name: str
    host: str
    port: int
    tags: List[str]
    meta: Dict[str, str]

class ServiceMesh:
    def __init__(self, 
                 consul_host: str = "consul", 
                 consul_port: int = 8500,
                 load_balancer_strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN,
                 redis_client = None):
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
        """Register service with Consul and load balancer."""
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
        """Deregister service from Consul."""
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
        """Get service details from Consul."""
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
        """Get all healthy instances of a service."""
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
        """Get next available service instance using load balancer."""
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
        """Release service instance after request completion."""
        instances = self.load_balancer.instances.get(service_name, [])
        for instance in instances:
            if instance.id == instance_id:
                self.load_balancer.record_request_complete(instance)
                break 

    @trace_method("get_service_with_cache")
    async def get_service_with_cache(self, service_name: str) -> Optional[Dict]:
        """Get service details with caching."""
        with self.tracer.start_span("cache_lookup") as span:
            # Try cache first
            cached = await self.cache_pattern.read_through(
                key=f"service:{service_name}",
                fetch_func=lambda: self.consul.health.service(service_name, passing=True),
                ttl=timedelta(seconds=30)
            )
            
            span.set_attribute("cache_hit", cached is not None)
            return cached