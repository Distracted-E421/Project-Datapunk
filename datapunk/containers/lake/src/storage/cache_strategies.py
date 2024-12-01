from typing import Any, Dict, List, Optional, Set, Union, Tuple
import asyncio
import random
import logging
import time
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import aioredis
from collections import defaultdict
import numpy as np
from ..ingestion.monitoring import HandlerMetrics, MetricType
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pandas as pd

logger = logging.getLogger(__name__)

class AccessPattern:
    """Tracks and analyzes cache access patterns"""
    
    def __init__(self, window_size: int = 3600):
        self.window_size = window_size
        self.access_times: Dict[str, List[float]] = defaultdict(list)
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.pattern_cache: Dict[str, List[Tuple[float, float]]] = {}
        
    def record_access(self, key: str, timestamp: Optional[float] = None):
        """Record key access"""
        ts = timestamp or time.time()
        self.access_times[key].append(ts)
        self.access_counts[key] += 1
        self._cleanup_old_data(ts)
        
    def get_periodic_patterns(self, key: str) -> List[Tuple[float, float]]:
        """Detect periodic access patterns"""
        if key in self.pattern_cache:
            return self.pattern_cache[key]
            
        times = self.access_times.get(key, [])
        if len(times) < 3:
            return []
            
        # Convert to numpy array for analysis
        intervals = np.diff(times)
        
        # Find periodic patterns using autocorrelation
        autocorr = np.correlate(intervals, intervals, mode='full')
        peaks = self._find_peaks(autocorr[len(autocorr)//2:])
        
        patterns = []
        for period in peaks:
            confidence = self._calculate_confidence(intervals, period)
            if confidence > 0.7:  # High confidence threshold
                patterns.append((period, confidence))
                
        self.pattern_cache[key] = patterns
        return patterns
        
    def predict_next_access(self, key: str) -> Optional[float]:
        """Predict next access time"""
        patterns = self.get_periodic_patterns(key)
        if not patterns:
            return None
            
        last_access = self.access_times[key][-1]
        predictions = []
        
        for period, confidence in patterns:
            next_time = last_access + period
            predictions.append((next_time, confidence))
            
        if predictions:
            # Weight predictions by confidence
            weighted_sum = sum(t * c for t, c in predictions)
            total_confidence = sum(c for _, c in predictions)
            return weighted_sum / total_confidence
            
        return None
        
    def get_related_keys(self, key: str, threshold: float = 0.8) -> List[str]:
        """Find keys frequently accessed together"""
        related = []
        key_times = set(self.access_times.get(key, []))
        
        if not key_times:
            return []
            
        for other_key, times in self.access_times.items():
            if other_key == key:
                continue
                
            other_times = set(times)
            if not other_times:
                continue
                
            # Calculate temporal correlation
            intersection = key_times.intersection(
                {t - 1 <= x <= t + 1 for t in other_times}
            )
            correlation = len(intersection) / max(
                len(key_times),
                len(other_times)
            )
            
            if correlation >= threshold:
                related.append(other_key)
                
        return related
        
    def _cleanup_old_data(self, current_time: float):
        """Remove data outside the window"""
        cutoff = current_time - self.window_size
        
        for key in list(self.access_times.keys()):
            times = self.access_times[key]
            valid_times = [t for t in times if t > cutoff]
            
            if valid_times:
                self.access_times[key] = valid_times
            else:
                del self.access_times[key]
                del self.access_counts[key]
                
        self.pattern_cache.clear()
        
    def _find_peaks(self, data: np.ndarray) -> List[float]:
        """Find significant peaks in data"""
        # Use basic peak detection
        peaks = []
        for i in range(1, len(data) - 1):
            if data[i] > data[i-1] and data[i] > data[i+1]:
                if data[i] > np.mean(data) + np.std(data):
                    peaks.append(float(i))
        return peaks
        
    def _calculate_confidence(
        self,
        intervals: np.ndarray,
        period: float
    ) -> float:
        """Calculate confidence in periodic pattern"""
        # Count intervals matching the period
        matches = sum(
            1 for interval in intervals
            if abs(interval - period) < period * 0.1
        )
        return matches / len(intervals)

class WarmingStrategy(ABC):
    """Base class for cache warming strategies"""
    
    @abstractmethod
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming"""
        pass

class TimeBasedWarming(WarmingStrategy):
    """Warm cache based on time patterns"""
    
    def __init__(self, redis: aioredis.Redis, access_pattern: AccessPattern):
        self.redis = redis
        self.access_pattern = access_pattern
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        candidates = []
        keys = await self.redis.keys(pattern)
        
        for key in keys:
            next_access = self.access_pattern.predict_next_access(key)
            if next_access:
                # Warm if predicted access is within warming window
                window = config.get("warm_window", 300)  # 5 minutes default
                if 0 <= next_access - time.time() <= window:
                    candidates.append(key)
                    
        return candidates[:config.get("batch_size", 100)]

class RelatedKeyWarming(WarmingStrategy):
    """Warm related keys based on access patterns"""
    
    def __init__(self, redis: aioredis.Redis, access_pattern: AccessPattern):
        self.redis = redis
        self.access_pattern = access_pattern
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        candidates = set()
        keys = await self.redis.keys(pattern)
        
        for key in keys:
            if await self.redis.exists(key):
                related = self.access_pattern.get_related_keys(
                    key,
                    config.get("correlation_threshold", 0.8)
                )
                candidates.update(
                    key for key in related
                    if not await self.redis.exists(key)
                )
                
        return list(candidates)[:config.get("batch_size", 100)]

class HybridWarming(WarmingStrategy):
    """Combines multiple warming strategies"""
    
    def __init__(self, strategies: List[WarmingStrategy]):
        self.strategies = strategies
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        all_candidates = set()
        
        for strategy in self.strategies:
            candidates = await strategy.get_warming_candidates(
                pattern,
                config
            )
            all_candidates.update(candidates)
            
        return list(all_candidates)[:config.get("batch_size", 100)]

class ReplicationManager:
    """Manages cache replication across nodes"""
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        replication_factor: int = 2
    ):
        self.nodes = nodes
        self.replication_factor = min(replication_factor, len(nodes))
        self.node_health: Dict[str, bool] = {
            f"{node['host']}:{node['port']}": True
            for node in nodes
        }
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start health checking"""
        self._health_check_task = asyncio.create_task(
            self._periodic_health_check()
        )
        
    async def stop(self):
        """Stop health checking"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
                
    async def get_replica_nodes(
        self,
        key: str,
        exclude_unhealthy: bool = True
    ) -> List[Dict[str, Any]]:
        """Get nodes for key replication"""
        available_nodes = [
            node for node in self.nodes
            if not exclude_unhealthy or
            self.node_health[f"{node['host']}:{node['port']}"]
        ]
        
        if not available_nodes:
            raise RuntimeError("No healthy nodes available")
            
        # Use consistent hashing to select primary node
        hash_val = hash(key)
        start_idx = hash_val % len(available_nodes)
        
        # Get replica nodes using ring distribution
        replicas = []
        for i in range(self.replication_factor):
            idx = (start_idx + i) % len(available_nodes)
            replicas.append(available_nodes[idx])
            
        return replicas
        
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
                        await redis.ping()
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

class EnhancedMetrics:
    """Enhanced metrics collection for cache operations"""
    
    def __init__(self, metrics: HandlerMetrics):
        self.metrics = metrics
        self.start_times: Dict[str, float] = {}
        
    async def record_operation_start(self, operation: str, key: str):
        """Record operation start time"""
        op_key = f"{operation}:{key}"
        self.start_times[op_key] = time.time()
        
    async def record_operation_end(
        self,
        operation: str,
        key: str,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record operation completion"""
        op_key = f"{operation}:{key}"
        start_time = self.start_times.pop(op_key, None)
        
        if start_time:
            duration = time.time() - start_time
            
            # Record operation duration
            await self.metrics.record_processing_time(
                f"cache_{operation}",
                duration
            )
            
            # Record operation result
            await self.metrics.record_metric(
                f"cache_{operation}",
                1,
                MetricType.COUNTER,
                {
                    "key": key,
                    "success": str(success),
                    **(metadata or {})
                }
            )
            
            # Record latency histogram
            await self.metrics.record_metric(
                f"cache_{operation}_latency",
                duration,
                MetricType.HISTOGRAM,
                {"key": key}
            )

class EvictionStrategy(ABC):
    """Base class for cache eviction strategies"""
    
    def __init__(self, redis: aioredis.Redis):
        self.redis = redis
        
    @abstractmethod
    async def record_access(self, key: str) -> None:
        """Record key access for strategy"""
        pass
        
    @abstractmethod
    async def get_eviction_candidates(self, count: int) -> List[str]:
        """Get keys to evict"""
        pass
        
    @abstractmethod
    async def remove_key(self, key: str) -> None:
        """Remove key from strategy metadata"""
        pass

class LRUStrategy(EvictionStrategy):
    """Least Recently Used strategy"""
    
    async def record_access(self, key: str) -> None:
        await self.redis.zadd(
            "cache:lru",
            {key: datetime.utcnow().timestamp()}
        )
        
    async def get_eviction_candidates(self, count: int) -> List[str]:
        return await self.redis.zrange("cache:lru", 0, count - 1)
        
    async def remove_key(self, key: str) -> None:
        await self.redis.zrem("cache:lru", key)

class LFUStrategy(EvictionStrategy):
    """Least Frequently Used strategy"""
    
    async def record_access(self, key: str) -> None:
        await self.redis.zincrby("cache:lfu", 1, key)
        
    async def get_eviction_candidates(self, count: int) -> List[str]:
        return await self.redis.zrange("cache:lfu", 0, count - 1)
        
    async def remove_key(self, key: str) -> None:
        await self.redis.zrem("cache:lfu", key)

class FIFOStrategy(EvictionStrategy):
    """First In First Out strategy"""
    
    async def record_access(self, key: str) -> None:
        if not await self.redis.zscore("cache:fifo", key):
            await self.redis.zadd(
                "cache:fifo",
                {key: datetime.utcnow().timestamp()}
            )
        
    async def get_eviction_candidates(self, count: int) -> List[str]:
        return await self.redis.zrange("cache:fifo", 0, count - 1)
        
    async def remove_key(self, key: str) -> None:
        await self.redis.zrem("cache:fifo", key)

class RandomStrategy(EvictionStrategy):
    """Random eviction strategy"""
    
    async def record_access(self, key: str) -> None:
        await self.redis.sadd("cache:random", key)
        
    async def get_eviction_candidates(self, count: int) -> List[str]:
        keys = await self.redis.smembers("cache:random")
        return random.sample(list(keys), min(count, len(keys)))
        
    async def remove_key(self, key: str) -> None:
        await self.redis.srem("cache:random", key)

class CacheWarmer:
    """Handles cache warming and prefetching"""
    
    def __init__(
        self,
        redis: aioredis.Redis,
        fetch_handler: callable,
        metrics: Any
    ):
        self.redis = redis
        self.fetch_handler = fetch_handler
        self.metrics = metrics
        self.warming_patterns: Dict[str, Dict] = {}
        self._warm_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start cache warming"""
        self._warm_task = asyncio.create_task(self._periodic_warm())
        
    async def stop(self):
        """Stop cache warming"""
        if self._warm_task:
            self._warm_task.cancel()
            try:
                await self._warm_task
            except asyncio.CancelledError:
                pass
    
    async def register_pattern(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> None:
        """Register a pattern for cache warming"""
        self.warming_patterns[pattern] = {
            "config": config,
            "last_warm": datetime.utcnow()
        }
        
    async def warm_cache(self, pattern: str) -> int:
        """Warm cache for specific pattern"""
        if pattern not in self.warming_patterns:
            raise ValueError(f"Unknown warming pattern: {pattern}")
            
        config = self.warming_patterns[pattern]["config"]
        keys = await self._get_warming_candidates(pattern, config)
        warmed = 0
        
        for key in keys:
            try:
                value = await self.fetch_handler(key)
                if value is not None:
                    await self.redis.set(
                        key,
                        value,
                        ex=config.get("ttl", 3600)
                    )
                    warmed += 1
            except Exception as e:
                logger.error(f"Error warming key {key}: {str(e)}")
                
        self.warming_patterns[pattern]["last_warm"] = datetime.utcnow()
        
        await self.metrics.record_metric(
            "cache_warm",
            warmed,
            "counter",
            {"pattern": pattern}
        )
        
        return warmed
    
    async def _periodic_warm(self):
        """Periodically warm cache"""
        while True:
            try:
                for pattern, info in self.warming_patterns.items():
                    config = info["config"]
                    interval = timedelta(
                        seconds=config.get("warm_interval", 3600)
                    )
                    
                    if (
                        datetime.utcnow() - info["last_warm"]
                        >= interval
                    ):
                        await self.warm_cache(pattern)
                        
                await asyncio.sleep(60)  # Check every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache warming error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming"""
        all_keys = await self.redis.keys(pattern)
        missing_keys = [
            key for key in all_keys
            if not await self.redis.exists(key)
        ]
        
        # Add predictive warming based on access patterns
        if config.get("predictive", False):
            access_patterns = await self._analyze_access_patterns(pattern)
            missing_keys.extend(access_patterns)
            
        return missing_keys[:config.get("batch_size", 100)]
    
    async def _analyze_access_patterns(self, pattern: str) -> List[str]:
        """Analyze access patterns for predictive warming"""
        # Implement your access pattern analysis logic here
        # This could involve analyzing access logs, time-based patterns, etc.
        return []

class DistributedCache:
    """Distributed cache implementation"""
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        strategy: str = "consistent-hashing"
    ):
        self.nodes = nodes
        self.strategy = strategy
        self.ring: Optional[Dict] = None
        self._initialize_ring()
        
    def _initialize_ring(self):
        """Initialize consistent hashing ring"""
        if self.strategy == "consistent-hashing":
            self.ring = {}
            for node in self.nodes:
                for i in range(node.get("virtual_nodes", 100)):
                    hash_key = self._hash_key(
                        f"{node['host']}:{node['port']}#{i}"
                    )
                    self.ring[hash_key] = node
                    
    def _hash_key(self, key: str) -> int:
        """Generate hash for key"""
        return hash(key)
        
    def _get_node(self, key: str) -> Dict[str, Any]:
        """Get node for key using consistent hashing"""
        if not self.ring:
            raise RuntimeError("Ring not initialized")
            
        hash_key = self._hash_key(key)
        nodes = sorted(self.ring.keys())
        
        for node_hash in nodes:
            if hash_key <= node_hash:
                return self.ring[node_hash]
        
        return self.ring[nodes[0]]  # Wrap around
        
    async def get_connection(self, key: str) -> aioredis.Redis:
        """Get Redis connection for key"""
        node = self._get_node(key)
        return await aioredis.from_url(
            f"redis://{node['host']}:{node['port']}"
        )

class StrategyFactory:
    """Factory for creating eviction strategies"""
    
    @staticmethod
    def create_strategy(
        strategy: CacheStrategy,
        redis: aioredis.Redis
    ) -> EvictionStrategy:
        """Create strategy instance"""
        strategies = {
            CacheStrategy.LRU: LRUStrategy,
            CacheStrategy.LFU: LFUStrategy,
            CacheStrategy.FIFO: FIFOStrategy,
            CacheStrategy.RANDOM: RandomStrategy
        }
        
        strategy_class = strategies.get(strategy)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy}")
            
        return strategy_class(redis) 

class MLBasedWarming(WarmingStrategy):
    """Machine learning based warming strategy"""
    
    def __init__(
        self,
        redis: aioredis.Redis,
        access_pattern: AccessPattern,
        model_update_interval: int = 3600
    ):
        self.redis = redis
        self.access_pattern = access_pattern
        self.model_update_interval = model_update_interval
        self.model = RandomForestRegressor(n_estimators=100)
        self.scaler = StandardScaler()
        self.last_update = 0
        self.feature_columns = [
            'hour_of_day',
            'day_of_week',
            'access_count',
            'time_since_last_access',
            'avg_access_interval'
        ]
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming based on ML predictions"""
        # Update model if needed
        if time.time() - self.last_update > self.model_update_interval:
            await self._update_model()
            
        candidates = []
        keys = await self.redis.keys(pattern)
        
        # Prepare features for prediction
        features = await self._prepare_features(keys)
        if features.empty:
            return []
            
        # Make predictions
        X = self.scaler.transform(features[self.feature_columns])
        predictions = self.model.predict(X)
        
        # Select keys with high access probability
        threshold = config.get('probability_threshold', 0.7)
        for key, prob in zip(features.index, predictions):
            if prob >= threshold and not await self.redis.exists(key):
                candidates.append(key)
                
        return candidates[:config.get('batch_size', 100)]
        
    async def _update_model(self):
        """Update the ML model with recent data"""
        # Collect training data
        data = []
        for key, times in self.access_pattern.access_times.items():
            if len(times) < 2:
                continue
                
            for i in range(1, len(times)):
                row = {
                    'key': key,
                    'hour_of_day': datetime.fromtimestamp(times[i]).hour,
                    'day_of_week': datetime.fromtimestamp(times[i]).weekday(),
                    'access_count': len(times[:i]),
                    'time_since_last_access': times[i] - times[i-1],
                    'avg_access_interval': np.mean(np.diff(times[:i])),
                    'was_accessed': 1.0
                }
                data.append(row)
                
            # Add negative samples
            gaps = self._find_access_gaps(times)
            for gap_start, gap_end in gaps:
                row = {
                    'key': key,
                    'hour_of_day': datetime.fromtimestamp(gap_start).hour,
                    'day_of_week': datetime.fromtimestamp(gap_start).weekday(),
                    'access_count': len(times),
                    'time_since_last_access': gap_start - times[-1],
                    'avg_access_interval': np.mean(np.diff(times)),
                    'was_accessed': 0.0
                }
                data.append(row)
                
        if not data:
            return
            
        # Prepare training data
        df = pd.DataFrame(data)
        X = df[self.feature_columns]
        y = df['was_accessed']
        
        # Train model
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)
        self.model.fit(X_scaled, y)
        
        self.last_update = time.time()
        
    async def _prepare_features(self, keys: List[str]) -> pd.DataFrame:
        """Prepare features for prediction"""
        data = []
        now = time.time()
        
        for key in keys:
            times = self.access_pattern.access_times.get(key, [])
            if not times:
                continue
                
            row = {
                'key': key,
                'hour_of_day': datetime.fromtimestamp(now).hour,
                'day_of_week': datetime.fromtimestamp(now).weekday(),
                'access_count': len(times),
                'time_since_last_access': now - times[-1],
                'avg_access_interval': np.mean(np.diff(times))
                if len(times) > 1 else 0
            }
            data.append(row)
            
        return pd.DataFrame(data).set_index('key')
        
    def _find_access_gaps(
        self,
        times: List[float],
        min_gap: float = 3600
    ) -> List[Tuple[float, float]]:
        """Find significant gaps in access times"""
        gaps = []
        for i in range(1, len(times)):
            gap = times[i] - times[i-1]
            if gap >= min_gap:
                gaps.append((times[i-1] + gap/4, times[i-1] + gap*3/4))
        return gaps

class SeasonalWarming(WarmingStrategy):
    """Seasonal pattern based warming strategy"""
    
    def __init__(self, redis: aioredis.Redis, access_pattern: AccessPattern):
        self.redis = redis
        self.access_pattern = access_pattern
        self.seasonal_patterns: Dict[str, Dict[str, float]] = {}
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming based on seasonal patterns"""
        candidates = []
        keys = await self.redis.keys(pattern)
        now = datetime.now()
        
        for key in keys:
            if not await self.redis.exists(key):
                pattern = self._get_seasonal_pattern(key)
                if pattern:
                    score = self._calculate_seasonal_score(pattern, now)
                    if score >= config.get('seasonal_threshold', 0.7):
                        candidates.append(key)
                        
        return candidates[:config.get('batch_size', 100)]
        
    def _get_seasonal_pattern(self, key: str) -> Optional[Dict[str, float]]:
        """Get or compute seasonal pattern for key"""
        if key not in self.seasonal_patterns:
            times = self.access_pattern.access_times.get(key, [])
            if len(times) < 24:  # Need enough data
                return None
                
            pattern = {
                'hourly': self._compute_hourly_pattern(times),
                'daily': self._compute_daily_pattern(times),
                'weekly': self._compute_weekly_pattern(times)
            }
            self.seasonal_patterns[key] = pattern
            
        return self.seasonal_patterns[key]
        
    def _calculate_seasonal_score(
        self,
        pattern: Dict[str, float],
        time: datetime
    ) -> float:
        """Calculate seasonal score for given time"""
        hour_score = pattern['hourly'].get(time.hour, 0)
        day_score = pattern['daily'].get(time.weekday(), 0)
        week_score = pattern['weekly'].get(time.isocalendar()[1] % 52, 0)
        
        return (hour_score + day_score + week_score) / 3
        
    def _compute_hourly_pattern(
        self,
        times: List[float]
    ) -> Dict[int, float]:
        """Compute hourly access pattern"""
        hours = [datetime.fromtimestamp(t).hour for t in times]
        return self._normalize_counts(Counter(hours))
        
    def _compute_daily_pattern(
        self,
        times: List[float]
    ) -> Dict[int, float]:
        """Compute daily access pattern"""
        days = [datetime.fromtimestamp(t).weekday() for t in times]
        return self._normalize_counts(Counter(days))
        
    def _compute_weekly_pattern(
        self,
        times: List[float]
    ) -> Dict[int, float]:
        """Compute weekly access pattern"""
        weeks = [
            datetime.fromtimestamp(t).isocalendar()[1] % 52
            for t in times
        ]
        return self._normalize_counts(Counter(weeks))
        
    def _normalize_counts(self, counts: Counter) -> Dict[Any, float]:
        """Normalize counter values to [0, 1] range"""
        total = sum(counts.values())
        return {k: v/total for k, v in counts.items()}

class QuorumReplication:
    """Quorum-based replication manager"""
    
    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        read_quorum: int,
        write_quorum: int
    ):
        self.nodes = nodes
        self.read_quorum = min(read_quorum, len(nodes))
        self.write_quorum = min(write_quorum, len(nodes))
        self.node_health: Dict[str, bool] = {
            f"{node['host']}:{node['port']}": True
            for node in nodes
        }
        self._health_check_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start health checking"""
        self._health_check_task = asyncio.create_task(
            self._periodic_health_check()
        )
        
    async def stop(self):
        """Stop health checking"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
                
    async def write(
        self,
        key: str,
        value: bytes,
        ttl: Optional[int] = None
    ) -> Tuple[bool, List[str]]:
        """Write value with quorum consensus"""
        healthy_nodes = self._get_healthy_nodes()
        if len(healthy_nodes) < self.write_quorum:
            raise RuntimeError(
                f"Not enough healthy nodes for write quorum "
                f"({len(healthy_nodes)} < {self.write_quorum})"
            )
            
        success_nodes = []
        for node in healthy_nodes:
            try:
                redis = await aioredis.from_url(
                    f"redis://{node['host']}:{node['port']}"
                )
                if await redis.set(key, value, ex=ttl):
                    success_nodes.append(
                        f"{node['host']}:{node['port']}"
                    )
                    if len(success_nodes) >= self.write_quorum:
                        return True, success_nodes
            except Exception as e:
                logger.error(
                    f"Write failed for node {node['host']}:{node['port']}: {e}"
                )
                
        return False, success_nodes
        
    async def read(
        self,
        key: str
    ) -> Tuple[Optional[bytes], List[str], bool]:
        """Read value with quorum consensus"""
        healthy_nodes = self._get_healthy_nodes()
        if len(healthy_nodes) < self.read_quorum:
            raise RuntimeError(
                f"Not enough healthy nodes for read quorum "
                f"({len(healthy_nodes)} < {self.read_quorum})"
            )
            
        values = []
        success_nodes = []
        
        for node in healthy_nodes:
            try:
                redis = await aioredis.from_url(
                    f"redis://{node['host']}:{node['port']}"
                )
                value = await redis.get(key)
                if value is not None:
                    values.append(value)
                    success_nodes.append(
                        f"{node['host']}:{node['port']}"
                    )
                    if len(success_nodes) >= self.read_quorum:
                        # Check consistency
                        consistent = all(v == values[0] for v in values)
                        return values[0], success_nodes, consistent
            except Exception as e:
                logger.error(
                    f"Read failed for node {node['host']}:{node['port']}: {e}"
                )
                
        return None, success_nodes, False
        
    def _get_healthy_nodes(self) -> List[Dict[str, Any]]:
        """Get list of healthy nodes"""
        return [
            node for node in self.nodes
            if self.node_health[f"{node['host']}:{node['port']}"]
        ]
        
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
                        await redis.ping()
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