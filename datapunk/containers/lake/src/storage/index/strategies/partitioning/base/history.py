from typing import List, Dict, Any, Tuple
import time

class PartitionHistory:
    """Tracks historical partition states and changes"""
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        
    def add_snapshot(self, partitions: Dict[str, List[Tuple[float, float]]], 
                    timestamp: float = None):
        """Add a snapshot of partition state"""
        if timestamp is None:
            timestamp = time.time()
            
        self.history.append({
            'timestamp': timestamp,
            'partitions': partitions.copy(),
            'stats': {
                'total_partitions': len(partitions),
                'total_points': sum(len(points) for points in partitions.values())
            }
        })
        
    def get_partition_growth(self, cell_id: str) -> List[Tuple[float, int]]:
        """Track growth of a specific partition over time"""
        return [(snapshot['timestamp'], 
                len(snapshot['partitions'].get(cell_id, [])))
                for snapshot in self.history]
                
    def get_total_points_over_time(self) -> List[Tuple[float, int]]:
        """Get total points at each snapshot"""
        return [(snapshot['timestamp'], 
                snapshot['stats']['total_points'])
                for snapshot in self.history]
                
    def get_partition_count_over_time(self) -> List[Tuple[float, int]]:
        """Get number of partitions at each snapshot"""
        return [(snapshot['timestamp'], 
                snapshot['stats']['total_partitions'])
                for snapshot in self.history]
                
    def clear(self):
        """Clear all history"""
        self.history.clear() 