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

class KafkaHealthCheck(BaseHealthCheck):
    """Kafka connectivity and consumer lag health check."""
    
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
        """Check Kafka health and consumer lag."""
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
    """Elasticsearch cluster health check."""
    
    def __init__(self, url: str, timeout: float = 5.0):
        self.url = url
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """Check Elasticsearch cluster health."""
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
    """Redis cluster health check."""
    
    def __init__(self, nodes: List[Dict[str, Any]], timeout: float = 5.0):
        self.nodes = nodes
        self.timeout = timeout
    
    async def check(self) -> HealthCheckResult:
        """Check Redis cluster health."""
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
    """Network connectivity and latency health check."""
    
    def __init__(self,
                 targets: List[Dict[str, str]],
                 timeout: float = 5.0,
                 latency_threshold: float = 0.5):
        self.targets = targets
        self.timeout = timeout
        self.latency_threshold = latency_threshold
    
    async def check(self) -> HealthCheckResult:
        """Check network connectivity and latency."""
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