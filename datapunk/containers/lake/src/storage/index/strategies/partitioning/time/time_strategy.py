from typing import List, Dict, Any, Union, Optional, Tuple
from datetime import datetime, timedelta
import pytz
from collections import defaultdict
import pandas as pd
import numpy as np

class TimePartitionStrategy:
    """Time-based partitioning strategy with flexible granularity"""
    
    def __init__(self, time_field: str = 'timestamp',
                 default_granularity: str = 'day',
                 timezone: str = 'UTC'):
        self.time_field = time_field
        self.default_granularity = default_granularity
        self.timezone = pytz.timezone(timezone)
        self.partitions = defaultdict(list)
        self.partition_stats = {}
        
    def _normalize_timestamp(self, timestamp: Union[str, datetime]) -> datetime:
        """Normalize timestamp to timezone-aware datetime"""
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        if timestamp.tzinfo is None:
            timestamp = self.timezone.localize(timestamp)
        return timestamp
    
    def _get_partition_key(self, timestamp: datetime, 
                          granularity: str = None) -> str:
        """Get partition key based on granularity"""
        granularity = granularity or self.default_granularity
        
        if granularity == 'year':
            return timestamp.strftime('%Y')
        elif granularity == 'month':
            return timestamp.strftime('%Y-%m')
        elif granularity == 'day':
            return timestamp.strftime('%Y-%m-%d')
        elif granularity == 'hour':
            return timestamp.strftime('%Y-%m-%d-%H')
        elif granularity == 'minute':
            return timestamp.strftime('%Y-%m-%d-%H-%M')
        else:
            raise ValueError(f"Unsupported granularity: {granularity}")
    
    def partition_data(self, data: List[Dict[str, Any]], 
                      granularity: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Partition data based on time intervals"""
        granularity = granularity or self.default_granularity
        partitions = defaultdict(list)
        
        for record in data:
            timestamp = self._normalize_timestamp(record[self.time_field])
            partition_key = self._get_partition_key(timestamp, granularity)
            partitions[partition_key].append(record)
            
        # Update partition statistics
        for key, records in partitions.items():
            self.partition_stats[key] = {
                'count': len(records),
                'start_time': min(r[self.time_field] for r in records),
                'end_time': max(r[self.time_field] for r in records)
            }
            
        return dict(partitions)
    
    def get_partition_for_time(self, timestamp: Union[str, datetime],
                             granularity: str = None) -> str:
        """Get partition key for a given timestamp"""
        timestamp = self._normalize_timestamp(timestamp)
        return self._get_partition_key(timestamp, granularity)
    
    def get_partitions_in_range(self, start_time: Union[str, datetime],
                               end_time: Union[str, datetime],
                               granularity: str = None) -> List[str]:
        """Get list of partition keys within a time range"""
        start_time = self._normalize_timestamp(start_time)
        end_time = self._normalize_timestamp(end_time)
        granularity = granularity or self.default_granularity
        
        partitions = []
        current_time = start_time
        
        # Calculate time delta based on granularity
        if granularity == 'year':
            delta = timedelta(days=365)
        elif granularity == 'month':
            delta = timedelta(days=30)
        elif granularity == 'day':
            delta = timedelta(days=1)
        elif granularity == 'hour':
            delta = timedelta(hours=1)
        else:  # minute
            delta = timedelta(minutes=1)
            
        while current_time <= end_time:
            partitions.append(self._get_partition_key(current_time, granularity))
            current_time += delta
            
        return partitions
    
    def analyze_partition_distribution(self) -> Dict[str, Any]:
        """Analyze distribution of data across partitions"""
        if not self.partition_stats:
            return {}
            
        counts = [stats['count'] for stats in self.partition_stats.values()]
        return {
            'total_partitions': len(self.partition_stats),
            'total_records': sum(counts),
            'records_per_partition': {
                'mean': float(np.mean(counts)),
                'median': float(np.median(counts)),
                'std': float(np.std(counts)),
                'min': float(np.min(counts)),
                'max': float(np.max(counts))
            },
            'partition_details': self.partition_stats
        }
    
    def suggest_optimal_granularity(self, data: List[Dict[str, Any]], 
                                  target_partition_size: int = 1000) -> str:
        """Suggest optimal time granularity based on data distribution"""
        if not data:
            return self.default_granularity
            
        # Get time range
        timestamps = [self._normalize_timestamp(r[self.time_field]) for r in data]
        time_range = max(timestamps) - min(timestamps)
        records_per_day = len(data) / (time_range.total_seconds() / 86400)
        
        if records_per_day < target_partition_size / 365:
            return 'year'
        elif records_per_day < target_partition_size / 30:
            return 'month'
        elif records_per_day < target_partition_size:
            return 'day'
        elif records_per_day < target_partition_size * 24:
            return 'hour'
        else:
            return 'minute'
    
    def get_partition_boundaries(self, partition_key: str) -> Tuple[datetime, datetime]:
        """Get start and end timestamps for a partition"""
        granularity = len(partition_key.split('-'))
        
        if granularity == 1:  # year
            year = int(partition_key)
            start = datetime(year, 1, 1)
            end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
        elif granularity == 2:  # month
            year, month = map(int, partition_key.split('-'))
            start = datetime(year, month, 1)
            if month == 12:
                end = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
            else:
                end = datetime(year, month + 1, 1) - timedelta(microseconds=1)
        elif granularity == 3:  # day
            year, month, day = map(int, partition_key.split('-'))
            start = datetime(year, month, day)
            end = start + timedelta(days=1) - timedelta(microseconds=1)
        elif granularity == 4:  # hour
            year, month, day, hour = map(int, partition_key.split('-'))
            start = datetime(year, month, day, hour)
            end = start + timedelta(hours=1) - timedelta(microseconds=1)
        else:  # minute
            year, month, day, hour, minute = map(int, partition_key.split('-'))
            start = datetime(year, month, day, hour, minute)
            end = start + timedelta(minutes=1) - timedelta(microseconds=1)
            
        return (self.timezone.localize(start), 
                self.timezone.localize(end))
    
    def merge_partitions(self, partition_keys: List[str]) -> Optional[str]:
        """Merge multiple partitions into a coarser granularity"""
        if not partition_keys:
            return None
            
        # Get timestamps from partition keys
        timestamps = []
        for key in partition_keys:
            start, _ = self.get_partition_boundaries(key)
            timestamps.append(start)
            
        # Find common granularity
        min_time = min(timestamps)
        max_time = max(timestamps)
        time_range = max_time - min_time
        
        if time_range.days > 365:
            return self._get_partition_key(min_time, 'year')
        elif time_range.days > 30:
            return self._get_partition_key(min_time, 'month')
        elif time_range.days > 1:
            return self._get_partition_key(min_time, 'day')
        elif time_range.seconds > 3600:
            return self._get_partition_key(min_time, 'hour')
        else:
            return self._get_partition_key(min_time, 'minute')