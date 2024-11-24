from typing import Optional, Dict, List
import structlog
from dataclasses import dataclass
import consul
from .service import ServiceMesh, ServiceConfig
from .load_balancer import LoadBalancer, LoadBalancerStrategy
from .circuit_breaker import CircuitBreaker
from .retry import RetryPolicy, RetryConfig
from .metrics import ServiceMeshMetrics
from ..tracing import TracingManager, TracingConfig, trace_method

logger = structlog.get_logger()

@dataclass
class MeshConfig:
    """Configuration for service mesh."""
    consul_host: str = "consul"
    consul_port: int = 8500
    load_balancer_strategy: LoadBalancerStrategy = LoadBalancerStrategy.ROUND_ROBIN
    retry_config: RetryConfig = RetryConfig()
    circuit_breaker_config: Dict = None
    enable_metrics: bool = True

class DatapunkMesh:
    """Main service mesh implementation combining all mesh components."""
    
    def __init__(self, config: MeshConfig):
        self.config = config
        self.logger = logger.bind(component="mesh")
        
        # Initialize core components
        self.service_mesh = ServiceMesh(
            consul_host=config.consul_host,
            consul_port=config.consul_port,
            load_balancer_strategy=config.load_balancer_strategy
        )
        
        self.load_balancer = self.service_mesh.load_balancer
        self.retry_policy = RetryPolicy(config.retry_config)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize metrics if enabled
        self.metrics = ServiceMeshMetrics() if config.enable_metrics else None
        
        # Initialize tracing
        self.tracing = TracingManager(TracingConfig(
            service_name="service_mesh",
            jaeger_host=config.consul_host  # Assuming same host
        ))
        
    @trace_method("register_service")
    async def register_service(self, config: ServiceConfig) -> bool:
        """Register service with mesh."""
        try:
            # Register with service discovery
            success = self.service_mesh.register_service(config)
            if not success:
                return False
                
            # Initialize circuit breaker for service
            if self.config.circuit_breaker_config:
                self.circuit_breakers[config.name] = CircuitBreaker(
                    **self.config.circuit_breaker_config
                )
                
            # Record metric
            if self.metrics:
                self.metrics.record_registration(config.name)
                
            # Add trace context
            self.tracing.set_attribute("service.name", config.name)
            self.tracing.set_attribute("service.host", config.host)
            self.tracing.set_attribute("service.port", config.port)
            
            return True
            
        except Exception as e:
            self.tracing.record_exception(e)
            raise
            
    @trace_method("call_service")
    async def call_service(self,
                          service_name: str,
                          operation: str,
                          *args,
                          **kwargs) -> Any:
        """Make service call with all mesh features."""
        # Add trace context
        self.tracing.set_attribute("service.name", service_name)
        self.tracing.set_attribute("operation", operation)
        
        try:
            # Get circuit breaker
            circuit_breaker = self.circuit_breakers.get(service_name)
            if circuit_breaker and not circuit_breaker.can_execute():
                self.tracing.add_event("circuit_breaker_open")
                raise Exception(f"Circuit breaker open for {service_name}")
            
            # Get service instance
            with self.tracing.start_span("get_service_instance") as span:
                instance = await self.service_mesh.get_service_instance(service_name)
                if not instance:
                    span.set_status(Status(StatusCode.ERROR))
                    raise Exception(f"No healthy instances for {service_name}")
                span.set_attribute("instance.id", instance["id"])
            
            # Execute with retry
            start_time = time.time()
            with self.tracing.start_span("execute_operation") as span:
                result = await self.retry_policy.execute_with_retry(
                    operation,
                    *args,
                    service_name=service_name,
                    instance=instance,
                    **kwargs
                )
                span.set_attribute("duration", time.time() - start_time)
            
            # Record success
            if self.metrics:
                duration = time.time() - start_time
                self.metrics.record_call_success(
                    service_name,
                    operation,
                    duration
                )
            
            if circuit_breaker:
                circuit_breaker.record_success()
            
            return result
            
        except Exception as e:
            self.tracing.record_exception(e)
            
            # Record failure metrics
            if self.metrics:
                self.metrics.record_call_failure(
                    service_name,
                    operation,
                    str(e)
                )
            
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            raise
            
    async def get_mesh_status(self) -> Dict:
        """Get overall mesh status."""
        services = await self.service_mesh.get_all_services()
        
        status = {
            "services": {},
            "circuit_breakers": {},
            "load_balancer": {
                "strategy": self.config.load_balancer_strategy.value,
                "instance_counts": {
                    name: len(instances)
                    for name, instances in self.load_balancer.instances.items()
                }
            }
        }
        
        # Collect service status
        for service in services:
            name = service["Service"]
            status["services"][name] = {
                "healthy_instances": len(
                    await self.service_mesh.get_healthy_services(name)
                ),
                "circuit_breaker": (
                    self.circuit_breakers[name].state.value
                    if name in self.circuit_breakers
                    else None
                )
            }
            
        return status 