from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
import bisect
from .time_strategy import TimePartitionStrategy

class TemporalIndex:
    def __init__(self, time_field: str):
        self.time_field = time_field
        self.time_ranges = []  # Sorted list of time range boundaries
        self.range_to_partition = {}  # Maps time ranges to partition IDs
        self.partition_stats = defaultdict(dict)  # Statistics per partition
        self.hot_ranges = set()  # Recently accessed ranges
        
    def add_partition(self, partition_id: str, 
                     start_time: datetime,
                     end_time: datetime,
                     stats: Dict[str, Any] = None):
        """Add a new partition to the temporal index"""
        time_range = (start_time, end_time)
        bisect.insort(self.time_ranges, time_range)
        self.range_to_partition[time_range] = partition_id
        
        if stats:
            self.partition_stats[partition_id].update(stats)
            
    def find_partitions(self, start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> List[str]:
        """Find relevant partitions for a time range query"""
        if not (start_time or end_time):
            return list(self.range_to_partition.values())
            
        relevant_ranges = []
        for range_start, range_end in self.time_ranges:
            if start_time and range_end < start_time:
                continue
            if end_time and range_start > end_time:
                break
            relevant_ranges.append((range_start, range_end))
            
        # Update hot ranges
        for time_range in relevant_ranges:
            self.hot_ranges.add(time_range)
            
        return [self.range_to_partition[r] for r in relevant_ranges]
        
class TemporalIndexManager:
    def __init__(self, strategy: TimePartitionStrategy):
        self.strategy = strategy
        self.primary_index = TemporalIndex(strategy.time_field)
        self.secondary_indexes = {}
        self.index_stats = defaultdict(lambda: {
            'hits': 0,
            'misses': 0,
            'scan_time': timedelta(0)
        })
        
    def create_secondary_index(self, name: str,
                             granularity: str,
                             retention_period: Optional[timedelta] = None):
        """Create a secondary temporal index with specific granularity"""
        self.secondary_indexes[name] = {
            'index': TemporalIndex(self.strategy.time_field),
            'granularity': granularity,
            'retention_period': retention_period
        }
        
    def add_partition(self, partition_id: str,
                     start_time: datetime,
                     end_time: datetime,
                     stats: Dict[str, Any] = None):
        """Add partition to all relevant indexes"""
        # Add to primary index
        self.primary_index.add_partition(partition_id, start_time, end_time, stats)
        
        # Add to secondary indexes with appropriate granularity
        for idx_name, idx_info in self.secondary_indexes.items():
            granular_start = self._adjust_to_granularity(start_time, idx_info['granularity'])
            granular_end = self._adjust_to_granularity(end_time, idx_info['granularity'])
            idx_info['index'].add_partition(partition_id, granular_start, granular_end, stats)
            
    def find_best_index(self, query_range: tuple) -> TemporalIndex:
        """Find the most appropriate index for a query"""
        start_time, end_time = query_range
        if not (start_time and end_time):
            return self.primary_index
            
        # Calculate query span
        span = end_time - start_time
        
        # Find index with closest matching granularity
        best_index = self.primary_index
        best_granularity_diff = float('inf')
        
        for idx_name, idx_info in self.secondary_indexes.items():
            gran_diff = abs(self._granularity_to_timedelta(idx_info['granularity']) - span)
            if gran_diff < best_granularity_diff:
                # Check retention period
                if (idx_info['retention_period'] and 
                    datetime.now() - start_time <= idx_info['retention_period']):
                    best_index = idx_info['index']
                    best_granularity_diff = gran_diff
                    
        return best_index
        
    def optimize_indexes(self):
        """Optimize index structure based on usage patterns"""
        # Remove expired data from secondary indexes
        self._cleanup_expired_data()
        
        # Analyze access patterns
        hot_ranges = self._analyze_access_patterns()
        
        # Create new indexes if needed
        self._create_optimized_indexes(hot_ranges)
        
    def _cleanup_expired_data(self):
        """Remove expired data from secondary indexes"""
        now = datetime.now()
        for idx_name, idx_info in list(self.secondary_indexes.items()):
            if idx_info['retention_period']:
                cutoff = now - idx_info['retention_period']
                new_ranges = []
                for start, end in idx_info['index'].time_ranges:
                    if end >= cutoff:
                        new_ranges.append((start, end))
                idx_info['index'].time_ranges = new_ranges
                
    def _analyze_access_patterns(self) -> Dict[str, int]:
        """Analyze access patterns to identify hot ranges"""
        hot_ranges = defaultdict(int)
        for idx in [self.primary_index] + [i['index'] for i in self.secondary_indexes.values()]:
            for time_range in idx.hot_ranges:
                hot_ranges[self._get_range_granularity(time_range)] += 1
        return hot_ranges
        
    def _create_optimized_indexes(self, hot_ranges: Dict[str, int]):
        """Create new optimized indexes based on access patterns"""
        # Find most common granularities
        common_granularities = sorted(
            hot_ranges.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Keep top 3 most accessed granularities
        
        # Create or update indexes
        for granularity, _ in common_granularities:
            if not any(i['granularity'] == granularity for i in self.secondary_indexes.values()):
                self.create_secondary_index(
                    f"auto_index_{granularity}",
                    granularity,
                    retention_period=timedelta(days=30)  # Default retention
                )
                
    def _adjust_to_granularity(self, dt: datetime, granularity: str) -> datetime:
        """Adjust datetime to specified granularity"""
        if granularity == 'year':
            return datetime(dt.year, 1, 1)
        elif granularity == 'month':
            return datetime(dt.year, dt.month, 1)
        elif granularity == 'day':
            return datetime(dt.year, dt.month, dt.day)
        elif granularity == 'hour':
            return datetime(dt.year, dt.month, dt.day, dt.hour)
        return dt
        
    def _granularity_to_timedelta(self, granularity: str) -> timedelta:
        """Convert granularity string to timedelta"""
        if granularity == 'year':
            return timedelta(days=365)
        elif granularity == 'month':
            return timedelta(days=30)
        elif granularity == 'day':
            return timedelta(days=1)
        elif granularity == 'hour':
            return timedelta(hours=1)
        return timedelta(0)
        
    def _get_range_granularity(self, time_range: tuple) -> str:
        """Determine appropriate granularity for a time range"""
        start, end = time_range
        span = end - start
        
        if span >= timedelta(days=365):
            return 'year'
        elif span >= timedelta(days=30):
            return 'month'
        elif span >= timedelta(days=1):
            return 'day'
        elif span >= timedelta(hours=1):
            return 'hour'
        return 'minute' 