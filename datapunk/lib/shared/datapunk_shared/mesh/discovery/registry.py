from typing import Dict, Optional
import consul
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ServiceRegistration:
    service_id: str
    name: str
    address: str
    port: int
    tags: list[str]
    metadata: Dict[str, str]
    registered_at: datetime

class ServiceRegistry:
    def __init__(self, consul_host: str, consul_port: int):
        self.consul = consul.Consul(host=consul_host, port=consul_port)
        
    async def register_service(self, registration: ServiceRegistration) -> bool:
        try:
            return self.consul.agent.service.register(
                name=registration.name,
                service_id=registration.service_id,
                address=registration.address,
                port=registration.port,
                tags=registration.tags,
                meta=registration.metadata
            )
        except Exception as e:
            # Log error and potentially retry
            return False 