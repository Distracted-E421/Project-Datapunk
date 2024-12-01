from typing import Dict, Any, List, Set, Optional
import threading
import logging
from datetime import datetime, timedelta
from .node import PartitionNode

class ReplicationState:
    """Represents the replication state of a partition"""
    
    def __init__(self, partition_id: str):
        self.partition_id = partition_id
        self.primary_node: Optional[str] = None
        self.replica_nodes: Set[str] = set()
        self.last_sync: Dict[str, datetime] = {}
        self.sync_status: Dict[str, str] = {}  # 'synced', 'syncing', 'failed'
        self.version = 0
        
class ReplicationManager:
    """Manages partition replication across nodes"""
    
    def __init__(self):
        self.states: Dict[str, ReplicationState] = {}
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self._stop_monitor = False
        self._monitor_thread = None
        
    def start(self):
        """Start the replication manager"""
        self._stop_monitor = False
        self._monitor_thread = threading.Thread(
            target=self._monitor_replication,
            daemon=True
        )
        self._monitor_thread.start()
        
    def stop(self):
        """Stop the replication manager"""
        self._stop_monitor = True
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def setup_replication(self, partition_id: str,
                         node_ids: List[str]) -> bool:
        """Setup replication for a partition"""
        with self.lock:
            if not node_ids:
                return False
                
            state = self.states.get(partition_id)
            if not state:
                state = ReplicationState(partition_id)
                self.states[partition_id] = state
                
            # First node is primary
            state.primary_node = node_ids[0]
            state.replica_nodes = set(node_ids[1:])
            
            # Initialize sync status
            for node_id in node_ids[1:]:
                if node_id not in state.sync_status:
                    state.sync_status[node_id] = 'syncing'
                    state.last_sync[node_id] = datetime.now()
                    
            return True
            
    def get_replicas(self, partition_id: str) -> List[str]:
        """Get all replica nodes for a partition"""
        with self.lock:
            state = self.states.get(partition_id)
            if not state:
                return []
            return [state.primary_node] + list(state.replica_nodes)
            
    def transfer_partition(self, partition_id: str,
                         source_node: PartitionNode,
                         target_node: PartitionNode) -> bool:
        """Transfer a partition to a new node"""
        with self.lock:
            try:
                # Verify source has partition
                if not source_node.has_partition(partition_id):
                    return False
                    
                # Check target capacity
                if not target_node.can_accept_partition():
                    return False
                    
                # Perform transfer
                success = self._transfer_data(
                    partition_id,
                    source_node,
                    target_node
                )
                
                if success:
                    # Update replication state
                    state = self.states.get(partition_id)
                    if state:
                        if source_node.node_id == state.primary_node:
                            state.primary_node = target_node.node_id
                        else:
                            state.replica_nodes.remove(source_node.node_id)
                            state.replica_nodes.add(target_node.node_id)
                            
                        state.sync_status[target_node.node_id] = 'synced'
                        state.last_sync[target_node.node_id] = datetime.now()
                        state.version += 1
                        
                return success
            except Exception as e:
                self.logger.error(
                    f"Transfer failed for partition {partition_id}: {str(e)}"
                )
                return False
                
    def restore_partition(self, partition_id: str,
                         source_node: PartitionNode,
                         target_node: PartitionNode) -> bool:
        """Restore a partition from a healthy replica"""
        with self.lock:
            try:
                # Verify source has partition
                if not source_node.has_partition(partition_id):
                    return False
                    
                # Check target capacity
                if not target_node.can_accept_partition():
                    return False
                    
                # Perform restore
                success = self._restore_data(
                    partition_id,
                    source_node,
                    target_node
                )
                
                if success:
                    # Update replication state
                    state = self.states.get(partition_id)
                    if state:
                        state.replica_nodes.add(target_node.node_id)
                        state.sync_status[target_node.node_id] = 'synced'
                        state.last_sync[target_node.node_id] = datetime.now()
                        state.version += 1
                        
                return success
            except Exception as e:
                self.logger.error(
                    f"Restore failed for partition {partition_id}: {str(e)}"
                )
                return False
                
    def check_replication_health(self, partition_id: str) -> Dict[str, Any]:
        """Check health of partition replication"""
        with self.lock:
            state = self.states.get(partition_id)
            if not state:
                return {
                    'status': 'unknown',
                    'healthy_replicas': 0,
                    'total_replicas': 0
                }
                
            # Count healthy replicas
            healthy_replicas = sum(
                1 for status in state.sync_status.values()
                if status == 'synced'
            )
            
            # Check sync age
            max_sync_age = timedelta(hours=1)
            outdated_replicas = sum(
                1 for last_sync in state.last_sync.values()
                if datetime.now() - last_sync > max_sync_age
            )
            
            return {
                'status': 'healthy' if healthy_replicas >= 2 else 'degraded',
                'healthy_replicas': healthy_replicas,
                'total_replicas': len(state.replica_nodes) + 1,
                'outdated_replicas': outdated_replicas,
                'primary_node': state.primary_node,
                'version': state.version
            }
            
    def _monitor_replication(self):
        """Monitor replication health and trigger repairs"""
        while not self._stop_monitor:
            try:
                self._check_replication_status()
                self._trigger_repairs()
            except Exception as e:
                self.logger.error(f"Replication monitor error: {str(e)}")
                
            # Sleep for monitoring interval
            threading.sleep(30)  # 30 second interval
            
    def _check_replication_status(self):
        """Check status of all replications"""
        with self.lock:
            for partition_id, state in self.states.items():
                health = self.check_replication_health(partition_id)
                if health['status'] != 'healthy':
                    self.logger.warning(
                        f"Unhealthy replication for partition {partition_id}"
                    )
                    
    def _trigger_repairs(self):
        """Trigger repairs for degraded replications"""
        with self.lock:
            for partition_id, state in self.states.items():
                for node_id, status in state.sync_status.items():
                    if status == 'failed':
                        self.logger.info(
                            f"Triggering repair for partition {partition_id} "
                            f"on node {node_id}"
                        )
                        # Reset status to trigger re-sync
                        state.sync_status[node_id] = 'syncing'
                        
    def _transfer_data(self, partition_id: str,
                      source_node: PartitionNode,
                      target_node: PartitionNode) -> bool:
        """Transfer partition data between nodes"""
        # This would integrate with your data transfer mechanism
        # For now, we'll simulate success
        return True
        
    def _restore_data(self, partition_id: str,
                     source_node: PartitionNode,
                     target_node: PartitionNode) -> bool:
        """Restore partition data from source to target"""
        # This would integrate with your data restore mechanism
        # For now, we'll simulate success
        return True
        
    def get_replication_metrics(self) -> Dict[str, Any]:
        """Get metrics about replication system"""
        with self.lock:
            total_partitions = len(self.states)
            healthy_partitions = sum(
                1 for p in self.states.keys()
                if self.check_replication_health(p)['status'] == 'healthy'
            )
            
            return {
                'total_partitions': total_partitions,
                'healthy_partitions': healthy_partitions,
                'degraded_partitions': total_partitions - healthy_partitions,
                'average_replicas': sum(
                    len(s.replica_nodes) + 1
                    for s in self.states.values()
                ) / max(1, total_partitions)
            } 