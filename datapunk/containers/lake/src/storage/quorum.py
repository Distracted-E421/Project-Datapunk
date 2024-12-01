from typing import Any, Dict, List, Optional, Set, Tuple
import asyncio
import logging
import time
import numpy as np
from collections import defaultdict
import aioredis
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import pandas as pd

logger = logging.getLogger(__name__)

class NodeStats:
    """Node statistics tracking"""
    
    def __init__(self):
        self.total_keys = 0
        self.memory_used = 0
        self.cpu_usage = 0.0
        self.network_in = 0
        self.network_out = 0
        self.latency = 0.0
        self.error_count = 0
        self.last_update = 0

class LoadBalancer:
    """Load balancer for Redis nodes"""
    
    def __init__(self, window_size: int = 3600):
        self.window_size = window_size
        self.node_stats: Dict[str, NodeStats] = {}
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        
    def record_operation(
        self,
        node_id: str,
        operation: str,
        duration: float
    ):
        """Record operation timing"""
        now = time.time()
        self.operation_times[node_id].append((now, operation, duration))
        self._cleanup_old_data(now)
        
    def get_node_score(self, node_id: str) -> float:
        """Calculate node health score"""
        if node_id not in self.node_stats:
            return 0.0
            
        stats = self.node_stats[node_id]
        
        # Calculate score components
        latency_score = 1.0 / (1.0 + stats.latency)
        error_score = 1.0 / (1.0 + stats.error_count)
        load_score = 1.0 - (stats.cpu_usage / 100.0)
        
        # Weighted combination
        return (
            0.4 * latency_score +
            0.4 * error_score +
            0.2 * load_score
        )
        
    def update_stats(self, node_id: str, stats: Dict[str, Any]):
        """Update node statistics"""
        if node_id not in self.node_stats:
            self.node_stats[node_id] = NodeStats()
            
        node_stats = self.node_stats[node_id]
        node_stats.total_keys = stats.get('total_keys', 0)
        node_stats.memory_used = stats.get('memory_used', 0)
        node_stats.cpu_usage = stats.get('cpu_usage', 0.0)
        node_stats.network_in = stats.get('network_in', 0)
        node_stats.network_out = stats.get('network_out', 0)
        node_stats.latency = stats.get('latency', 0.0)
        node_stats.error_count = stats.get('error_count', 0)
        node_stats.last_update = time.time()
        
    def _cleanup_old_data(self, current_time: float):
        """Remove old operation data"""
        cutoff = current_time - self.window_size
        
        for node_id in self.operation_times:
            self.operation_times[node_id] = [
                (t, op, d) for t, op, d in self.operation_times[node_id]
                if t > cutoff
            ]

class ScalingPredictor:
    """Predicts node scaling requirements"""
    
    def __init__(self, window_size: int = 3600, forecast_horizon: int = 300):
        self.window_size = window_size
        self.forecast_horizon = forecast_horizon
        self.scaler = StandardScaler()
        self.model = LinearRegression()
        self.metrics_history: List[Dict[str, Any]] = []
        self.last_update = 0
        
    def add_metrics(self, metrics: Dict[str, Any]):
        """Add current metrics to history"""
        metrics['timestamp'] = time.time()
        self.metrics_history.append(metrics)
        self._cleanup_old_data()
        
    def predict_scaling_needs(self) -> Dict[str, Any]:
        """Predict future resource requirements"""
        if len(self.metrics_history) < 10:  # Need enough data
            return {}
            
        df = pd.DataFrame(self.metrics_history)
        df['time_delta'] = df['timestamp'] - df['timestamp'].min()
        
        # Prepare features
        features = [
            'memory_used',
            'cpu_usage',
            'total_keys',
            'time_delta'
        ]
        
        X = df[features].values
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model on recent data
        self.model.fit(X_scaled[:-1], X_scaled[1:])
        
        # Predict future state
        last_state = X_scaled[-1].reshape(1, -1)
        future_state = self.model.predict(last_state)
        
        # Convert back to original scale
        future_metrics = self.scaler.inverse_transform(future_state)[0]
        
        return {
            'predicted_memory': future_metrics[0],
            'predicted_cpu': future_metrics[1],
            'predicted_keys': future_metrics[2],
            'confidence': self.model.score(X_scaled[:-1], X_scaled[1:])
        }
        
    def _cleanup_old_data(self):
        """Remove old metrics"""
        cutoff = time.time() - self.window_size
        self.metrics_history = [
            m for m in self.metrics_history
            if m['timestamp'] > cutoff
        ]

class AutoScaler:
    """Automatic node scaling manager"""
    
    def __init__(
        self,
        min_nodes: int = 2,
        max_nodes: int = 10,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 80.0,
        scale_up_factor: float = 1.5,
        scale_down_factor: float = 0.5,
        cooldown_period: int = 300
    ):
        self.min_nodes = min_nodes
        self.max_nodes = max_nodes
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.scale_up_factor = scale_up_factor
        self.scale_down_factor = scale_down_factor
        self.cooldown_period = cooldown_period
        self.last_scale = 0
        self.predictor = ScalingPredictor()
        
    def check_scaling(
        self,
        current_nodes: List[Dict[str, Any]],
        node_stats: Dict[str, NodeStats]
    ) -> Tuple[int, str]:
        """Check if scaling is needed"""
        if time.time() - self.last_scale < self.cooldown_period:
            return 0, "In cooldown period"
            
        # Collect current metrics
        metrics = self._aggregate_metrics(node_stats)
        self.predictor.add_metrics(metrics)
        
        # Get predictions
        predictions = self.predictor.predict_scaling_needs()
        if not predictions:
            return 0, "Insufficient data for prediction"
            
        current_count = len(current_nodes)
        scale_reason = ""
        
        # Check CPU scaling
        if predictions['predicted_cpu'] > self.cpu_threshold:
            cpu_nodes = int(
                current_count * self.scale_up_factor
            )
            scale_reason = "CPU threshold exceeded"
        elif predictions['predicted_cpu'] < self.cpu_threshold * self.scale_down_factor:
            cpu_nodes = int(
                current_count * self.scale_down_factor
            )
            scale_reason = "CPU usage low"
        else:
            cpu_nodes = current_count
            
        # Check memory scaling
        if predictions['predicted_memory'] > self.memory_threshold:
            memory_nodes = int(
                current_count * self.scale_up_factor
            )
            scale_reason = "Memory threshold exceeded"
        elif predictions['predicted_memory'] < self.memory_threshold * self.scale_down_factor:
            memory_nodes = int(
                current_count * self.scale_down_factor
            )
            scale_reason = "Memory usage low"
        else:
            memory_nodes = current_count
            
        # Take max of CPU and memory requirements
        target_nodes = max(cpu_nodes, memory_nodes)
        target_nodes = min(max(target_nodes, self.min_nodes), self.max_nodes)
        
        if target_nodes != current_count:
            self.last_scale = time.time()
            return target_nodes - current_count, scale_reason
            
        return 0, "No scaling needed"
        
    def _aggregate_metrics(
        self,
        node_stats: Dict[str, NodeStats]
    ) -> Dict[str, Any]:
        """Aggregate metrics across nodes"""
        total_memory = 0
        total_cpu = 0.0
        total_keys = 0
        node_count = len(node_stats)
        
        for stats in node_stats.values():
            total_memory += stats.memory_used
            total_cpu += stats.cpu_usage
            total_keys += stats.total_keys
            
        return {
            'memory_used': total_memory / node_count,
            'cpu_usage': total_cpu / node_count,
            'total_keys': total_keys,
            'node_count': node_count
        }

class QuorumManager:
    """Enhanced quorum management with predictive scaling"""
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        read_quorum: int,
        write_quorum: int,
        rebalance_interval: int = 3600,
        min_nodes: int = 2,
        max_nodes: int = 10
    ):
        self.nodes = nodes
        self.read_quorum = min(read_quorum, len(nodes))
        self.write_quorum = min(write_quorum, len(nodes))
        self.rebalance_interval = rebalance_interval
        
        self.load_balancer = LoadBalancer()
        self.node_health: Dict[str, bool] = {
            f"{node['host']}:{node['port']}": True
            for node in nodes
        }
        self.node_keys: Dict[str, Set[str]] = defaultdict(set)
        self.key_nodes: Dict[str, Set[str]] = defaultdict(set)
        
        self._health_check_task: Optional[asyncio.Task] = None
        self._rebalance_task: Optional[asyncio.Task] = None
        self._scale_task: Optional[asyncio.Task] = None
        
        self.auto_scaler = AutoScaler(
            min_nodes=min_nodes,
            max_nodes=max_nodes
        )
        
    async def start(self):
        """Start management tasks"""
        self._health_check_task = asyncio.create_task(
            self._periodic_health_check()
        )
        self._rebalance_task = asyncio.create_task(
            self._periodic_rebalance()
        )
        self._scale_task = asyncio.create_task(
            self._periodic_scale_check()
        )
        
    async def stop(self):
        """Stop management tasks"""
        for task in [self._health_check_task, self._rebalance_task, self._scale_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                    
    async def write(
        self,
        key: str,
        value: bytes,
        ttl: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """Write value with quorum consensus"""
        start_time = time.time()
        nodes = await self._get_target_nodes(key, self.write_quorum)
        
        if len(nodes) < self.write_quorum:
            raise RuntimeError(
                f"Not enough healthy nodes for write quorum "
                f"({len(nodes)} < {self.write_quorum})"
            )
            
        success_nodes = []
        for node in nodes:
            try:
                node_id = f"{node['host']}:{node['port']}"
                redis = await aioredis.from_url(
                    f"redis://{node['host']}:{node['port']}"
                )
                if await redis.set(key, value, ex=ttl):
                    success_nodes.append(node_id)
                    self.node_keys[node_id].add(key)
                    self.key_nodes[key].add(node_id)
                    
                    # Record operation timing
                    duration = time.time() - start_time
                    self.load_balancer.record_operation(
                        node_id,
                        'write',
                        duration
                    )
                    
                    if len(success_nodes) >= self.write_quorum:
                        return True, success_nodes
            except Exception as e:
                logger.error(
                    f"Write failed for node {node_id}: {e}"
                )
                self.load_balancer.node_stats[node_id].error_count += 1
                
        return False, success_nodes
        
    async def read(
        self,
        key: str
    ) -> Tuple[Optional[bytes], List[str], bool]:
        """Read value with quorum consensus"""
        start_time = time.time()
        nodes = await self._get_target_nodes(key, self.read_quorum)
        
        if len(nodes) < self.read_quorum:
            raise RuntimeError(
                f"Not enough healthy nodes for read quorum "
                f"({len(nodes)} < {self.read_quorum})"
            )
            
        values = []
        success_nodes = []
        
        for node in nodes:
            try:
                node_id = f"{node['host']}:{node['port']}"
                redis = await aioredis.from_url(
                    f"redis://{node['host']}:{node['port']}"
                )
                value = await redis.get(key)
                
                if value is not None:
                    values.append(value)
                    success_nodes.append(node_id)
                    
                    # Record operation timing
                    duration = time.time() - start_time
                    self.load_balancer.record_operation(
                        node_id,
                        'read',
                        duration
                    )
                    
                    if len(success_nodes) >= self.read_quorum:
                        # Check consistency
                        consistent = all(v == values[0] for v in values)
                        if not consistent:
                            await self._resolve_inconsistency(
                                key,
                                values,
                                success_nodes
                            )
                        return values[0], success_nodes, consistent
            except Exception as e:
                logger.error(
                    f"Read failed for node {node_id}: {e}"
                )
                self.load_balancer.node_stats[node_id].error_count += 1
                
        return None, success_nodes, False
        
    async def _get_target_nodes(
        self,
        key: str,
        count: int
    ) -> List[Dict[str, Any]]:
        """Get target nodes for operation"""
        # Get existing nodes for key
        existing_nodes = self.key_nodes.get(key, set())
        nodes = []
        
        # First, try nodes that already have the key
        for node in self.nodes:
            node_id = f"{node['host']}:{node['port']}"
            if (
                node_id in existing_nodes and
                self.node_health[node_id]
            ):
                nodes.append(node)
                
        # Then add additional nodes based on health scores
        remaining = count - len(nodes)
        if remaining > 0:
            available_nodes = [
                node for node in self.nodes
                if (
                    f"{node['host']}:{node['port']}" not in existing_nodes and
                    self.node_health[f"{node['host']}:{node['port']}"]
                )
            ]
            
            # Sort by health score
            scores = [
                (
                    node,
                    self.load_balancer.get_node_score(
                        f"{node['host']}:{node['port']}"
                    )
                )
                for node in available_nodes
            ]
            scores.sort(key=lambda x: x[1], reverse=True)
            
            nodes.extend(node for node, _ in scores[:remaining])
            
        return nodes
        
    async def _resolve_inconsistency(
        self,
        key: str,
        values: List[bytes],
        nodes: List[str]
    ):
        """Resolve inconsistent values"""
        # Use majority value if possible
        value_counts = defaultdict(int)
        for value in values:
            value_counts[value] += 1
            
        majority_value = max(
            value_counts.items(),
            key=lambda x: x[1]
        )[0]
        
        # Update nodes with inconsistent values
        for node_id, value in zip(nodes, values):
            if value != majority_value:
                try:
                    host, port = node_id.split(':')
                    redis = await aioredis.from_url(
                        f"redis://{host}:{port}"
                    )
                    await redis.set(key, majority_value)
                except Exception as e:
                    logger.error(
                        f"Failed to resolve inconsistency on {node_id}: {e}"
                    )
                    
    async def _periodic_health_check(self):
        """Check node health periodically"""
        while True:
            try:
                for node in self.nodes:
                    node_id = f"{node['host']}:{node['port']}"
                    try:
                        redis = await aioredis.from_url(
                            f"redis://{node['host']}:{node['port']}"
                        )
                        
                        # Basic health check
                        await redis.ping()
                        
                        # Collect detailed stats
                        info = await redis.info()
                        stats = {
                            'total_keys': info.get('db0', {}).get('keys', 0),
                            'memory_used': info.get('used_memory', 0),
                            'cpu_usage': info.get('used_cpu_sys', 0.0),
                            'network_in': info.get('total_net_input_bytes', 0),
                            'network_out': info.get('total_net_output_bytes', 0),
                            'latency': info.get('latency_ms', 0.0),
                            'error_count': self.load_balancer.node_stats.get(
                                node_id,
                                NodeStats()
                            ).error_count
                        }
                        
                        self.load_balancer.update_stats(node_id, stats)
                        self.node_health[node_id] = True
                        
                    except Exception as e:
                        logger.error(f"Node {node_id} health check failed: {e}")
                        self.node_health[node_id] = False
                        
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(60)
                
    async def _periodic_rebalance(self):
        """Rebalance data periodically"""
        while True:
            try:
                await asyncio.sleep(self.rebalance_interval)
                await self._rebalance_data()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rebalance error: {e}")
                
    async def _rebalance_data(self):
        """Rebalance data across nodes"""
        # Calculate load metrics
        node_loads = {}
        total_keys = 0
        
        for node_id, keys in self.node_keys.items():
            if self.node_health[node_id]:
                node_loads[node_id] = len(keys)
                total_keys += len(keys)
                
        if not node_loads:
            return
            
        # Calculate target load per node
        healthy_nodes = len(node_loads)
        target_load = total_keys / healthy_nodes
        
        # Identify overloaded and underloaded nodes
        overloaded = []
        underloaded = []
        
        for node_id, load in node_loads.items():
            if load > target_load * 1.1:  # 10% threshold
                overloaded.append((node_id, load))
            elif load < target_load * 0.9:
                underloaded.append((node_id, load))
                
        # Rebalance keys
        for over_node, over_load in overloaded:
            excess = over_load - target_load
            
            for under_node, under_load in underloaded:
                if excess <= 0:
                    break
                    
                capacity = target_load - under_load
                to_move = min(excess, capacity)
                
                if to_move > 0:
                    await self._move_keys(
                        over_node,
                        under_node,
                        int(to_move)
                    )
                    excess -= to_move
                    
    async def _move_keys(
        self,
        source: str,
        target: str,
        count: int
    ):
        """Move keys between nodes"""
        keys = list(self.node_keys[source])[:count]
        
        source_host, source_port = source.split(':')
        target_host, target_port = target.split(':')
        
        source_redis = await aioredis.from_url(
            f"redis://{source_host}:{source_port}"
        )
        target_redis = await aioredis.from_url(
            f"redis://{target_host}:{target_port}"
        )
        
        for key in keys:
            try:
                # Copy key to target
                value = await source_redis.dump(key)
                if value:
                    ttl = await source_redis.ttl(key)
                    await target_redis.restore(key, ttl, value)
                    
                    # Update tracking
                    self.node_keys[target].add(key)
                    self.key_nodes[key].add(target)
                    
            except Exception as e:
                logger.error(
                    f"Failed to move key {key} from {source} to {target}: {e}"
                )
        
    async def _periodic_scale_check(self):
        """Check scaling requirements periodically"""
        while True:
            try:
                scale_diff, reason = self.auto_scaler.check_scaling(
                    self.nodes,
                    self.load_balancer.node_stats
                )
                
                if scale_diff != 0:
                    logger.info(
                        f"Scaling adjustment needed: {scale_diff} nodes "
                        f"({reason})"
                    )
                    await self._adjust_nodes(scale_diff)
                    
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scale check error: {e}")
                await asyncio.sleep(60)
                
    async def _adjust_nodes(self, scale_diff: int):
        """Adjust number of nodes"""
        if scale_diff > 0:
            # Scale up
            current_ports = {
                int(node['port'])
                for node in self.nodes
            }
            
            # Find available ports
            new_ports = []
            port = 6379
            while len(new_ports) < scale_diff:
                if port not in current_ports:
                    new_ports.append(port)
                port += 1
                
            # Add new nodes
            for port in new_ports:
                node = {
                    'host': 'localhost',
                    'port': str(port)
                }
                self.nodes.append(node)
                node_id = f"{node['host']}:{node['port']}"
                self.node_health[node_id] = True
                
            logger.info(f"Added {scale_diff} new nodes")
            
        elif scale_diff < 0:
            # Scale down
            to_remove = abs(scale_diff)
            
            # Sort nodes by health score
            scores = [
                (
                    node,
                    self.load_balancer.get_node_score(
                        f"{node['host']}:{node['port']}"
                    )
                )
                for node in self.nodes
            ]
            scores.sort(key=lambda x: x[1])
            
            # Remove nodes with lowest scores
            for node, _ in scores[:to_remove]:
                node_id = f"{node['host']}:{node['port']}"
                
                # Move keys to other nodes
                if node_id in self.node_keys:
                    keys = list(self.node_keys[node_id])
                    if keys:
                        # Find best target node
                        target = max(
                            (n for n in self.nodes if n != node),
                            key=lambda x: self.load_balancer.get_node_score(
                                f"{x['host']}:{x['port']}"
                            )
                        )
                        target_id = f"{target['host']}:{target['port']}"
                        
                        await self._move_keys(
                            node_id,
                            target_id,
                            len(keys)
                        )
                        
                self.nodes.remove(node)
                del self.node_health[node_id]
                if node_id in self.node_keys:
                    del self.node_keys[node_id]
                    
            logger.info(f"Removed {abs(scale_diff)} nodes")
            
        # Update quorum sizes
        self.read_quorum = min(self.read_quorum, len(self.nodes))
        self.write_quorum = min(self.write_quorum, len(self.nodes))