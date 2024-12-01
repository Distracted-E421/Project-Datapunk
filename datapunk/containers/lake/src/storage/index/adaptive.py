from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from enum import Enum
import heapq
import numpy as np
from collections import defaultdict

from .core import IndexBase
from .stats import StatisticsStore
from .optimizer import IndexOptimizer
from .manager import IndexManager

logger = logging.getLogger(__name__)

class PartitionStrategy(Enum):
    """Index partitioning strategies."""
    RANGE = "range"
    HASH = "hash"
    LIST = "list"
    COMPOSITE = "composite"
    TIME_SERIES = "time_series"

@dataclass
class PartitionInfo:
    """Information about an index partition."""
    partition_key: str
    strategy: PartitionStrategy
    boundaries: List[Any]
    size_bytes: int
    record_count: int
    last_accessed: datetime
    hot_data: bool = False

@dataclass
class QueryPattern:
    """Represents a query access pattern."""
    pattern_id: str
    query_type: str
    predicates: List[str]
    frequency: int
    avg_execution_time: float
    last_seen: datetime
    affected_indexes: Set[str]

class AdaptiveIndexManager:
    """Manages adaptive indexing and partitioning."""
    
    def __init__(
        self,
        store: StatisticsStore,
        manager: IndexManager,
        optimizer: IndexOptimizer,
        config_path: Optional[Union[str, Path]] = None
    ):
        self.store = store
        self.manager = manager
        self.optimizer = optimizer
        self.config_path = Path(config_path) if config_path else None
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.partitions: Dict[str, List[PartitionInfo]] = {}
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.maintenance_schedule: List[Tuple[datetime, str, str]] = []
        self.index_scores: Dict[str, float] = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path or not self.config_path.exists():
            return {
                "partition_size_threshold": 1024 * 1024 * 100,  # 100MB
                "max_partitions_per_index": 100,
                "hot_data_threshold_days": 7,
                "pattern_expiry_days": 30,
                "min_pattern_frequency": 5,
                "score_weights": {
                    "query_frequency": 0.4,
                    "data_size": 0.2,
                    "maintenance_cost": 0.2,
                    "access_pattern": 0.2
                },
                "maintenance_window": {
                    "start_hour": 1,
                    "end_hour": 5
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def analyze_query_pattern(
        self,
        query_type: str,
        predicates: List[str],
        execution_time: float,
        affected_indexes: Set[str]
    ):
        """Analyze and record query pattern."""
        # Generate pattern ID
        pattern_id = f"{query_type}_{'-'.join(sorted(predicates))}"
        
        # Update or create pattern
        if pattern_id in self.query_patterns:
            pattern = self.query_patterns[pattern_id]
            pattern.frequency += 1
            pattern.avg_execution_time = (
                (pattern.avg_execution_time * (pattern.frequency - 1) + execution_time)
                / pattern.frequency
            )
            pattern.last_seen = datetime.now()
            pattern.affected_indexes.update(affected_indexes)
        else:
            self.query_patterns[pattern_id] = QueryPattern(
                pattern_id=pattern_id,
                query_type=query_type,
                predicates=predicates,
                frequency=1,
                avg_execution_time=execution_time,
                last_seen=datetime.now(),
                affected_indexes=affected_indexes
            )
            
        # Clean up old patterns
        self._cleanup_patterns()
        
        # Update index scores
        self._update_index_scores()
        
    def _cleanup_patterns(self):
        """Remove expired query patterns."""
        expiry = datetime.now() - timedelta(
            days=self.config["pattern_expiry_days"]
        )
        min_frequency = self.config["min_pattern_frequency"]
        
        expired = [
            pid for pid, pattern in self.query_patterns.items()
            if (
                pattern.last_seen < expiry or
                pattern.frequency < min_frequency
            )
        ]
        
        for pid in expired:
            del self.query_patterns[pid]
            
    def _update_index_scores(self):
        """Update scores for all indexes based on patterns."""
        weights = self.config["score_weights"]
        
        for index_id in self.manager.list_indexes():
            # Get index statistics
            stats = self.store.get_latest_stats(index_id)
            if not stats:
                continue
                
            # Calculate score components
            query_score = self._calculate_query_score(index_id)
            size_score = self._calculate_size_score(stats.size.size_bytes)
            maintenance_score = self._calculate_maintenance_score(stats)
            pattern_score = self._calculate_pattern_score(index_id)
            
            # Compute weighted score
            self.index_scores[index_id] = (
                query_score * weights["query_frequency"] +
                size_score * weights["data_size"] +
                maintenance_score * weights["maintenance_cost"] +
                pattern_score * weights["access_pattern"]
            )
            
    def _calculate_query_score(self, index_id: str) -> float:
        """Calculate score based on query frequency."""
        total_queries = sum(p.frequency for p in self.query_patterns.values())
        if total_queries == 0:
            return 0.0
            
        index_queries = sum(
            p.frequency
            for p in self.query_patterns.values()
            if index_id in p.affected_indexes
        )
        
        return index_queries / total_queries
        
    def _calculate_size_score(self, size_bytes: int) -> float:
        """Calculate score based on data size."""
        threshold = self.config["partition_size_threshold"]
        return 1.0 - min(size_bytes / threshold, 1.0)
        
    def _calculate_maintenance_score(self, stats: Any) -> float:
        """Calculate score based on maintenance costs."""
        # Higher score means lower maintenance cost
        fragmentation_penalty = stats.size.fragmentation_ratio
        update_frequency = (
            stats.usage.total_writes /
            (stats.usage.total_reads + 1)
        )
        
        return 1.0 - (fragmentation_penalty * 0.5 + update_frequency * 0.5)
        
    def _calculate_pattern_score(self, index_id: str) -> float:
        """Calculate score based on access patterns."""
        recent_patterns = [
            p for p in self.query_patterns.values()
            if (
                index_id in p.affected_indexes and
                (datetime.now() - p.last_seen).days <= 7
            )
        ]
        
        if not recent_patterns:
            return 0.0
            
        # Consider pattern diversity and recency
        pattern_count = len(recent_patterns)
        avg_recency = np.mean([
            (7 - (datetime.now() - p.last_seen).days) / 7
            for p in recent_patterns
        ])
        
        return (pattern_count / 10) * 0.5 + avg_recency * 0.5
        
    def recommend_partitioning(
        self,
        index_id: str
    ) -> Optional[Tuple[PartitionStrategy, List[Any]]]:
        """Recommend partitioning strategy for an index."""
        stats = self.store.get_latest_stats(index_id)
        if not stats:
            return None
            
        # Analyze data distribution and patterns
        patterns = [
            p for p in self.query_patterns.values()
            if index_id in p.affected_indexes
        ]
        
        if not patterns:
            return None
            
        # Analyze predicate types
        predicate_types = defaultdict(int)
        for pattern in patterns:
            for pred in pattern.predicates:
                if "time" in pred.lower() or "date" in pred.lower():
                    predicate_types["time"] += pattern.frequency
                elif pred.startswith("range"):
                    predicate_types["range"] += pattern.frequency
                elif "in" in pred.lower():
                    predicate_types["list"] += pattern.frequency
                else:
                    predicate_types["hash"] += pattern.frequency
                    
        # Select strategy based on dominant pattern
        dominant_type = max(predicate_types.items(), key=lambda x: x[1])[0]
        
        if dominant_type == "time":
            return (
                PartitionStrategy.TIME_SERIES,
                self._generate_time_boundaries(patterns)
            )
        elif dominant_type == "range":
            return (
                PartitionStrategy.RANGE,
                self._generate_range_boundaries(patterns)
            )
        elif dominant_type == "list":
            return (
                PartitionStrategy.LIST,
                self._generate_list_boundaries(patterns)
            )
        else:
            return (
                PartitionStrategy.HASH,
                self._generate_hash_boundaries(
                    stats.size.total_entries
                )
            )
            
    def _generate_time_boundaries(
        self,
        patterns: List[QueryPattern]
    ) -> List[Any]:
        """Generate time-based partition boundaries."""
        # Analyze time ranges in predicates
        time_ranges = []
        for pattern in patterns:
            for pred in pattern.predicates:
                if "time" in pred.lower() or "date" in pred.lower():
                    # Extract time range (simplified)
                    # TODO: Implement proper time range extraction
                    time_ranges.append(datetime.now() - timedelta(days=7))
                    
        if not time_ranges:
            return []
            
        # Create boundaries at regular intervals
        earliest = min(time_ranges)
        latest = max(time_ranges)
        interval = (latest - earliest) / 10  # 10 partitions
        
        return [
            earliest + interval * i
            for i in range(11)  # Include both ends
        ]
        
    def _generate_range_boundaries(
        self,
        patterns: List[QueryPattern]
    ) -> List[Any]:
        """Generate range-based partition boundaries."""
        # TODO: Implement range boundary generation
        return []
        
    def _generate_list_boundaries(
        self,
        patterns: List[QueryPattern]
    ) -> List[Any]:
        """Generate list-based partition boundaries."""
        # TODO: Implement list boundary generation
        return []
        
    def _generate_hash_boundaries(
        self,
        total_entries: int
    ) -> List[Any]:
        """Generate hash-based partition boundaries."""
        num_partitions = min(
            total_entries // 1000000 + 1,  # 1M records per partition
            self.config["max_partitions_per_index"]
        )
        return list(range(0, num_partitions))
        
    def schedule_maintenance(
        self,
        index_id: str,
        operation: str,
        priority: int = 1
    ):
        """Schedule maintenance operation for an index."""
        # Get maintenance window
        window = self.config["maintenance_window"]
        now = datetime.now()
        
        # Find next available slot in maintenance window
        if now.hour >= window["end_hour"]:
            # Schedule for next day
            next_slot = now.replace(
                hour=window["start_hour"],
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=1)
        elif now.hour < window["start_hour"]:
            # Schedule for today
            next_slot = now.replace(
                hour=window["start_hour"],
                minute=0,
                second=0,
                microsecond=0
            )
        else:
            # Schedule for next available minute
            next_slot = now.replace(
                microsecond=0
            ) + timedelta(minutes=1)
            
        # Add to schedule with priority
        heapq.heappush(
            self.maintenance_schedule,
            (priority, next_slot, index_id, operation)
        )
        
    def get_next_maintenance(self) -> Optional[Tuple[datetime, str, str]]:
        """Get next scheduled maintenance operation."""
        while self.maintenance_schedule:
            priority, timestamp, index_id, operation = heapq.heappop(
                self.maintenance_schedule
            )
            
            if timestamp > datetime.now():
                return (timestamp, index_id, operation)
                
        return None
        
    def get_index_recommendations(
        self,
        min_score: float = 0.5
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Get index recommendations based on scores."""
        recommendations = []
        
        for index_id, score in self.index_scores.items():
            if score >= min_score:
                stats = self.store.get_latest_stats(index_id)
                if not stats:
                    continue
                    
                # Generate recommendations
                partition_rec = self.recommend_partitioning(index_id)
                
                recommendations.append((
                    index_id,
                    score,
                    {
                        "current_size": stats.size.size_bytes,
                        "fragmentation": stats.size.fragmentation_ratio,
                        "recommended_partitioning": partition_rec,
                        "maintenance_needed": score < 0.7,
                        "query_patterns": [
                            p.pattern_id
                            for p in self.query_patterns.values()
                            if index_id in p.affected_indexes
                        ]
                    }
                ))
                
        return sorted(
            recommendations,
            key=lambda x: x[1],
            reverse=True
        )