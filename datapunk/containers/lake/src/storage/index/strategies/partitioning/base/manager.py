from typing import Dict, List, Tuple, Any, Set
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import numpy as np
from shapely.geometry import Polygon, Point

from ..grid.factory import GridFactory
from .cache import SpatialCache
from .history import PartitionHistory
from ..clustering.density import DensityAnalyzer
from ..clustering.advanced import AdvancedClusterAnalyzer
from ..clustering.balancer import LoadBalancer
from ..time.strategy import TimePartitionStrategy
from ..distributed.manager import DistributedPartitionManager

class GridPartitionManager:
    """Main manager class for grid-based partitioning"""
    
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        
        # Initialize analyzers and managers
        self.density_analyzer = DensityAnalyzer(self)
        self.advanced_analyzer = AdvancedClusterAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.time_strategy = TimePartitionStrategy('timestamp')
        self.distributed_manager = DistributedPartitionManager()
        
    def partition_points(self, points: List[Tuple[float, float]], 
                        precision: int,
                        batch_size: int = 1000) -> Dict[str, List[Tuple[float, float]]]:
        """Partition points with batch processing support"""
        partitions = defaultdict(list)
        
        def process_batch(batch):
            batch_partitions = defaultdict(list)
            for lat, lng in batch:
                try:
                    cell_id = self.grid.encode_point(lat, lng, precision)
                    batch_partitions[cell_id].append((lat, lng))
                    self._recovery_state[f"{lat},{lng}"] = cell_id
                except Exception as e:
                    print(f"Error partitioning point ({lat}, {lng}): {str(e)}")
            return batch_partitions
        
        # Process points in batches using ThreadPoolExecutor
        with ThreadPoolExecutor() as executor:
            futures = []
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                futures.append(executor.submit(process_batch, batch))
            
            # Collect results
            for future in futures:
                batch_results = future.result()
                for cell_id, cell_points in batch_results.items():
                    partitions[cell_id].extend(cell_points)
        
        # Check if rebalancing is needed
        if self._needs_rebalancing(partitions):
            partitions = self._rebalance_partitions(partitions, precision)
        
        # Save historical snapshot
        self.history.add_snapshot(partitions)
        
        return dict(partitions)
    
    def _needs_rebalancing(self, partitions: Dict[str, List[Tuple[float, float]]]) -> bool:
        """Check if partitions need rebalancing"""
        if not partitions:
            return False
            
        # Calculate points per partition statistics
        points_per_partition = [len(points) for points in partitions.values()]
        avg_points = np.mean(points_per_partition)
        max_points = max(points_per_partition)
        
        # Check if any partition exceeds threshold
        return (max_points > self.max_points_per_partition or
                max_points > avg_points * (1 + self.rebalance_threshold))
    
    def _rebalance_partitions(self, partitions: Dict[str, List[Tuple[float, float]]], 
                             precision: int) -> Dict[str, List[Tuple[float, float]]]:
        """Rebalance partitions by splitting or merging"""
        new_partitions = defaultdict(list)
        
        for cell_id, points in partitions.items():
            if len(points) > self.max_points_per_partition:
                # Split partition
                new_precision = precision + 1
                for lat, lng in points:
                    new_cell = self.grid.encode_point(lat, lng, new_precision)
                    new_partitions[new_cell].append((lat, lng))
                    self._recovery_state[f"{lat},{lng}"] = new_cell
            else:
                new_partitions[cell_id] = points
        
        return dict(new_partitions)
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        polygon = self.grid.get_cell_polygon(cell_id)
        self.cache.set(cell_id, polygon)
        return polygon
    
    def partition_polygon(self, polygon: Polygon, precision: int) -> Set[str]:
        """Find all grid cells that intersect with a polygon"""
        # Get polygon bounds
        minx, miny, maxx, maxy = polygon.bounds
        
        # Generate candidate cells
        cells = set()
        lat_step = (maxy - miny) / 10
        lng_step = (maxx - minx) / 10
        
        for lat in np.arange(miny, maxy, lat_step):
            for lng in np.arange(minx, maxx, lng_step):
                cell_id = self.grid.encode_point(lat, lng, precision)
                cell_poly = self.get_cell_polygon(cell_id)
                if cell_poly.intersects(polygon):
                    cells.add(cell_id)
        
        return cells
    
    def spatial_join(self, points: List[Tuple[float, float]], 
                    polygons: List[Polygon], 
                    precision: int) -> Dict[str, List[Tuple[Polygon, List[Tuple[float, float]]]]]:
        """Perform spatial join between points and polygons"""
        # First partition points
        point_partitions = self.partition_points(points, precision)
        
        # Find cells for each polygon
        polygon_cells = defaultdict(list)
        for poly in polygons:
            cells = self.partition_polygon(poly, precision)
            for cell in cells:
                polygon_cells[cell].append(poly)
        
        # Perform join
        results = defaultdict(list)
        for cell_id, cell_points in point_partitions.items():
            cell_polygons = polygon_cells.get(cell_id, [])
            for poly in cell_polygons:
                matching_points = [p for p in cell_points if Point(p[1], p[0]).within(poly)]
                if matching_points:
                    results[cell_id].append((poly, matching_points))
        
        return dict(results)
    
    def get_partition_stats(self) -> Dict[str, Any]:
        """Get statistics about current partitioning"""
        stats = {
            'total_partitions': len(set(self._recovery_state.values())),
            'total_points': len(self._recovery_state),
            'points_per_partition': defaultdict(int)
        }
        
        for cell_id in self._recovery_state.values():
            stats['points_per_partition'][cell_id] += 1
            
        return dict(stats)
    
    def recover_partition(self, point: Tuple[float, float]) -> str:
        """Recover the partition for a given point"""
        point_key = f"{point[0]},{point[1]}"
        return self._recovery_state.get(point_key) 