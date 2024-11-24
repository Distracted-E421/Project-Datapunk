# Service Discovery Standards

## Purpose

Define standardized patterns for service registration, discovery, and health monitoring across the Datapunk platform.

## Context

Service discovery is critical for dynamic service-to-service communication, load balancing, and system resilience.

## Design/Details

### 1. Service Registration

```yaml
service_registration:
  metadata:
    required_fields:
      - service_name
      - service_version
      - service_type
      - environment
      - instance_id
      
    optional_fields:
      - region
      - zone
      - deployment_id
      - capabilities
      
  health_check:
    types:
      - http
      - tcp
      - script
      - grpc
    interval: "30s"
    timeout: "10s"
    deregister_after: "1m"
```

### 2. Service Discovery Patterns

```yaml
discovery_patterns:
  direct:
    type: "service_lookup"
    caching: true
    cache_ttl: "30s"
    
  dns:
    type: "dns_lookup"
    format: "service.datacenter.consul"
    
  template:
    type: "consul_template"
    refresh: "1m"
    
  watch:
    type: "service_watch"
    handlers:
      - "config_update"
      - "load_balancer_update"
      - "metrics_update"
```

### 3. Service Mesh Integration

```yaml
mesh_integration:
  consul:
    connect: true
    intentions: true
    mesh_gateway: true
    
  service_defaults:
    protocol: "http"
    connect_timeout: "5s"
    mesh_gateway_mode: "local"
    
  proxy_defaults:
    local_connect_timeout: "1s"
    local_request_timeout: "10s"
    local_idle_timeout: "1h"
```

## Implementation Patterns

### 1. Service Registration for Python

```python
from dataclasses import dataclass
from typing import Dict, List, Optional
import uuid

@dataclass
class ServiceDefinition:
    """Service registration definition."""
    name: str
    version: str
    type: str
    environment: str
    instance_id: str = str(uuid.uuid4())
    tags: List[str] = None
    meta: Dict[str, str] = None
    
    def to_consul_service(self) -> Dict:
        """Convert to Consul service definition."""
        return {
            "Name": self.name,
            "ID": f"{self.name}-{self.instance_id}",
            "Tags": self.tags or [],
            "Meta": {
                "version": self.version,
                "type": self.type,
                "environment": self.environment,
                **(self.meta or {})
            },
            "Check": {
                "HTTP": f"http://localhost:{self.port}/health",
                "Interval": "30s",
                "Timeout": "10s",
                "DeregisterCriticalServiceAfter": "1m"
            }
        }
```

### 2. Service Discovery

```python
from typing import Optional, List
import structlog
import aiohttp
from cachetools import TTLCache

logger = structlog.get_logger()

class ServiceDiscovery:
    def __init__(self, consul_client):
        self.consul = consul_client
        self.cache = TTLCache(maxsize=100, ttl=30)
        self.logger = logger.bind(component="service_discovery")
    
    async def get_service(self, 
                         name: str,
                         dc: Optional[str] = None,
                         tag: Optional[str] = None) -> Optional[Dict]:
        """Get service details with caching."""
        cache_key = f"{name}:{dc}:{tag}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Query Consul
            _, services = await self.consul.health.service(
                name,
                dc=dc,
                tag=tag,
                passing=True
            )
            
            if services:
                self.cache[cache_key] = services[0]
                return services[0]
                
            return None
            
        except Exception as e:
            self.logger.error("service_lookup_failed",
                            service=name,
                            error=str(e))
            return None
    
    async def watch_service(self,
                          name: str,
                          callback: Callable,
                          blocking_timeout: int = 300) -> None:
        """Watch for service changes."""
        index = None
        
        while True:
            try:
                index, services = await self.consul.health.service(
                    name,
                    index=index,
                    wait=f"{blocking_timeout}s",
                    passing=True
                )
                
                await callback(services)
                
            except Exception as e:
                self.logger.error("service_watch_failed",
                                service=name,
                                error=str(e))
                await asyncio.sleep(5)  # Backoff on error
```

### 3. Health Check Integration

```python
from enum import Enum
from typing import Optional, Dict
import asyncio
import aiohttp

class HealthCheckType(Enum):
    HTTP = "http"
    TCP = "tcp"
    SCRIPT = "script"
    GRPC = "grpc"

class HealthCheckDefinition:
    def __init__(self,
                 check_type: HealthCheckType,
                 target: str,
                 interval: str = "30s",
                 timeout: str = "10s"):
        self.type = check_type
        self.target = target
        self.interval = interval
        self.timeout = timeout
    
    def to_consul_check(self) -> Dict:
        """Convert to Consul check definition."""
        check = {
            "Interval": self.interval,
            "Timeout": self.timeout,
            "DeregisterCriticalServiceAfter": "1m"
        }
        
        if self.type == HealthCheckType.HTTP:
            check["HTTP"] = self.target
        elif self.type == HealthCheckType.TCP:
            check["TCP"] = self.target
        elif self.type == HealthCheckType.SCRIPT:
            check["Script"] = self.target
        elif self.type == HealthCheckType.GRPC:
            check["GRPC"] = self.target
            
        return check
```

## Security Considerations

### 1. Access Control

```yaml
access_control:
  acl:
    enabled: true
    default_policy: "deny"
    down_policy: "extend-cache"
    
  tokens:
    agent: "restricted"
    service: "minimal"
    
  policies:
    service_registration:
      service_prefix: ""
      node_prefix: ""
      
    service_discovery:
      service_read: true
      node_read: true
```

### 2. Network Security

```yaml
network_security:
  encryption:
    gossip: true
    rpc: true
    
  verify_incoming: true
  verify_outgoing: true
  verify_server_hostname: true
  
  ca_file: "/etc/consul/ca.pem"
  cert_file: "/etc/consul/cert.pem"
  key_file: "/etc/consul/key.pem"
```

## Monitoring and Metrics

```yaml
monitoring:
  metrics:
    service_health:
      type: "gauge"
      labels: ["service", "instance", "dc"]
      
    discovery_latency:
      type: "histogram"
      labels: ["service", "operation"]
      
    cache_stats:
      type: "counter"
      labels: ["service", "result"]
```

## Known Issues and Mitigations

### 1. Split Brain Prevention

```python
class SplitBrainProtection:
    def __init__(self, min_nodes: int = 3):
        self.min_nodes = min_nodes
    
    async def check_cluster_health(self) -> bool:
        """Check for potential split-brain scenarios."""
        try:
            members = await self.consul.agent.members()
            active_nodes = len([m for m in members if m["Status"] == 1])
            
            return active_nodes >= self.min_nodes
        except Exception as e:
            self.logger.error("cluster_health_check_failed",
                            error=str(e))
            return False
```

### 2. Cache Consistency

```python
class CacheConsistency:
    def __init__(self, ttl: int = 30):
        self.ttl = ttl
        self.last_index = {}
    
    async def validate_cache(self, service: str) -> bool:
        """Validate cache consistency with Consul."""
        try:
            current_index = await self.consul.kv.get(
                f"services/{service}/index"
            )
            
            if current_index != self.last_index.get(service):
                self.cache.pop(service, None)
                self.last_index[service] = current_index
                return False
                
            return True
            
        except Exception:
            return False
```

## Testing Requirements

```yaml
testing:
  integration_tests:
    - service_registration
    - service_discovery
    - health_checks
    - watch_handlers
    
  chaos_tests:
    - node_failure
    - network_partition
    - service_degradation
    
  performance_tests:
    - discovery_latency
    - cache_effectiveness
    - scaling_limits
```
