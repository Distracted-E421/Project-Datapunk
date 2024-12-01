from typing import Dict, Any, List, Optional, Set
import threading
import time
from datetime import datetime
import logging
from .node import PartitionNode

class ClusterState:
    """Represents the current state of the cluster"""
    
    def __init__(self):
        self.nodes: Dict[str, PartitionNode] = {}
        self.partition_locations: Dict[str, Set[str]] = {}
        self.version = 0
        self.last_update = datetime.now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return {
            'nodes': {
                node_id: {
                    'status': node.status,
                    'capacity': node.capacity,
                    'metrics': node.metrics,
                    'partitions': list(node.get_partitions())
                }
                for node_id, node in self.nodes.items()
            },
            'partition_locations': {
                partition_id: list(nodes)
                for partition_id, nodes in self.partition_locations.items()
            },
            'version': self.version,
            'last_update': self.last_update.isoformat()
        }
        
class PartitionCoordinator:
    """Coordinates partition distribution and cluster state"""
    
    def __init__(self):
        self.state = ClusterState()
        self.lock = threading.Lock()
        self.state_subscribers: List[callable] = []
        self.logger = logging.getLogger(__name__)
        self._stop_monitor = False
        self._monitor_thread = None
        
    def start(self):
        """Start the coordinator"""
        self._stop_monitor = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_cluster,
            daemon=True
        )
        self._monitor_thread.start()
        
    def stop(self):
        """Stop the coordinator"""
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def add_node(self, node: PartitionNode):
        """Add a node to the cluster"""
        with self.lock:
            self.state.nodes[node.node_id] = node
            self._update_state()
            
    def remove_node(self, node: PartitionNode):
        """Remove a node from the cluster"""
        with self.lock:
            if node.node_id in self.state.nodes:
                del self.state.nodes[node.node_id]
                # Update partition locations
                for partition_id in list(self.state.partition_locations.keys()):
                    nodes = self.state.partition_locations[partition_id]
                    if node.node_id in nodes:
                        nodes.remove(node.node_id)
                        if not nodes:
                            del self.state.partition_locations[partition_id]
                self._update_state()
                
    def update_partition_location(self, partition_id: str,
                                node_ids: Set[str]):
        """Update the location of a partition"""
        with self.lock:
            self.state.partition_locations[partition_id] = node_ids
            self._update_state()
            
    def get_partition_nodes(self, partition_id: str) -> List[PartitionNode]:
        """Get nodes containing a partition"""
        with self.lock:
            node_ids = self.state.partition_locations.get(partition_id, set())
            return [
                self.state.nodes[node_id]
                for node_id in node_ids
                if node_id in self.state.nodes
            ]
            
    def subscribe_to_state_changes(self, callback: callable):
        """Subscribe to state changes"""
        self.state_subscribers.append(callback)
        
    def unsubscribe_from_state_changes(self, callback: callable):
        """Unsubscribe from state changes"""
        if callback in self.state_subscribers:
            self.state_subscribers.remove(callback)
            
    def get_cluster_state(self) -> Dict[str, Any]:
        """Get current cluster state"""
        with self.lock:
            return self.state.to_dict()
            
    def update_cluster_state(self):
        """Force update of cluster state"""
        with self.lock:
            self._update_state()
            
    def get_node_count(self) -> int:
        """Get number of nodes in cluster"""
        return len(self.state.nodes)
        
    def get_partition_count(self) -> int:
        """Get number of unique partitions"""
        return len(self.state.partition_locations)
        
    def get_healthy_nodes(self) -> List[PartitionNode]:
        """Get list of healthy nodes"""
        return [
            node for node in self.state.nodes.values()
            if node.is_healthy()
        ]
        
    def get_node_by_id(self, node_id: str) -> Optional[PartitionNode]:
        """Get node by ID"""
        return self.state.nodes.get(node_id)
        
    def _update_state(self):
        """Update cluster state and notify subscribers"""
        self.state.version += 1
        self.state.last_update = datetime.now()
        
        # Notify subscribers
        state_dict = self.state.to_dict()
        for subscriber in self.state_subscribers:
            try:
                subscriber(state_dict)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber: {str(e)}")
                
    def _monitor_cluster(self):
        """Monitor cluster health and state"""
        while not self._stop_monitor:
            try:
                self._check_node_health()
                self._check_partition_health()
                self._cleanup_stale_state()
            except Exception as e:
                self.logger.error(f"Error in cluster monitor: {str(e)}")
                
            # Sleep for monitoring interval
            time.sleep(10)  # 10 second interval
            
    def _check_node_health(self):
        """Check health of all nodes"""
        with self.lock:
            for node in list(self.state.nodes.values()):
                if not node.is_healthy():
                    if node.status == 'active':
                        node.status = 'unhealthy'
                        self._update_state()
                elif node.status == 'unhealthy':
                    node.status = 'active'
                    self._update_state()
                    
    def _check_partition_health(self):
        """Check health of partition distribution"""
        with self.lock:
            for partition_id, node_ids in list(self.state.partition_locations.items()):
                healthy_nodes = [
                    node_id for node_id in node_ids
                    if node_id in self.state.nodes and 
                    self.state.nodes[node_id].is_healthy()
                ]
                
                if len(healthy_nodes) < len(node_ids):
                    self.logger.warning(
                        f"Partition {partition_id} has unhealthy replicas"
                    )
                    
    def _cleanup_stale_state(self):
        """Clean up stale state information"""
        with self.lock:
            # Remove partitions with no valid locations
            for partition_id in list(self.state.partition_locations.keys()):
                nodes = self.state.partition_locations[partition_id]
                valid_nodes = {
                    node_id for node_id in nodes
                    if node_id in self.state.nodes
                }
                if not valid_nodes:
                    del self.state.partition_locations[partition_id]
                elif valid_nodes != nodes:
                    self.state.partition_locations[partition_id] = valid_nodes
                    
            if self.state.version > 1000000:  # Prevent version from growing too large
                self.state.version = 0
                
    def get_node_distribution(self) -> Dict[str, int]:
        """Get partition distribution across nodes"""
        distribution = {}
        for node_id, node in self.state.nodes.items():
            distribution[node_id] = len(node.get_partitions())
        return distribution
        
    def get_replication_status(self) -> Dict[str, Dict[str, Any]]:
        """Get replication status for all partitions"""
        status = {}
        for partition_id, node_ids in self.state.partition_locations.items():
            healthy_replicas = sum(
                1 for node_id in node_ids
                if node_id in self.state.nodes and 
                self.state.nodes[node_id].is_healthy()
            )
            status[partition_id] = {
                'total_replicas': len(node_ids),
                'healthy_replicas': healthy_replicas,
                'nodes': list(node_ids)
            }
        return status 