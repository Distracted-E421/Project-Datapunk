from typing import Dict, List, Optional, Any
import structlog
import aiohttp
import asyncio
import psutil
import os
import socket
import ssl
import redis
import aiokafka
from datetime import datetime
from .health_check_types import BaseHealthCheck, HealthCheckResult, HealthStatus

logger = structlog.get_logger()

"""
Extended Health Checks for Datapunk Service Mesh

This module provides specialized health checks for:
- Kafka cluster and consumer health
- Elasticsearch cluster status
- Redis cluster operations
- Network connectivity and latency

These checks enable deep health monitoring of critical
infrastructure components beyond basic connectivity.

TODO: Add MongoDB cluster health check
TODO: Implement custom check aggregation
FIXME: Improve timeout handling for slow responses
"""

class KafkaHealthCheck(BaseHealthCheck):
    """
    Kafka connectivity and consumer lag monitoring.
    
    Checks:
    - Topic existence
    - Consumer group status
    - Partition lag
    - Connection health
    
    NOTE: High lag may indicate processing issues
    TODO: Add producer health metrics
    """
    
    def __init__(self,
                 bootstrap_servers: str,
                 topic: str,
                 group_id: str,
                 timeout: float = 5.0):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.group_id = group_id
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """
        Check Kafka health and consumer lag.
        
        Health determination:
        1. Verify topic exists
        2. Check partition assignment
        3. Calculate consumer lag
        4. Evaluate overall health
        
        NOTE: Returns DEGRADED if lag exceeds 1000
        FIXME: Add configurable lag thresholds
        """
        try:
            consumer = aiokafka.AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id
            )
            
            await consumer.start()
            try:
                # Get consumer lag
                partitions = await consumer.partitions_for_topic(self.topic)
                if not partitions:
                    return HealthCheckResult(
                        status=HealthStatus.UNHEALTHY,
                        message="Topic not found",
                        details={"topic": self.topic}
                    )
                
                total_lag = 0
                for partition in partitions:
                    position = await consumer.position(
                        aiokafka.TopicPartition(self.topic, partition)
                    )
                    committed = await consumer.committed(
                        aiokafka.TopicPartition(self.topic, partition)
                    )
                    if committed:
                        total_lag += position - committed
                
                status = HealthStatus.HEALTHY if total_lag < 1000 else HealthStatus.DEGRADED
                return HealthCheckResult(
                    status=status,
                    message="Kafka operational",
                    details={
                        "consumer_lag": total_lag,
                        "partitions": len(partitions)
                    }
                )
                
            finally:
                await consumer.stop()
                
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Kafka check failed: {str(e)}"
            )

class ElasticsearchHealthCheck(BaseHealthCheck):
    """
    Elasticsearch cluster health monitoring.
    
    Evaluates:
    - Cluster state (green/yellow/red)
    - Node availability
    - Shard distribution
    - Cluster operations
    
    NOTE: Yellow status common in single-node setups
    TODO: Add index-level health checks
    """
    
    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """
        Check Elasticsearch cluster health.
        
        Status mapping:
        green -> HEALTHY: Fully operational
        yellow -> DEGRADED: Reduced redundancy
        red -> UNHEALTHY: Data unavailability
        
        NOTE: Includes shard allocation details
        FIXME: Add timeout for cluster state calls
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/_cluster/health",
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        return HealthCheckResult(
                            status=HealthStatus.UNHEALTHY,
                            message=f"Elasticsearch returned {response.status}"
                        )
                    
                    data = await response.json()
                    status_map = {
                        "green": HealthStatus.HEALTHY,
                        "yellow": HealthStatus.DEGRADED,
                        "red": HealthStatus.UNHEALTHY
                    }
                    
                    return HealthCheckResult(
                        status=status_map[data["status"]],
                        message=f"Elasticsearch cluster {data['status']}",
                        details={
                            "nodes": data["number_of_nodes"],
                            "data_nodes": data["number_of_data_nodes"],
                            "active_shards": data["active_shards"],
                            "relocating_shards": data["relocating_shards"]
                        }
                    )
                    
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Elasticsearch check failed: {str(e)}"
            )

class RedisClusterHealthCheck(BaseHealthCheck):
    """
    Redis cluster health monitoring.
    
    Monitors:
    - Cluster state
    - Node availability
    - Slot distribution
    - Memory usage
    
    NOTE: Requires cluster mode configuration
    TODO: Add keyspace monitoring
    """
    
    def __init__(self, nodes: List[Dict[str, Any]], timeout: float = 5.0):
        self.nodes = nodes
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """
        Check Redis cluster health.
        
        Health criteria:
        1. Cluster state verification
        2. Node failure detection
        3. Slot assignment check
        4. Resource utilization
        
        NOTE: DEGRADED on partial node failures
        FIXME: Improve memory usage calculation
        """
        try:
            client = redis.RedisCluster(
                startup_nodes=self.nodes,
                decode_responses=True
            )
            
            # Check cluster info
            cluster_info = client.cluster_info()
            cluster_state = cluster_info["cluster_state"]
            
            if cluster_state != "ok":
                return HealthCheckResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"Cluster state: {cluster_state}",
                    details=cluster_info
                )
            
            # Check node health
            nodes = client.cluster_nodes()
            node_count = len(nodes)
            failed_nodes = sum(1 for node in nodes if node["flags"]["fail"])
            
            if failed_nodes > 0:
                status = HealthStatus.DEGRADED
                message = f"{failed_nodes} failed nodes"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis cluster operational"
            
            return HealthCheckResult(
                status=status,
                message=message,
                details={
                    "total_nodes": node_count,
                    "failed_nodes": failed_nodes,
                    "cluster_size_bytes": cluster_info["cluster_size"],
                    "total_slots_assigned": cluster_info["cluster_slots_assigned"]
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                message=f"Redis cluster check failed: {str(e)}"
            )

class NetworkHealthCheck(BaseHealthCheck):
    """
    Network connectivity and latency monitoring.
    
    Measures:
    - Connection success
    - Round-trip time
    - Error patterns
    - Latency distribution
    
    Best for:
    - Cross-region services
    - Critical dependencies
    - Performance monitoring
    
    NOTE: Consider network conditions in results
    TODO: Add path MTU discovery
    """
    
    def __init__(self,
                 targets: List[Dict[str, str]],
                 timeout: float = 5.0,
                 latency_threshold: float = 0.5):
        self.targets = targets
        self.timeout = timeout
        self.latency_threshold = latency_threshold
    
    async def check(self) -> HealthCheckResult:
        """
        Check network connectivity and latency.
        
        Health determination:
        1. Test all targets
        2. Measure latencies
        3. Detect failures
        4. Calculate averages
        
        Status rules:
        - HEALTHY: All targets reachable, low latency
        - DEGRADED: Some failures or high latency
        - UNHEALTHY: Critical target failures
        
        NOTE: Latency threshold affects status
        FIXME: Add connection pooling
        """
        results = {}
        total_latency = 0
        failed = 0
        
        for target in self.targets:
            try:
                start_time = datetime.utcnow()
                reader, writer = await asyncio.open_connection(
                    target["host"],
                    target["port"]
                )
                latency = (datetime.utcnow() - start_time).total_seconds()
                writer.close()
                await writer.wait_closed()
                
                results[target["name"]] = {
                    "latency": latency,
                    "status": "ok"
                }
                total_latency += latency
                
            except Exception as e:
                results[target["name"]] = {
                    "status": "failed",
                    "error": str(e)
                }
                failed += 1
        
        avg_latency = total_latency / (len(self.targets) - failed) if failed < len(self.targets) else 0
        
        if failed > 0:
            status = HealthStatus.DEGRADED if failed < len(self.targets) else HealthStatus.UNHEALTHY
            message = f"{failed} targets unreachable"
        elif avg_latency > self.latency_threshold:
            status = HealthStatus.DEGRADED
            message = f"High average latency: {avg_latency:.3f}s"
        else:
            status = HealthStatus.HEALTHY
            message = "Network operational"
        
        return HealthCheckResult(
            status=status,
            message=message,
            details={
                "results": results,
                "average_latency": avg_latency,
                "failed_targets": failed
            }
        ) 