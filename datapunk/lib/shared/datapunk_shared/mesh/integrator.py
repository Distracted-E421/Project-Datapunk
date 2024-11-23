from typing import Dict, Any, Optional
import structlog
from .discovery import ServiceDiscovery
from .circuit_breaker import CircuitBreakerRegistry
from ..utils.retry import RetryConfig

logger = structlog.get_logger(__name__)

class MeshIntegrator:
    """Integrates service mesh components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.discovery = ServiceDiscovery(config)
        self.circuit_breakers = CircuitBreakerRegistry()
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
    
    async def initialize(self):
        """Initialize mesh components"""
        await self.discovery.initialize()
        logger.info("Mesh integrator initialized")
    
    async def call_service(
        self,
        service_name: str,
        operation: str,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Call service with circuit breaker and retry"""
        breaker = self.circuit_breakers.get_or_create(
            f"{service_name}.{operation}",
            failure_threshold=self.config.get('failure_threshold', 0.5),
            reset_timeout=self.config.get('reset_timeout', 30.0)
        )
        
        async def execute_call():
            service = await self.discovery.discover_service(service_name)
            if not service:
                raise ServiceNotFoundError(f"Service {service_name} not found")
                
            # Execute actual service call here
            # This is where you'd implement the specific call logic
            
        return await breaker.call(execute_call)
    
    async def get_mesh_status(self) -> Dict[str, Any]:
        """Get status of mesh components"""
        return {
            "circuit_breakers": self.circuit_breakers.get_all_states(),
            "discovery": await self.discovery.get_status()
        }

class ServiceNotFoundError(Exception):
    """Raised when service cannot be discovered"""
    pass 