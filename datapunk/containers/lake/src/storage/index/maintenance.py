from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import time
import logging
from datetime import datetime, timedelta
from .core import Index, IndexType
from .advisor import IndexAdvisor, QueryPattern, ColumnStats

class IndexUsageStats:
    """Tracks usage statistics for an index."""
    
    def __init__(self, index: Index):
        self.index = index
        self.total_lookups = 0
        self.total_updates = 0
        self.total_range_scans = 0
        self.lookup_time_ms = 0
        self.update_time_ms = 0
        self.last_used = datetime.now()
        self.last_rebuilt = datetime.now()
        self.size_bytes = 0
        self.fragmentation = 0.0  # Percentage of fragmented space
        
    def record_lookup(self, duration_ms: float) -> None:
        """Record a lookup operation."""
        self.total_lookups += 1
        self.lookup_time_ms += duration_ms
        self.last_used = datetime.now()
        
    def record_update(self, duration_ms: float) -> None:
        """Record an update operation."""
        self.total_updates += 1
        self.update_time_ms += duration_ms
        self.last_used = datetime.now()
        
    def record_range_scan(self) -> None:
        """Record a range scan operation."""
        self.total_range_scans += 1
        self.last_used = datetime.now()
        
    def get_average_lookup_time(self) -> float:
        """Get average lookup time in milliseconds."""
        return self.lookup_time_ms / self.total_lookups if self.total_lookups > 0 else 0
        
    def get_average_update_time(self) -> float:
        """Get average update time in milliseconds."""
        return self.update_time_ms / self.total_updates if self.total_updates > 0 else 0

class IndexMaintenanceManager:
    """Manages index maintenance and statistics collection."""
    
    def __init__(self, advisor: IndexAdvisor):
        self.advisor = advisor
        self.usage_stats: Dict[str, IndexUsageStats] = {}
        self.rebuild_threshold = 30.0  # Rebuild if fragmentation > 30%
        self.unused_days_threshold = 30  # Consider dropping if unused for 30 days
        self.logger = logging.getLogger(__name__)
        
    def register_index(self, index: Index) -> None:
        """Register an index for maintenance tracking."""
        self.usage_stats[index.name] = IndexUsageStats(index)
        self.advisor.register_existing_index(index)
        
    def record_operation(self, index_name: str, operation: str, 
                        duration_ms: Optional[float] = None) -> None:
        """Record an index operation."""
        if index_name not in self.usage_stats:
            return
            
        stats = self.usage_stats[index_name]
        if operation == "lookup":
            stats.record_lookup(duration_ms or 0)
        elif operation == "update":
            stats.record_update(duration_ms or 0)
        elif operation == "range_scan":
            stats.record_range_scan()
            
    def update_statistics(self, index_name: str, size_bytes: int,
                         fragmentation: float) -> None:
        """Update size and fragmentation statistics."""
        if index_name not in self.usage_stats:
            return
            
        stats = self.usage_stats[index_name]
        stats.size_bytes = size_bytes
        stats.fragmentation = fragmentation
        
    def analyze_maintenance_needs(self) -> Dict[str, List[str]]:
        """Analyze indexes and provide maintenance recommendations."""
        recommendations = defaultdict(list)
        now = datetime.now()
        
        for index_name, stats in self.usage_stats.items():
            index = stats.index
            table_name = index.table_name
            
            # Check fragmentation
            if stats.fragmentation > self.rebuild_threshold:
                recommendations[table_name].append(
                    f"Rebuild index {index_name} (fragmentation: {stats.fragmentation:.1f}%)")
                    
            # Check usage
            days_unused = (now - stats.last_used).days
            if days_unused > self.unused_days_threshold:
                recommendations[table_name].append(
                    f"Consider dropping unused index {index_name} "
                    f"(not used for {days_unused} days)")
                    
            # Check performance
            avg_lookup = stats.get_average_lookup_time()
            if avg_lookup > 100:  # More than 100ms
                recommendations[table_name].append(
                    f"Investigate slow index {index_name} "
                    f"(avg lookup: {avg_lookup:.1f}ms)")
                    
        return dict(recommendations)
        
    def get_index_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get comprehensive statistics for all indexes."""
        result = {}
        for index_name, stats in self.usage_stats.items():
            result[index_name] = {
                "total_lookups": stats.total_lookups,
                "total_updates": stats.total_updates,
                "total_range_scans": stats.total_range_scans,
                "avg_lookup_time_ms": stats.get_average_lookup_time(),
                "avg_update_time_ms": stats.get_average_update_time(),
                "size_bytes": stats.size_bytes,
                "fragmentation": stats.fragmentation,
                "days_since_last_use": (datetime.now() - stats.last_used).days,
                "days_since_rebuild": (datetime.now() - stats.last_rebuilt).days
            }
        return result
        
    def perform_maintenance(self, index_name: str) -> None:
        """Perform maintenance on an index."""
        if index_name not in self.usage_stats:
            return
            
        stats = self.usage_stats[index_name]
        index = stats.index
        
        try:
            # Rebuild the index
            start_time = time.time()
            index.rebuild()
            duration = time.time() - start_time
            
            # Update statistics
            stats.last_rebuilt = datetime.now()
            stats.fragmentation = 0.0
            
            self.logger.info(
                f"Successfully rebuilt index {index_name} in {duration:.2f} seconds")
        except Exception as e:
            self.logger.error(f"Failed to rebuild index {index_name}: {str(e)}")
            
    def collect_query_patterns(self, index_name: str, 
                             columns: List[str], is_range: bool = False) -> None:
        """Collect query patterns for the advisor."""
        if index_name not in self.usage_stats:
            return
            
        stats = self.usage_stats[index_name]
        index = stats.index
        
        # Create query pattern based on usage
        pattern = QueryPattern(
            table_name=index.table_name,
            columns=columns,
            is_equality=not is_range,
            is_range=is_range,
            frequency=stats.total_lookups + stats.total_range_scans
        )
        
        self.advisor.add_query_pattern(pattern) 