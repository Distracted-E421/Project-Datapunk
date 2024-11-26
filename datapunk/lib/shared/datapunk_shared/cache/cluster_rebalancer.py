from typing import Dict, List, Set, Optional, Any
import asyncio
import logging
import time
from datetime import datetime
from .cluster_manager import ClusterNode, ClusterManager

class RebalanceStrategy(Enum):
    """
    Defines different strategies for redistributing keys across cluster nodes.
    
    The choice of strategy impacts system performance and availability during rebalancing:
    - GRADUAL: Minimizes performance impact but takes longer
    - IMMEDIATE: Fastest but may impact system performance
    - OFF_PEAK: Balances performance impact by operating during low-traffic hours
    """
    GRADUAL = "gradual"
    IMMEDIATE = "immediate"
    OFF_PEAK = "off_peak"

class ClusterRebalancer:
    """
    Manages the redistribution of keys across cluster nodes to maintain balanced data distribution.
    
    This class handles the complex task of moving keys between nodes while:
    - Preserving data consistency
    - Maintaining TTL values
    - Allowing for interruption of the rebalancing process
    - Supporting different rebalancing strategies based on operational needs
    
    NOTE: The rebalancer assumes the master node has a complete view of all keys
    TODO: Consider adding support for partial rebalancing of specific key ranges
    """

    async def start_rebalance(self) -> None:
        """
        Initiates the cluster rebalancing process.
        
        The process follows these steps:
        1. Rebuilds the hash ring to reflect current cluster topology
        2. Identifies keys that need to be moved based on the new ring
        3. Executes the chosen rebalancing strategy
        
        IMPORTANT: This operation can be resource-intensive depending on the chosen strategy
        """
        if self._rebalancing:
            self.logger.warning("Rebalancing already in progress")
            return

        try:
            self._rebalancing = True
            self._cancel_rebalancing = False

            # Build new hash ring
            self.cluster._build_hash_ring()
            
            # Get all keys and their current locations
            keys_to_move = await self._identify_keys_to_move()
            
            if not keys_to_move:
                self.logger.info("No keys need to be moved")
                return

            self.logger.info(f"Starting rebalance of {len(keys_to_move)} keys")
            
            if self.strategy == RebalanceStrategy.IMMEDIATE:
                await self._rebalance_immediate(keys_to_move)
            elif self.strategy == RebalanceStrategy.GRADUAL:
                await self._rebalance_gradual(keys_to_move)
            elif self.strategy == RebalanceStrategy.OFF_PEAK:
                await self._rebalance_off_peak(keys_to_move)

        except Exception as e:
            self.logger.error(f"Rebalancing failed: {str(e)}")
            raise
        finally:
            self._rebalancing = False

    async def stop_rebalance(self) -> None:
        """Stop ongoing rebalancing"""
        self._cancel_rebalancing = True
        while self._rebalancing:
            await asyncio.sleep(0.1)

    async def _identify_keys_to_move(self) -> Dict[str, str]:
        """
        Scans all nodes to identify keys that need redistribution.
        
        Uses Redis SCAN for memory-efficient key iteration. Only includes keys that:
        - Belong to this cluster's namespace
        - Need to move to a different node based on the current hash ring
        
        NOTE: The scan operation may return duplicate keys if the keyspace changes during scanning
        TODO: Consider implementing a mechanism to handle key duplicates
        """
        keys_to_move = {}
        
        for node in self.cluster.nodes.values():
            if node.status != "connected" or not node.connection:
                continue

            cursor = 0
            while True:
                cursor, keys = await node.connection.scan(
                    cursor,
                    match=f"{self.cluster.config.namespace}:*",
                    count=self.batch_size
                )

                for key in keys:
                    target_node = await self.cluster.get_node_for_key(key)
                    if target_node and target_node.node_id != node.node_id:
                        keys_to_move[key] = target_node.node_id

                if cursor == 0:
                    break

        return keys_to_move

    async def _rebalance_immediate(self, keys_to_move: Dict[str, str]) -> None:
        """
        Performs immediate bulk transfer of all keys that need to be moved.
        
        Uses pipelining to reduce the number of network round-trips when deleting keys.
        
        WARNING: This method can cause significant load on both source and target nodes
        FIXME: Consider implementing retry logic for failed transfers
        """
        pipe = self.cluster._master_node.connection.pipeline()
        
        for key, target_node_id in keys_to_move.items():
            if self._cancel_rebalancing:
                break

            target_node = self.cluster.nodes[target_node_id]
            if target_node.status != "connected" or not target_node.connection:
                continue

            # Get key data and TTL
            data = await self.cluster._master_node.connection.get(key)
            ttl = await self.cluster._master_node.connection.ttl(key)

            if data:
                # Set on target node
                await target_node.connection.set(key, data, ex=ttl if ttl > 0 else None)
                # Delete from source
                pipe.delete(key)

        await pipe.execute()

    async def _rebalance_gradual(self, keys_to_move: Dict[str, str]) -> None:
        """
        Gradually transfers keys in controlled batches to minimize system impact.
        
        Features:
        - Respects batch size and sleep interval configuration
        - Handles individual key transfer failures without stopping the process
        - Can be interrupted via cancel flag
        
        NOTE: Keys might be temporarily duplicated during the transfer window
        TODO: Add metrics collection for monitoring transfer progress
        """
        moved_count = 0
        
        for key, target_node_id in keys_to_move.items():
            if self._cancel_rebalancing:
                break

            target_node = self.cluster.nodes[target_node_id]
            if target_node.status != "connected" or not target_node.connection:
                continue

            try:
                # Get key data and TTL
                data = await self.cluster._master_node.connection.get(key)
                ttl = await self.cluster._master_node.connection.ttl(key)

                if data:
                    # Set on target node
                    await target_node.connection.set(key, data, ex=ttl if ttl > 0 else None)
                    # Delete from source
                    await self.cluster._master_node.connection.delete(key)
                    
                    moved_count += 1
                    if moved_count % self.batch_size == 0:
                        await asyncio.sleep(self.sleep_between_batches)

            except Exception as e:
                self.logger.error(f"Failed to move key {key}: {str(e)}")

    async def _rebalance_off_peak(self, keys_to_move: Dict[str, str]) -> None:
        """
        Executes rebalancing during defined off-peak hours (2 AM - 5 AM).
        
        Uses the gradual rebalancing approach during the allowed window.
        Sleeps during peak hours to avoid system impact.
        
        NOTE: The off-peak window is currently hardcoded
        TODO: Make the off-peak window configurable
        """
        while keys_to_move and not self._cancel_rebalancing:
            # Check if current time is off-peak (e.g., between 2 AM and 5 AM)
            current_hour = datetime.now().hour
            if 2 <= current_hour <= 5:
                await self._rebalance_gradual(keys_to_move)
            else:
                await asyncio.sleep(300)  # Sleep for 5 minutes 