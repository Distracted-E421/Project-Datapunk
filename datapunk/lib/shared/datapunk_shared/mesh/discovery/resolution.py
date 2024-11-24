from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta
import random
from ..routing.balancer import LoadBalancer, ServiceInstance, BalancingStrategy
from .registry import ServiceRegistration
import consul
import json

@dataclass
class ResolutionConfig:
    """Configuration for service resolution"""
    consul_host: str = "localhost"
    consul_port: int = 8500
    cache_ttl: int = 30  # seconds
    watch_services: bool = True
    watch_interval: int = 10  # seconds
    balancing_strategy: BalancingStrategy = BalancingStrategy.ROUND_ROBIN

class ServiceResolutionError(Exception):
    """Custom exception for service resolution errors"""
    pass

class ServiceResolver:
    """Resolves service locations and manages service discovery"""
    def __init__(self, config: ResolutionConfig):
        self.config = config
        self.consul = consul.Consul(
            host=config.consul_host,
            port=config.port
        )
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._balancers: Dict[str, LoadBalancer] = {}
        self._watchers: Dict[str, asyncio.Task] = {}
        
    async def start(self):
        """Start the resolver and service watchers"""
        if self.config.watch_services:
            await self._start_service_watchers()
    
    async def stop(self):
        """Stop all service watchers"""
        for watcher in self._watchers.values():
            watcher.cancel()
        self._watchers.clear()
        
    async def resolve(self, service_name: str) -> ServiceInstance:
        """Resolve a service to a specific instance"""
        try:
            # Check cache first
            if self._is_cache_valid(service_name):
                return await self._get_from_cache(service_name)
            
            # Get service instances from Consul
            instances = await self._get_service_instances(service_name)
            if not instances:
                raise ServiceResolutionError(f"No instances found for service: {service_name}")
            
            # Update cache
            self._update_cache(service_name, instances)
            
            # Get instance using load balancer
            return await self._get_balanced_instance(service_name, instances)
            
        except Exception as e:
            raise ServiceResolutionError(f"Failed to resolve service {service_name}: {str(e)}")
    
    async def _get_service_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get service instances from Consul"""
        try:
            index, services = await self.consul.health.service(
                service_name,
                passing=True
            )
            
            instances = []
            for service in services:
                instance = ServiceInstance(
                    id=service["Service"]["ID"],
                    host=service["Service"]["Address"],
                    port=service["Service"]["Port"],
                    weight=service["Service"].get("Weights", {}).get("Passing", 100),
                    healthy=True,
                    metadata=service["Service"].get("Meta", {})
                )
                instances.append(instance)
                
            return instances
            
        except Exception as e:
            raise ServiceResolutionError(f"Failed to get instances from Consul: {str(e)}")
    
    def _is_cache_valid(self, service_name: str) -> bool:
        """Check if cached service data is still valid"""
        if service_name not in self._cache_timestamps:
            return False
            
        age = datetime.utcnow() - self._cache_timestamps[service_name]
        return age.total_seconds() < self.config.cache_ttl
    
    async def _get_from_cache(self, service_name: str) -> ServiceInstance:
        """Get service instance from cache using load balancer"""
        if service_name not in self._cache:
            raise ServiceResolutionError(f"Service {service_name} not found in cache")
            
        instances = self._cache[service_name]
        return await self._get_balanced_instance(service_name, instances)
    
    def _update_cache(self, service_name: str, instances: List[ServiceInstance]):
        """Update the service cache"""
        self._cache[service_name] = instances
        self._cache_timestamps[service_name] = datetime.utcnow()
    
    async def _get_balanced_instance(
        self,
        service_name: str,
        instances: List[ServiceInstance]
    ) -> ServiceInstance:
        """Get an instance using the configured load balancing strategy"""
        if service_name not in self._balancers:
            self._balancers[service_name] = LoadBalancer(
                strategy=self.config.balancing_strategy
            )
            
        balancer = self._balancers[service_name]
        
        # Update balancer with current instances
        balancer.instances = instances
        
        return balancer.get_next_instance()
    
    async def _start_service_watchers(self):
        """Start watchers for registered services"""
        try:
            index, services = await self.consul.catalog.services()
            
            for service_name in services:
                if service_name not in self._watchers:
                    self._watchers[service_name] = asyncio.create_task(
                        self._watch_service(service_name)
                    )
                    
        except Exception as e:
            raise ServiceResolutionError(f"Failed to start service watchers: {str(e)}")
    
    async def _watch_service(self, service_name: str):
        """Watch for changes in a service's instances"""
        while True:
            try:
                # Get current instances
                instances = await self._get_service_instances(service_name)
                
                # Update cache
                self._update_cache(service_name, instances)
                
                # Wait before next check
                await asyncio.sleep(self.config.watch_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error watching service {service_name}: {str(e)}")
                await asyncio.sleep(self.config.watch_interval)

    async def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health status for all instances of a service"""
        try:
            instances = await self._get_service_instances(service_name)
            
            return {
                "service_name": service_name,
                "healthy_count": len([i for i in instances if i.healthy]),
                "total_count": len(instances),
                "instances": [
                    {
                        "id": i.id,
                        "host": i.host,
                        "port": i.port,
                        "healthy": i.healthy,
                        "metadata": i.metadata
                    }
                    for i in instances
                ]
            }
            
        except Exception as e:
            raise ServiceResolutionError(f"Failed to get service health: {str(e)}") 