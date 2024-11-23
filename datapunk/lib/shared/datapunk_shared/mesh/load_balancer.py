from typing import Dict, Any, List, Optional
import random
import time
import structlog
from prometheus_client import Counter, Gauge, Histogram
from ..utils.retry import RetryConfig

logger = structlog.get_logger(__name__)

class LoadBalancerMetrics:
    """Metrics for load balancer monitoring"""
    def __init__(self, name: str):
        self.requests = Counter(
            f'load_balancer_requests_total_{name}',
            'Total number of load balanced requests',
            ['service', 'instance']
        )
        self.active_instances = Gauge(
            f'load_balancer_active_instances_{name}',
            'Number of active instances',
            ['service']
        )
        self.response_time = Histogram(
            f'load_balancer_response_time_{name}',
            'Response time for load balanced requests',
            ['service', 'instance']
        )
        self.errors = Counter(
            f'load_balancer_errors_total_{name}',
            'Number of load balancer errors',
            ['service', 'instance', 'error_type']
        )

class ServiceInstance:
    """Represents a service instance with health metrics"""
    def __init__(self, id: str, host: str, port: int):
        self.id = id
        self.host = host
        self.port = port
        self.healthy = True
        self.last_check = time.time()
        self.error_count = 0
        self.success_count = 0
        self.response_times: List[float] = []
        self.max_response_times = 100  # Keep last 100 response times

    def update_health(self, healthy: bool, response_time: Optional[float] = None):
        """Update instance health metrics"""
        self.healthy = healthy
        self.last_check = time.time()
        
        if response_time is not None:
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_times:
                self.response_times.pop(0)

    def get_average_response_time(self) -> float:
        """Get average response time"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)

class LoadBalancer:
    """Load balancer implementation with multiple strategies"""
    
    def __init__(
        self,
        name: str,
        strategy: str = "round_robin",
        health_check_interval: float = 30.0
    ):
        self.name = name
        self.strategy = strategy
        self.health_check_interval = health_check_interval
        self.instances: Dict[str, ServiceInstance] = {}
        self.current_index = 0
        self.metrics = LoadBalancerMetrics(name)
        self.retry_config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=15.0
        )
    
    def add_instance(self, id: str, host: str, port: int):
        """Add service instance"""
        self.instances[id] = ServiceInstance(id, host, port)
        self.metrics.active_instances.labels(service=self.name).inc()
        logger.info(f"Added instance {id} to load balancer")
    
    def remove_instance(self, id: str):
        """Remove service instance"""
        if id in self.instances:
            del self.instances[id]
            self.metrics.active_instances.labels(service=self.name).dec()
            logger.info(f"Removed instance {id} from load balancer")
    
    def get_next_instance(self) -> Optional[ServiceInstance]:
        """Get next instance based on selected strategy"""
        healthy_instances = [
            inst for inst in self.instances.values()
            if inst.healthy
        ]
        
        if not healthy_instances:
            return None
            
        if self.strategy == "round_robin":
            instance = healthy_instances[self.current_index % len(healthy_instances)]
            self.current_index += 1
            return instance
            
        elif self.strategy == "least_connections":
            return min(
                healthy_instances,
                key=lambda x: x.success_count - x.error_count
            )
            
        elif self.strategy == "response_time":
            return min(
                healthy_instances,
                key=lambda x: x.get_average_response_time()
            )
            
        else:  # random
            return random.choice(healthy_instances)
    
    def record_request(
        self,
        instance_id: str,
        success: bool,
        response_time: Optional[float] = None
    ):
        """Record request metrics"""
        instance = self.instances.get(instance_id)
        if not instance:
            return
            
        if success:
            instance.success_count += 1
            self.metrics.requests.labels(
                service=self.name,
                instance=instance_id
            ).inc()
            
            if response_time is not None:
                self.metrics.response_time.labels(
                    service=self.name,
                    instance=instance_id
                ).observe(response_time)
                
        else:
            instance.error_count += 1
            self.metrics.errors.labels(
                service=self.name,
                instance=instance_id,
                error_type="request_failed"
            ).inc()
    
    def update_instance_health(
        self,
        instance_id: str,
        healthy: bool,
        response_time: Optional[float] = None
    ):
        """Update instance health status"""
        instance = self.instances.get(instance_id)
        if instance:
            instance.update_health(healthy, response_time)
            if not healthy:
                self.metrics.errors.labels(
                    service=self.name,
                    instance=instance_id,
                    error_type="health_check_failed"
                ).inc()
                
            logger.info(
                f"Updated instance health",
                instance=instance_id,
                healthy=healthy,
                response_time=response_time
            ) 