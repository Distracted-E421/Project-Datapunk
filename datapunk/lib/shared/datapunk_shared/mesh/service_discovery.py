"""
Service discovery and registration module for Datapunk's service mesh.

This module handles:
- Service registration and deregistration with Consul
- Health check setup and monitoring
- Load balancer integration for service instances
- Metrics collection for service operations

Part of the service mesh layer, ensuring reliable service communication
and availability through dynamic discovery and health monitoring.
"""

from typing import Dict, List, Optional, Any
import asyncio
import consul
import logging
from dataclasses import dataclass
from .health.health_checks import HealthChecker, HealthCheckType
from .load_balancer.load_balancer import LoadBalancer, ServiceInstance
from .discovery_metrics import DiscoveryMetrics

@dataclass
class ServiceRegistration:
    """
    Data class representing a service registration configuration.
    
    Encapsulates all necessary details for registering a service with Consul,
    including health check parameters and load balancing weight.
    
    NOTE: Ensure health_check_path is accessible and returns appropriate status
    """
    name: str
    address: str
    port: int
    tags: List[str]
    meta: Dict[str, str]
    health_check_path: str = "/health"
    health_check_interval: str = "10s"
    weight: int = 1

class ServiceDiscovery:
    """
    Manages service registration, health checks, and discovery.
    
    Integrates with Consul for service registration and health monitoring,
    and with a load balancer for distributing requests across healthy instances.
    
    TODO: Consider adding support for additional service registries
    """
    
    def __init__(
        self,
        consul_host: str = "localhost",
        consul_port: int = 8500,
        health_checker: Optional[HealthChecker] = None,
        load_balancer: Optional[LoadBalancer] = None,
        metrics_enabled: bool = True
    ):
        """
        Initialize the service discovery component.
        
        Sets up connections to Consul, health checker, and load balancer.
        Optionally enables metrics collection for monitoring service operations.
        
        NOTE: Default Consul host and port are for local development; update for production
        """
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        self.health_checker = health_checker or HealthChecker()
        self.load_balancer = load_balancer or LoadBalancer()
        self.logger = logging.getLogger(__name__)
        self.metrics = DiscoveryMetrics() if metrics_enabled else None
        self._watch_tasks: Dict[str, asyncio.Task] = {}
        self._registered_services: Dict[str, ServiceRegistration] = {}

    async def register_service(self, service: ServiceRegistration) -> bool:
        """
        Register a service with Consul and set up health checks.
        
        Handles the full lifecycle of service registration, including:
        - Consul registration with health checks
        - Load balancer instance registration
        - Health monitoring task setup
        
        Returns True if registration is successful, False otherwise.
        
        FIXME: Handle edge cases where Consul registration partially succeeds
        """
        try:
            # Register with Consul
            success = self.consul.agent.service.register(
                name=service.name,
                service_id=f"{service.name}-{service.port}",
                address=service.address,
                port=service.port,
                tags=service.tags,
                meta=service.meta,
                check={
                    "http": f"http://{service.address}:{service.port}{service.health_check_path}",
                    "interval": service.health_check_interval
                }
            )

            if success:
                # Store registration
                self._registered_services[service.name] = service

                # Set up health checker
                await self.health_checker.add_check(
                    service_id=f"{service.name}-{service.port}",
                    check_type=HealthCheckType.HTTP,
                    target=f"http://{service.address}:{service.port}{service.health_check_path}"
                )

                # Register with load balancer
                instance = ServiceInstance(
                    id=f"{service.name}-{service.port}",
                    address=service.address,
                    port=service.port,
                    weight=service.weight
                )
                await self.load_balancer.register_instance(service.name, instance)

                # Start watching service health
                self._watch_tasks[service.name] = asyncio.create_task(
                    self._watch_service_health(service.name)
                )

                if self.metrics:
                    await self.metrics.record_service_registration(service.name)

                self.logger.info(f"Successfully registered service: {service.name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to register service {service.name}: {str(e)}")
            return False

    async def deregister_service(self, service_name: str) -> bool:
        """
        Deregister a service from Consul and clean up resources.
        
        Ensures that all associated resources, such as health checks and
        load balancer instances, are properly cleaned up upon deregistration.
        
        Returns True if deregistration is successful, False otherwise.
        
        NOTE: Ensure service_name is correctly formatted and registered
        """
        try:
            if service_name in self._registered_services:
                service = self._registered_services[service_name]
                service_id = f"{service.name}-{service.port}"

                # Deregister from Consul
                success = self.consul.agent.service.deregister(service_id)

                if success:
                    # Clean up health checker
                    await self.health_checker.remove_check(service_id)

                    # Remove from load balancer
                    await self.load_balancer.remove_instance(service_name, service_id)

                    # Stop watching service
                    if service_name in self._watch_tasks:
                        self._watch_tasks[service_name].cancel()
                        del self._watch_tasks[service_name]

                    # Clean up registration
                    del self._registered_services[service_name]

                    if self.metrics:
                        await self.metrics.record_service_deregistration(service_name)

                    self.logger.info(f"Successfully deregistered service: {service_name}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to deregister service {service_name}: {str(e)}")
            return False

    async def discover_service(self, service_name: str) -> Optional[ServiceInstance]:
        """
        Discover and return an instance of the requested service.
        
        Attempts to retrieve a healthy service instance from the load balancer.
        If not available, queries Consul for available instances and updates
        the load balancer accordingly.
        
        Returns a ServiceInstance if found, None otherwise.
        
        TODO: Optimize discovery for large-scale deployments
        """
        try:
            # First try load balancer
            instance = await self.load_balancer.get_instance(service_name)
            if instance:
                return instance

            # If not found, query Consul
            _, services = self.consul.health.service(service_name, passing=True)
            
            if services:
                for service in services:
                    instance = ServiceInstance(
                        id=service["Service"]["ID"],
                        address=service["Service"]["Address"],
                        port=service["Service"]["Port"]
                    )
                    await self.load_balancer.register_instance(service_name, instance)

                if self.metrics:
                    await self.metrics.record_service_discovery(service_name)

                return await self.load_balancer.get_instance(service_name)

            return None

        except Exception as e:
            self.logger.error(f"Failed to discover service {service_name}: {str(e)}")
            return None

    async def _watch_service_health(self, service_name: str) -> None:
        """
        Watch Consul for health status changes and update load balancer.
        
        Continuously monitors the health status of registered services and
        updates the load balancer with the latest health information.
        
        NOTE: Consider adding exponential backoff for error handling
        """
        index = None
        while True:
            try:
                index, services = self.consul.health.service(
                    service_name,
                    index=index,
                    wait="30s"
                )

                for service in services:
                    service_id = service["Service"]["ID"]
                    is_passing = all(check["Status"] == "passing" for check in service["Checks"])
                    
                    await self.load_balancer.update_instance_health(
                        service_name,
                        service_id,
                        1.0 if is_passing else 0.0
                    )

                    if self.metrics:
                        await self.metrics.record_health_status(
                            service_name,
                            service_id,
                            is_passing
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error watching service {service_name}: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying 