from typing import Dict, Any, Set, Optional
from datetime import datetime
import threading

class PartitionNode:
    """Represents a node in the distributed partition cluster"""
    
    def __init__(self, node_id: str,
                 capacity: Dict[str, Any],
                 status: str = 'active'):
        self.node_id = node_id
        self.capacity = capacity
        self.status = status
        self.partitions: Set[str] = set()
        self.metrics: Dict[str, Any] = {
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'disk_usage': 0.0,
            'network_io': 0.0,
            'iops': 0.0
        }
        self.last_heartbeat = datetime.now()
        self.lock = threading.Lock()
        
    def add_partition(self, partition_id: str) -> bool:
        """Add a partition to this node"""
        with self.lock:
            if partition_id in self.partitions:
                return False
            self.partitions.add(partition_id)
            return True
            
    def remove_partition(self, partition_id: str) -> bool:
        """Remove a partition from this node"""
        with self.lock:
            if partition_id not in self.partitions:
                return False
            self.partitions.remove(partition_id)
            return True
            
    def has_partition(self, partition_id: str) -> bool:
        """Check if node has a specific partition"""
        return partition_id in self.partitions
        
    def get_partitions(self) -> Set[str]:
        """Get all partitions assigned to this node"""
        return self.partitions.copy()
        
    def update_metrics(self, metrics: Dict[str, Any]):
        """Update node metrics"""
        with self.lock:
            self.metrics.update(metrics)
            
    def get_load(self) -> float:
        """Get current load factor of the node"""
        with self.lock:
            # Calculate load based on multiple factors
            cpu_weight = 0.3
            memory_weight = 0.3
            disk_weight = 0.2
            partition_weight = 0.2
            
            cpu_load = self.metrics['cpu_usage'] / 100.0
            memory_load = self.metrics['memory_usage'] / 100.0
            disk_load = self.metrics['disk_usage'] / 100.0
            partition_load = len(self.partitions) / max(1, self.capacity.get('max_partitions', 1000))
            
            return (cpu_load * cpu_weight +
                   memory_load * memory_weight +
                   disk_load * disk_weight +
                   partition_load * partition_weight)
                   
    def update_heartbeat(self):
        """Update last heartbeat time"""
        with self.lock:
            self.last_heartbeat = datetime.now()
            
    def is_healthy(self) -> bool:
        """Check if node is healthy based on metrics and heartbeat"""
        with self.lock:
            # Check heartbeat
            heartbeat_age = (datetime.now() - self.last_heartbeat).total_seconds()
            if heartbeat_age > 30:  # 30 seconds threshold
                return False
                
            # Check metrics
            if (self.metrics['cpu_usage'] > 90 or  # CPU threshold
                self.metrics['memory_usage'] > 90 or  # Memory threshold
                self.metrics['disk_usage'] > 90):  # Disk threshold
                return False
                
            return self.status == 'active'
            
    def get_capacity_score(self) -> float:
        """Calculate capacity score for node selection"""
        with self.lock:
            # Normalize and weight different capacity aspects
            storage_score = min(1.0, self.capacity.get('storage', 0) / 1000.0)  # TB
            memory_score = min(1.0, self.capacity.get('memory', 0) / 256.0)  # GB
            cpu_score = min(1.0, self.capacity.get('cpu_cores', 0) / 32.0)
            network_score = min(1.0, self.capacity.get('network_bandwidth', 0) / 10.0)  # Gbps
            
            # Weighted sum
            return (storage_score * 0.4 +
                   memory_score * 0.3 +
                   cpu_score * 0.2 +
                   network_score * 0.1)
                   
    def can_accept_partition(self, partition_size: Optional[int] = None) -> bool:
        """Check if node can accept a new partition"""
        with self.lock:
            # Check status
            if self.status != 'active':
                return False
                
            # Check partition count
            if len(self.partitions) >= self.capacity.get('max_partitions', 1000):
                return False
                
            # Check resources
            if (self.metrics['cpu_usage'] > 80 or
                self.metrics['memory_usage'] > 80 or
                self.metrics['disk_usage'] > 80):
                return False
                
            # Check specific partition size if provided
            if partition_size:
                available_storage = (
                    self.capacity.get('storage', 0) * 
                    (1 - self.metrics['disk_usage'] / 100.0)
                )
                if partition_size > available_storage:
                    return False
                    
            return True
            
    def get_resource_usage(self) -> Dict[str, float]:
        """Get current resource usage metrics"""
        with self.lock:
            return {
                'cpu': self.metrics['cpu_usage'],
                'memory': self.metrics['memory_usage'],
                'disk': self.metrics['disk_usage'],
                'network': self.metrics['network_io'],
                'iops': self.metrics['iops'],
                'partition_count': len(self.partitions)
            }
            
    def get_location_info(self) -> Dict[str, str]:
        """Get node location information"""
        return {
            'datacenter': self.capacity.get('datacenter_id', ''),
            'rack': self.capacity.get('rack_id', ''),
            'zone': self.capacity.get('zone', '')
        } 