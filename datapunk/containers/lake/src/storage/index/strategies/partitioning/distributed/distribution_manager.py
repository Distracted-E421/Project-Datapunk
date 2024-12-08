from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import threading
import logging
from ..base.base_manager import GridPartitionManager
from .node import PartitionNode
from .coordinator import PartitionCoordinator
from .replication import ReplicationManager
from .health import HealthMonitor

class DistributedPartitionManager:
    """Manages distributed partitions across multiple nodes"""
    
    def __init__(self, base_manager: GridPartitionManager):
        self.base_manager = base_manager
        self.nodes: Dict[str, PartitionNode] = {}
        self.coordinator = PartitionCoordinator()
        self.replication_manager = ReplicationManager()
        self.health_monitor = HealthMonitor()
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
    def register_node(self, node_id: str, capacity: Dict[str, Any]) -> bool:
        """Register a new node in the cluster"""
        with self.lock:
            if node_id in self.nodes:
                return False
                
            node = PartitionNode(
                node_id=node_id,
                capacity=capacity,
                status='active'
            )
            self.nodes[node_id] = node
            self.coordinator.add_node(node)
            self.health_monitor.register_node(node)
            return True
            
    def deregister_node(self, node_id: str) -> bool:
        """Remove a node from the cluster"""
        with self.lock:
            if node_id not in self.nodes:
                return False
                
            node = self.nodes[node_id]
            # Initiate partition rebalancing
            self._rebalance_partitions(node)
            
            # Remove node from all components
            self.coordinator.remove_node(node)
            self.health_monitor.deregister_node(node)
            del self.nodes[node_id]
            return True
            
    def assign_partition(self, partition_id: str, 
                        node_ids: List[str],
                        replication_factor: int = 3) -> bool:
        """Assign a partition to specific nodes"""
        with self.lock:
            # Validate nodes exist
            if not all(node_id in self.nodes for node_id in node_ids):
                return False
                
            # Ensure replication factor
            if len(node_ids) < replication_factor:
                additional_nodes = self._select_additional_nodes(
                    node_ids, 
                    replication_factor - len(node_ids)
                )
                node_ids.extend(additional_nodes)
                
            # Assign partition
            for node_id in node_ids:
                self.nodes[node_id].add_partition(partition_id)
                
            # Setup replication
            self.replication_manager.setup_replication(
                partition_id,
                node_ids
            )
            return True
            
    def get_partition_locations(self, partition_id: str) -> List[str]:
        """Get all nodes hosting a partition"""
        locations = []
        for node_id, node in self.nodes.items():
            if node.has_partition(partition_id):
                locations.append(node_id)
        return locations
        
    def rebalance_cluster(self) -> bool:
        """Rebalance partitions across all nodes"""
        with self.lock:
            try:
                # Get current distribution
                distribution = self._get_current_distribution()
                
                # Calculate ideal distribution
                ideal = self._calculate_ideal_distribution()
                
                # Generate rebalancing plan
                plan = self._generate_rebalancing_plan(
                    distribution,
                    ideal
                )
                
                # Execute rebalancing
                return self._execute_rebalancing_plan(plan)
            except Exception as e:
                self.logger.error(f"Rebalancing failed: {str(e)}")
                return False
                
    def handle_node_failure(self, node_id: str):
        """Handle a node failure"""
        with self.lock:
            if node_id not in self.nodes:
                return
                
            node = self.nodes[node_id]
            node.status = 'failed'
            
            # Trigger recovery process
            self._recover_failed_node(node)
            
            # Update cluster state
            self.coordinator.update_cluster_state()
            
    def _rebalance_partitions(self, failed_node: PartitionNode):
        """Rebalance partitions from a failed/removed node"""
        partitions = failed_node.get_partitions()
        remaining_nodes = [n for n in self.nodes.values() if n.node_id != failed_node.node_id]
        
        if not remaining_nodes:
            return
            
        # Redistribute partitions
        for partition_id in partitions:
            target_nodes = self._select_target_nodes(
                partition_id,
                remaining_nodes,
                3  # Default replication factor
            )
            self.assign_partition(partition_id, [n.node_id for n in target_nodes])
            
    def _select_additional_nodes(self, 
                               existing_nodes: List[str],
                               count: int) -> List[str]:
        """Select additional nodes for replication"""
        available_nodes = [
            node_id for node_id in self.nodes.keys()
            if node_id not in existing_nodes
            and self.nodes[node_id].status == 'active'
        ]
        
        # Sort by capacity and load
        sorted_nodes = sorted(
            available_nodes,
            key=lambda x: self.nodes[x].get_load()
        )
        
        return sorted_nodes[:count]
        
    def _get_current_distribution(self) -> Dict[str, Set[str]]:
        """Get current partition distribution"""
        distribution = {}
        for node_id, node in self.nodes.items():
            distribution[node_id] = node.get_partitions()
        return distribution
        
    def _calculate_ideal_distribution(self) -> Dict[str, int]:
        """Calculate ideal partition distribution"""
        total_partitions = sum(
            len(node.get_partitions())
            for node in self.nodes.values()
        )
        
        active_nodes = [
            node for node in self.nodes.values()
            if node.status == 'active'
        ]
        
        if not active_nodes:
            return {}
            
        base_count = total_partitions // len(active_nodes)
        remainder = total_partitions % len(active_nodes)
        
        distribution = {}
        for i, node in enumerate(active_nodes):
            distribution[node.node_id] = base_count
            if i < remainder:
                distribution[node.node_id] += 1
                
        return distribution
        
    def _generate_rebalancing_plan(self,
                                 current: Dict[str, Set[str]],
                                 ideal: Dict[str, int]) -> List[Dict[str, Any]]:
        """Generate plan for rebalancing partitions"""
        plan = []
        
        # Find overloaded and underloaded nodes
        overloaded = {
            node_id: len(partitions) - ideal[node_id]
            for node_id, partitions in current.items()
            if len(partitions) > ideal[node_id]
        }
        
        underloaded = {
            node_id: ideal[node_id] - len(current.get(node_id, set()))
            for node_id in ideal
            if ideal[node_id] > len(current.get(node_id, set()))
        }
        
        # Create movement plan
        for source_id, excess in overloaded.items():
            source_partitions = current[source_id]
            
            for target_id, deficit in underloaded.items():
                if excess <= 0 or deficit <= 0:
                    continue
                    
                move_count = min(excess, deficit)
                partitions_to_move = set(list(source_partitions)[:move_count])
                
                plan.append({
                    'source': source_id,
                    'target': target_id,
                    'partitions': partitions_to_move
                })
                
                excess -= move_count
                underloaded[target_id] -= move_count
                source_partitions -= partitions_to_move
                
        return plan
        
    def _execute_rebalancing_plan(self, plan: List[Dict[str, Any]]) -> bool:
        """Execute the rebalancing plan"""
        try:
            for move in plan:
                source_node = self.nodes[move['source']]
                target_node = self.nodes[move['target']]
                
                for partition_id in move['partitions']:
                    # Transfer partition
                    if self.replication_manager.transfer_partition(
                        partition_id,
                        source_node,
                        target_node
                    ):
                        source_node.remove_partition(partition_id)
                        target_node.add_partition(partition_id)
                    else:
                        self.logger.error(
                            f"Failed to transfer partition {partition_id}"
                        )
                        return False
                        
            return True
        except Exception as e:
            self.logger.error(f"Plan execution failed: {str(e)}")
            return False
            
    def _recover_failed_node(self, node: PartitionNode):
        """Recover from a node failure"""
        # Get affected partitions
        affected_partitions = node.get_partitions()
        
        # Find healthy replicas
        for partition_id in affected_partitions:
            replicas = self.replication_manager.get_replicas(partition_id)
            healthy_replicas = [
                n for n in replicas 
                if n.status == 'active'
            ]
            
            if healthy_replicas:
                # Restore from healthy replica
                source = healthy_replicas[0]
                new_targets = self._select_target_nodes(
                    partition_id,
                    [n for n in self.nodes.values() if n.status == 'active'],
                    3  # Default replication factor
                )
                
                for target in new_targets:
                    self.replication_manager.restore_partition(
                        partition_id,
                        source,
                        target
                    )
            else:
                self.logger.error(
                    f"No healthy replicas for partition {partition_id}"
                )
                
    def _select_target_nodes(self,
                           partition_id: str,
                           candidates: List[PartitionNode],
                           count: int) -> List[PartitionNode]:
        """Select target nodes for partition placement"""
        # Sort by capacity and current load
        sorted_candidates = sorted(
            candidates,
            key=lambda x: (x.get_load(), -x.capacity.get('storage', 0))
        )
        
        # Select nodes with consideration for rack/datacenter diversity
        selected = []
        for node in sorted_candidates:
            if len(selected) >= count:
                break
                
            # Check rack/datacenter constraints
            if self._satisfies_placement_constraints(
                partition_id, 
                selected + [node]
            ):
                selected.append(node)
                
        return selected
        
    def _satisfies_placement_constraints(self,
                                      partition_id: str,
                                      nodes: List[PartitionNode]) -> bool:
        """Check if node selection satisfies placement constraints"""
        # Example: Ensure nodes are in different racks/datacenters
        racks = set()
        datacenters = set()
        
        for node in nodes:
            rack_id = node.capacity.get('rack_id')
            dc_id = node.capacity.get('datacenter_id')
            
            if rack_id in racks or dc_id in datacenters:
                return False
                
            racks.add(rack_id)
            datacenters.add(dc_id)
            
        return True 