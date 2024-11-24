from typing import Dict, List, Set, Optional, Any
import asyncio
import logging
import time
from datetime import datetime
from .cluster_manager import ClusterNode, ClusterManager

class RebalanceStrategy(Enum):
    GRADUAL = "gradual"  # Move keys gradually to minimize impact
    IMMEDIATE = "immediate"  # Move all keys at once
    OFF_PEAK = "off_peak"  # Move keys during off-peak hours

class ClusterRebalancer:
    def __init__(
        self,
        cluster_manager: ClusterManager,
        strategy: RebalanceStrategy = RebalanceStrategy.GRADUAL,
        batch_size: int = 100,
        sleep_between_batches: float = 0.1
    ):
        self.cluster = cluster_manager
        self.strategy = strategy
        self.batch_size = batch_size
        self.sleep_between_batches = sleep_between_batches
        self.logger = logging.getLogger(__name__)
        self._rebalancing = False
        self._cancel_rebalancing = False

    async def start_rebalance(self) -> None:
        """Start cluster rebalancing"""
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
        """Identify keys that need to be moved"""
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
        """Move all keys immediately"""
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
        """Move keys gradually in batches"""
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
        """Move keys during off-peak hours"""
        while keys_to_move and not self._cancel_rebalancing:
            # Check if current time is off-peak (e.g., between 2 AM and 5 AM)
            current_hour = datetime.now().hour
            if 2 <= current_hour <= 5:
                await self._rebalance_gradual(keys_to_move)
            else:
                await asyncio.sleep(300)  # Sleep for 5 minutes 