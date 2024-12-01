from typing import Dict, Any, List, Optional, Union, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from enum import Enum
import hashlib
import numpy as np
from shapely.geometry import box, Point, Polygon
from shapely.ops import unary_union
import pytz
import pandas as pd
from abc import ABC, abstractmethod
import h3
from s2sphere import CellId, LatLng
import pygeohash as pgh
from concurrent.futures import ThreadPoolExecutor
import threading
from functools import lru_cache
from collections import defaultdict
import time

from ..sharding import PartitionStrategy, ShardInfo
from ..geometry import BoundingBox, GeoPoint

logger = logging.getLogger(__name__)

class TimeGranularity(Enum):
    """Time partitioning granularity."""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class GeoGridType(Enum):
    """Geospatial grid types."""
    QUADTREE = "quadtree"
    GEOHASH = "geohash"
    H3 = "h3"
    S2 = "s2"

@dataclass
class TimeRange:
    """Time range for partitioning."""
    start: datetime
    end: datetime
    granularity: TimeGranularity
    timezone: str = "UTC"

@dataclass
class GeoGrid:
    """Geospatial grid cell."""
    cell_id: str
    bounds: BoundingBox
    level: int
    grid_type: GeoGridType

class PartitioningStrategy:
    """Base class for partitioning strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
    def get_partition_key(self, data: Dict[str, Any]) -> str:
        """Get partition key for data."""
        raise NotImplementedError
        
    def get_shard_mapping(self, key: str) -> List[str]:
        """Get list of shard IDs for partition key."""
        raise NotImplementedError

class TimePartitionStrategy(PartitioningStrategy):
    """Time-based partitioning strategy."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        time_field: str,
        granularity: TimeGranularity,
        timezone: str = "UTC"
    ):
        super().__init__(config)
        self.time_field = time_field
        self.granularity = granularity
        self.timezone = pytz.timezone(timezone)
        
    def get_partition_key(self, data: Dict[str, Any]) -> str:
        """Get time-based partition key."""
        timestamp = pd.to_datetime(data[self.time_field])
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize(self.timezone)
            
        if self.granularity == TimeGranularity.MINUTE:
            return timestamp.strftime("%Y%m%d%H%M")
        elif self.granularity == TimeGranularity.HOUR:
            return timestamp.strftime("%Y%m%d%H")
        elif self.granularity == TimeGranularity.DAY:
            return timestamp.strftime("%Y%m%d")
        elif self.granularity == TimeGranularity.WEEK:
            return timestamp.strftime("%Y%V")
        elif self.granularity == TimeGranularity.MONTH:
            return timestamp.strftime("%Y%m")
        else:  # YEAR
            return timestamp.strftime("%Y")
            
    def get_time_range(self, key: str) -> TimeRange:
        """Get time range for partition key."""
        if self.granularity == TimeGranularity.MINUTE:
            start = datetime.strptime(key, "%Y%m%d%H%M")
            end = start + timedelta(minutes=1)
        elif self.granularity == TimeGranularity.HOUR:
            start = datetime.strptime(key, "%Y%m%d%H")
            end = start + timedelta(hours=1)
        elif self.granularity == TimeGranularity.DAY:
            start = datetime.strptime(key, "%Y%m%d")
            end = start + timedelta(days=1)
        elif self.granularity == TimeGranularity.WEEK:
            year = int(key[:4])
            week = int(key[4:])
            start = datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w")
            end = start + timedelta(weeks=1)
        elif self.granularity == TimeGranularity.MONTH:
            start = datetime.strptime(key, "%Y%m")
            if start.month == 12:
                end = datetime(start.year + 1, 1, 1)
            else:
                end = datetime(start.year, start.month + 1, 1)
        else:  # YEAR
            start = datetime.strptime(key, "%Y")
            end = datetime(start.year + 1, 1, 1)
            
        return TimeRange(
            start=self.timezone.localize(start),
            end=self.timezone.localize(end),
            granularity=self.granularity,
            timezone=self.timezone.zone
        )

class GeoPartitionStrategy(PartitioningStrategy):
    """Geospatial partitioning strategy."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        lat_field: str,
        lon_field: str,
        grid_type: GeoGridType = GeoGridType.QUADTREE,
        max_level: int = 12
    ):
        super().__init__(config)
        self.lat_field = lat_field
        self.lon_field = lon_field
        self.grid_type = grid_type
        self.max_level = max_level
        self.grids: Dict[str, GeoGrid] = {}
        
    def get_partition_key(self, data: Dict[str, Any]) -> str:
        """Get geospatial partition key."""
        lat = float(data[self.lat_field])
        lon = float(data[self.lon_field])
        point = GeoPoint(lat, lon)
        
        if self.grid_type == GeoGridType.QUADTREE:
            return self._get_quadtree_key(point)
        elif self.grid_type == GeoGridType.GEOHASH:
            return self._get_geohash_key(point)
        elif self.grid_type == GeoGridType.H3:
            return self._get_h3_key(point)
        else:  # S2
            return self._get_s2_key(point)
            
    def _get_quadtree_key(self, point: GeoPoint) -> str:
        """Get quadtree cell key."""
        key = ""
        bounds = BoundingBox(-90, -180, 90, 180)
        
        for level in range(self.max_level):
            mid_lat = (bounds.min_lat + bounds.max_lat) / 2
            mid_lon = (bounds.min_lon + bounds.max_lon) / 2
            
            if point.lat >= mid_lat:
                if point.lon >= mid_lon:
                    key += "0"  # NE
                    bounds = BoundingBox(mid_lat, mid_lon, bounds.max_lat, bounds.max_lon)
                else:
                    key += "1"  # NW
                    bounds = BoundingBox(mid_lat, bounds.min_lon, bounds.max_lat, mid_lon)
            else:
                if point.lon >= mid_lon:
                    key += "2"  # SE
                    bounds = BoundingBox(bounds.min_lat, mid_lon, mid_lat, bounds.max_lon)
                else:
                    key += "3"  # SW
                    bounds = BoundingBox(bounds.min_lat, bounds.min_lon, mid_lat, mid_lon)
                    
        return key
        
    def _get_geohash_key(self, point: GeoPoint) -> str:
        """Get geohash cell key."""
        # TODO: Implement geohash encoding
        pass
        
    def _get_h3_key(self, point: GeoPoint) -> str:
        """Get H3 cell key."""
        # TODO: Implement H3 encoding
        pass
        
    def _get_s2_key(self, point: GeoPoint) -> str:
        """Get S2 cell key."""
        # TODO: Implement S2 encoding
        pass
        
    def get_grid_cell(self, key: str) -> GeoGrid:
        """Get grid cell for partition key."""
        if key in self.grids:
            return self.grids[key]
            
        bounds = self._decode_grid_key(key)
        grid = GeoGrid(
            cell_id=key,
            bounds=bounds,
            level=len(key),
            grid_type=self.grid_type
        )
        
        self.grids[key] = grid
        return grid
        
    def _decode_grid_key(self, key: str) -> BoundingBox:
        """Decode grid key to bounding box."""
        bounds = BoundingBox(-90, -180, 90, 180)
        
        for digit in key:
            mid_lat = (bounds.min_lat + bounds.max_lat) / 2
            mid_lon = (bounds.min_lon + bounds.max_lon) / 2
            
            if digit == "0":  # NE
                bounds = BoundingBox(mid_lat, mid_lon, bounds.max_lat, bounds.max_lon)
            elif digit == "1":  # NW
                bounds = BoundingBox(mid_lat, bounds.min_lon, bounds.max_lat, mid_lon)
            elif digit == "2":  # SE
                bounds = BoundingBox(bounds.min_lat, mid_lon, mid_lat, bounds.max_lon)
            else:  # SW
                bounds = BoundingBox(bounds.min_lat, bounds.min_lon, mid_lat, mid_lon)
                
        return bounds

class CompositePartitionStrategy(PartitioningStrategy):
    """Composite partitioning strategy."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        strategies: List[PartitioningStrategy]
    ):
        super().__init__(config)
        self.strategies = strategies
        
    def get_partition_key(self, data: Dict[str, Any]) -> str:
        """Get composite partition key."""
        return "|".join(
            strategy.get_partition_key(data)
            for strategy in self.strategies
        )
        
    def get_shard_mapping(self, key: str) -> List[str]:
        """Get shard mapping for composite key."""
        keys = key.split("|")
        if len(keys) != len(self.strategies):
            raise ValueError("Invalid composite key")
            
        # Get shard mappings from each strategy
        mappings = [
            set(strategy.get_shard_mapping(k))
            for strategy, k in zip(self.strategies, keys)
        ]
        
        # Return intersection of all mappings
        return list(set.intersection(*mappings))

class AdaptivePartitionStrategy(PartitioningStrategy):
    """Adaptive partitioning strategy."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        base_strategy: PartitioningStrategy,
        metrics_window: timedelta = timedelta(hours=1)
    ):
        super().__init__(config)
        self.base_strategy = base_strategy
        self.metrics_window = metrics_window
        self.access_patterns: Dict[str, List[Tuple[datetime, int]]] = {}
        self.partition_stats: Dict[str, Dict[str, float]] = {}
        
    def record_access(self, key: str, count: int = 1):
        """Record partition access."""
        now = datetime.now()
        self.access_patterns.setdefault(key, []).append((now, count))
        
        # Clean up old access records
        cutoff = now - self.metrics_window
        self.access_patterns[key] = [
            (t, c) for t, c in self.access_patterns[key]
            if t > cutoff
        ]
        
    def update_stats(self, key: str, stats: Dict[str, float]):
        """Update partition statistics."""
        self.partition_stats[key] = stats
        
    def get_partition_key(self, data: Dict[str, Any]) -> str:
        """Get adaptive partition key."""
        base_key = self.base_strategy.get_partition_key(data)
        
        # Check if partition needs splitting
        if self._should_split(base_key):
            return self._split_partition(base_key, data)
            
        # Check if partition needs merging
        if self._should_merge(base_key):
            return self._merge_partition(base_key)
            
        return base_key
        
    def _should_split(self, key: str) -> bool:
        """Check if partition should be split."""
        if key not in self.partition_stats:
            return False
            
        stats = self.partition_stats[key]
        
        # Check size and access patterns
        return (
            stats.get("size_bytes", 0) > self.config["max_partition_size_bytes"] or
            self._get_access_rate(key) > self.config["max_access_rate"]
        )
        
    def _should_merge(self, key: str) -> bool:
        """Check if partition should be merged."""
        if key not in self.partition_stats:
            return False
            
        stats = self.partition_stats[key]
        
        # Check size and access patterns
        return (
            stats.get("size_bytes", 0) < self.config["min_partition_size_bytes"] and
            self._get_access_rate(key) < self.config["min_access_rate"]
        )
        
    def _get_access_rate(self, key: str) -> float:
        """Calculate access rate for partition."""
        if key not in self.access_patterns:
            return 0.0
            
        total_count = sum(
            count for _, count in self.access_patterns[key]
        )
        
        window_seconds = self.metrics_window.total_seconds()
        return total_count / window_seconds
        
    def _split_partition(self, key: str, data: Dict[str, Any]) -> str:
        """Split partition into smaller partitions."""
        # TODO: Implement partition splitting logic
        return key
        
    def _merge_partition(self, key: str) -> str:
        """Merge partition with neighbors."""
        # TODO: Implement partition merging logic
        return key 

class GridSystem(ABC):
    @abstractmethod
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        pass
    
    @abstractmethod
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        pass
    
    @abstractmethod
    def get_neighbors(self, cell_id: str) -> List[str]:
        pass

class GeohashGrid(GridSystem):
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        return pgh.encode(lat, lng, precision)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        lat, lng = pgh.decode(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        return list(pgh.neighbors(cell_id).values())
    
    def get_precision(self, meters: float) -> int:
        # Approximate Geohash precision based on meters
        precision_map = {
            5000000: 1,  # ±2500km
            625000: 2,   # ±630km
            123000: 3,   # ±78km
            19500: 4,    # ±20km
            3900: 5,     # ±2.4km
            610: 6,      # ±610m
            76: 7,       # ±76m
            19: 8,       # ±19m
        }
        return next((p for m, p in precision_map.items() if meters >= m), 8)

class H3Grid(GridSystem):
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        h3_cell = h3.geo_to_h3(lat, lng, precision)
        return str(h3_cell)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        lat, lng = h3.h3_to_geo(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        return [str(n) for n in h3.k_ring(cell_id, 1)]
    
    def get_resolution(self, meters: float) -> int:
        # Approximate H3 resolution based on meters
        resolution_map = {
            1000000: 0,  # ~1107.71km
            100000: 3,   # ~82.31km
            10000: 6,    # ~6.10km
            1000: 9,     # ~0.45km
            100: 12,     # ~0.03km
        }
        return next((r for m, r in resolution_map.items() if meters >= m), 12)

class S2Grid(GridSystem):
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        ll = LatLng.from_degrees(lat, lng)
        cell = CellId.from_lat_lng(ll).parent(precision)
        return str(cell.id())
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        cell = CellId(int(cell_id))
        ll = cell.to_lat_lng()
        return ll.lat().degrees, ll.lng().degrees
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        cell = CellId(int(cell_id))
        neighbors = []
        for i in range(4):  # Get all 4 adjacent cells
            neighbor = cell.get_edge_neighbors()[i]
            neighbors.append(str(neighbor.id()))
        return neighbors
    
    def get_level(self, meters: float) -> int:
        # Approximate S2 level based on meters
        level_map = {
            1000000: 8,   # ~700km
            100000: 12,   # ~50km
            10000: 16,    # ~3km
            1000: 20,     # ~200m
            100: 24,      # ~10m
        }
        return next((l for m, l in level_map.items() if meters >= m), 24)

class GridFactory:
    @staticmethod
    def create_grid(grid_type: str) -> GridSystem:
        grid_map = {
            'geohash': GeohashGrid(),
            'h3': H3Grid(),
            's2': S2Grid()
        }
        if grid_type not in grid_map:
            raise ValueError(f"Unsupported grid system: {grid_type}")
        return grid_map[grid_type]

class PartitionHistory:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        
    def add_snapshot(self, partitions: Dict[str, List[Tuple[float, float]]], timestamp: float = None):
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

class SpatialCache:
    def __init__(self, max_size: int = 1000):
        self.cache = {}
        self.max_size = max_size
        self.lock = threading.Lock()
        
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            return self.cache.get(key)
            
    def set(self, key: str, value: Any):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)
        elif isinstance(self.grid, S2Grid):
            # Convert S2 cell to polygon
            cell = CellId(int(cell_id))
            vertices = []
            for i in range(4):
                vertex = cell.vertex(i)
                ll = vertex.to_lat_lng()
                vertices.append((ll.lng().degrees, ll.lat().degrees))
            polygon = Polygon(vertices)
            
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
        """Perform spatial join between points and polygons using grid cells"""
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

class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None, 
                       show_history: bool = False,
                       highlight_cells: Set[str] = None):
        """Enhanced visualization with history and highlighting"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) 
                                for k in self.grid_manager._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) 
                                for k in self.grid_manager._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Create color map
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            colormap = cm.LinearColormap(
                colors=['yellow', 'orange', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            # Plot current partitions
            for cell_id, count in stats['points_per_partition'].items():
                color = 'blue' if highlight_cells and cell_id in highlight_cells else colormap(count)
                
                # Get cell polygon
                try:
                    cell_poly = self.grid_manager.get_cell_polygon(cell_id)
                    folium.GeoJson(
                        cell_poly.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=f"Cell: {cell_id}<br>Points: {count}"
                    ).add_to(m)
                except Exception as e:
                    print(f"Error plotting cell {cell_id}: {str(e)}")
            
            # Add historical growth if requested
            if show_history and self.grid_manager.history.history:
                for cell_id in stats['points_per_partition'].keys():
                    growth = self.grid_manager.history.get_partition_growth(cell_id)
                    if growth:
                        times, counts = zip(*growth)
                        folium.Circle(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.mean(counts),
                            popup=f"Growth: {counts}",
                            color='green',
                            fill=True
                        ).add_to(m)
            
            # Add colormap to map
            colormap.add_to(m)
            
            if save_path:
                m.save(save_path)
            return m
            
        except ImportError:
            print("Visualization requires folium and branca packages")
            return None

class QuadkeyGrid(GridSystem):
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        return quadkey.from_geo((lat, lng), precision)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        lat, lng = quadkey.to_geo(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        return quadkey.neighbors(cell_id)

class RTreeGrid(GridSystem):
    def __init__(self):
        self.idx = index.Index()
        self.cell_counter = 0
        self.cell_bounds = {}
        
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        cell_id = str(self.cell_counter)
        # Create cell bounds based on precision
        cell_size = 1.0 / (2 ** precision)
        bounds = (lng - cell_size, lat - cell_size, 
                 lng + cell_size, lat + cell_size)
        self.idx.insert(self.cell_counter, bounds)
        self.cell_bounds[cell_id] = bounds
        self.cell_counter += 1
        return cell_id
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        bounds = self.cell_bounds[cell_id]
        return ((bounds[1] + bounds[3]) / 2, 
                (bounds[0] + bounds[2]) / 2)
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        bounds = self.cell_bounds[cell_id]
        return [str(i) for i in self.idx.intersection(bounds)]

class DensityAnalyzer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def calculate_density_metrics(self, points: List[Tuple[float, float]], 
                                precision: int) -> Dict[str, float]:
        """Calculate density metrics for each partition"""
        partitions = self.grid_manager.partition_points(points, precision)
        metrics = {}
        
        for cell_id, cell_points in partitions.items():
            cell_poly = self.grid_manager.get_cell_polygon(cell_id)
            density = len(cell_points) / cell_poly.area
            metrics[cell_id] = density
            
        return metrics
    
    def find_hotspots(self, points: List[Tuple[float, float]], 
                     precision: int, 
                     threshold: float = 0.75) -> Set[str]:
        """Identify high-density areas"""
        densities = self.calculate_density_metrics(points, precision)
        if not densities:
            return set()
            
        density_threshold = np.percentile(list(densities.values()), 
                                        threshold * 100)
        return {cell_id for cell_id, density in densities.items() 
                if density >= density_threshold}
    
    def cluster_analysis(self, points: List[Tuple[float, float]], 
                        eps: float = 0.1, 
                        min_samples: int = 5) -> Dict[str, List[Tuple[float, float]]]:
        """Perform DBSCAN clustering on points"""
        if not points:
            return {}
            
        # Normalize points for clustering
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(points_normalized)
        
        # Group points by cluster
        cluster_points = defaultdict(list)
        for point, cluster_id in zip(points, clusters):
            cluster_points[str(cluster_id)].append(point)
            
        return dict(cluster_points)

class LoadBalancer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        self.load_history = defaultdict(list)
        
    def calculate_load_metrics(self, partitions: Dict[str, List[Tuple[float, float]]]) -> Dict[str, float]:
        """Calculate load metrics for each partition"""
        metrics = {}
        total_points = sum(len(points) for points in partitions.values())
        
        for cell_id, points in partitions.items():
            # Combine point count with historical load
            current_load = len(points) / max(total_points, 1)
            historical_load = np.mean(self.load_history[cell_id]) if self.load_history[cell_id] else 0
            metrics[cell_id] = 0.7 * current_load + 0.3 * historical_load
            
            # Update history
            self.load_history[cell_id].append(current_load)
            if len(self.load_history[cell_id]) > 10:
                self.load_history[cell_id].pop(0)
                
        return metrics
    
    def suggest_rebalancing(self, partitions: Dict[str, List[Tuple[float, float]]],
                           threshold: float = 0.2) -> List[Tuple[str, str, int]]:
        """Suggest partition splits or merges"""
        load_metrics = self.calculate_load_metrics(partitions)
        suggestions = []
        
        # Find overloaded and underloaded partitions
        avg_load = np.mean(list(load_metrics.values()))
        overloaded = {cell_id for cell_id, load in load_metrics.items() 
                     if load > avg_load * (1 + threshold)}
        underloaded = {cell_id for cell_id, load in load_metrics.items() 
                      if load < avg_load * (1 - threshold)}
        
        # Suggest splits for overloaded partitions
        for cell_id in overloaded:
            suggestions.append((cell_id, None, 1))  # 1 indicates split
            
        # Suggest merges for underloaded partitions
        underloaded_list = list(underloaded)
        for i in range(0, len(underloaded_list) - 1, 2):
            suggestions.append((underloaded_list[i], 
                             underloaded_list[i + 1], 
                             2))  # 2 indicates merge
            
        return suggestions

class SpatialIndexManager:
    def __init__(self):
        self.rtree_idx = index.Index()
        self.kdtree = None
        self.points = []
        
    def build_indexes(self, points: List[Tuple[float, float]]):
        """Build spatial indexes for points"""
        self.points = points
        
        # Build R-tree index
        for i, (lat, lng) in enumerate(points):
            self.rtree_idx.insert(i, (lng, lat, lng, lat))
            
        # Build KD-tree index
        self.kdtree = cKDTree(points)
        
    def nearest_neighbors(self, point: Tuple[float, float], k: int = 5) -> List[Tuple[float, float]]:
        """Find k nearest neighbors using KD-tree"""
        if self.kdtree is None:
            return []
            
        distances, indices = self.kdtree.query([point], k=k)
        return [self.points[i] for i in indices[0]]
        
    def range_query(self, bounds: Tuple[float, float, float, float]) -> List[Tuple[float, float]]:
        """Find all points within bounds using R-tree"""
        indices = list(self.rtree_idx.intersection(bounds))
        return [self.points[i] for i in indices]

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        self.density_analyzer = DensityAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.spatial_index = SpatialIndexManager()
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)
        elif isinstance(self.grid, S2Grid):
            # Convert S2 cell to polygon
            cell = CellId(int(cell_id))
            vertices = []
            for i in range(4):
                vertex = cell.vertex(i)
                ll = vertex.to_lat_lng()
                vertices.append((ll.lng().degrees, ll.lat().degrees))
            polygon = Polygon(vertices)
            
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
        """Perform spatial join between points and polygons using grid cells"""
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

class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None, 
                       show_history: bool = False,
                       highlight_cells: Set[str] = None,
                       show_density: bool = False,
                       show_clusters: bool = False):
        """Enhanced visualization with multiple layers"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) 
                                for k in self.grid_manager._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) 
                                for k in self.grid_manager._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Create color maps
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            point_colormap = cm.LinearColormap(
                colors=['yellow', 'orange', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            if show_density:
                density_metrics = self.grid_manager.density_analyzer.calculate_density_metrics(
                    [(float(k.split(',')[0]), float(k.split(',')[1])) 
                     for k in self.grid_manager._recovery_state.keys()],
                    5  # Use fixed precision for visualization
                )
                max_density = max(density_metrics.values())
                density_colormap = cm.LinearColormap(
                    colors=['blue', 'purple', 'red'],
                    vmin=0,
                    vmax=max_density
                )
            
            # Create feature groups for layers
            grid_layer = folium.FeatureGroup(name='Grid Cells')
            density_layer = folium.FeatureGroup(name='Density Heatmap')
            cluster_layer = folium.FeatureGroup(name='Clusters')
            history_layer = folium.FeatureGroup(name='Historical Growth')
            
            # Plot current partitions
            for cell_id, count in stats['points_per_partition'].items():
                color = 'blue' if highlight_cells and cell_id in highlight_cells else point_colormap(count)
                
                try:
                    cell_poly = self.grid_manager.get_cell_polygon(cell_id)
                    folium.GeoJson(
                        cell_poly.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=f"Cell: {cell_id}<br>Points: {count}"
                    ).add_to(grid_layer)
                    
                    if show_density:
                        density = density_metrics.get(cell_id, 0)
                        folium.CircleMarker(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.sqrt(density) * 10,
                            color=density_colormap(density),
                            popup=f"Density: {density:.2f}",
                            fill=True
                        ).add_to(density_layer)
                        
                except Exception as e:
                    print(f"Error plotting cell {cell_id}: {str(e)}")
            
            # Add historical growth if requested
            if show_history and self.grid_manager.history.history:
                for cell_id in stats['points_per_partition'].keys():
                    growth = self.grid_manager.history.get_partition_growth(cell_id)
                    if growth:
                        times, counts = zip(*growth)
                        folium.Circle(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.mean(counts) * 100,
                            popup=f"Growth: {counts}",
                            color='green',
                            fill=True
                        ).add_to(history_layer)
            
            # Add clustering if requested
            if show_clusters:
                points = [(float(k.split(',')[0]), float(k.split(',')[1])) 
                         for k in self.grid_manager._recovery_state.keys()]
                clusters = self.grid_manager.density_analyzer.cluster_analysis(points)
                
                for cluster_id, cluster_points in clusters.items():
                    if cluster_points:
                        cluster_color = f'#{hash(cluster_id) % 0xFFFFFF:06x}'
                        for point in cluster_points:
                            folium.CircleMarker(
                                location=point,
                                radius=5,
                                color=cluster_color,
                                popup=f"Cluster: {cluster_id}",
                                fill=True
                            ).add_to(cluster_layer)
            
            # Add all layers to map
            grid_layer.add_to(m)
            if show_density:
                density_layer.add_to(m)
                density_colormap.add_to(m)
            if show_clusters:
                cluster_layer.add_to(m)
            if show_history:
                history_layer.add_to(m)
            point_colormap.add_to(m)
            
            # Add fullscreen option
            plugins.Fullscreen().add_to(m)
            
            # Add search box
            m.add_child(plugins.Search(
                layer=grid_layer,
                search_label='cell_id',
                position='topright'
            ))
            
            if save_path:
                m.save(save_path)
            return m
            
        except ImportError:
            print("Visualization requires folium and branca packages")
            return None

class TimePartitionStrategy:
    def __init__(self, time_field: str, interval: timedelta = timedelta(days=1)):
        self.time_field = time_field
        self.interval = interval
        self.partitions = defaultdict(list)
        
    def partition_data(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Partition data based on time intervals"""
        for record in data:
            timestamp = record[self.time_field]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Calculate partition key
            partition_key = timestamp.replace(
                hour=0, minute=0, second=0, microsecond=0
            ).isoformat()
            
            self.partitions[partition_key].append(record)
            
        return dict(self.partitions)
    
    def get_partition_for_time(self, timestamp: Union[str, datetime]) -> str:
        """Get partition key for a given timestamp"""
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
        return timestamp.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
    
    def get_partitions_in_range(self, start_time: Union[str, datetime],
                               end_time: Union[str, datetime]) -> List[str]:
        """Get list of partition keys within a time range"""
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
        partitions = []
        current_time = start_time
        
        while current_time <= end_time:
            partitions.append(self.get_partition_for_time(current_time))
            current_time += self.interval
            
        return partitions

class AdvancedClusterAnalyzer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def hdbscan_clustering(self, points: List[Tuple[float, float]], 
                          min_cluster_size: int = 5) -> Dict[str, List[Tuple[float, float]]]:
        """Perform HDBSCAN clustering"""
        if not points:
            return {}
            
        # Normalize points
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Perform clustering
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size)
        cluster_labels = clusterer.fit_predict(points_normalized)
        
        # Group points by cluster
        clusters = defaultdict(list)
        for point, label in zip(points, cluster_labels):
            clusters[str(label)].append(point)
            
        return dict(clusters)
    
    def optics_clustering(self, points: List[Tuple[float, float]], 
                         min_samples: int = 5) -> Dict[str, List[Tuple[float, float]]]:
        """Perform OPTICS clustering"""
        if not points:
            return {}
            
        # Normalize points
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Perform clustering
        clusterer = OPTICS(min_samples=min_samples)
        cluster_labels = clusterer.fit_predict(points_normalized)
        
        # Group points by cluster
        clusters = defaultdict(list)
        for point, label in zip(points, cluster_labels):
            clusters[str(label)].append(point)
            
        return dict(clusters)
    
    def analyze_cluster_stability(self, points: List[Tuple[float, float]], 
                                time_window: timedelta = timedelta(hours=1)) -> Dict[str, float]:
        """Analyze cluster stability over time"""
        now = datetime.now(pytz.UTC)
        window_start = now - time_window
        
        # Get historical clusters
        historical_clusters = []
        current_time = window_start
        
        while current_time <= now:
            clusters = self.hdbscan_clustering(points)
            historical_clusters.append((current_time, clusters))
            current_time += timedelta(minutes=10)
        
        # Calculate stability metrics
        stability = {}
        for cluster_id in set().union(*(c[1].keys() for c in historical_clusters)):
            appearances = sum(1 for _, clusters in historical_clusters if cluster_id in clusters)
            stability[cluster_id] = appearances / len(historical_clusters)
            
        return stability

class DistributedPartitionManager:
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.redis_client = redis.Redis(host=redis_host, port=redis_port)
        self.dask_client = Client(LocalCluster())
        
    def partition_distributed(self, data: List[Dict[str, Any]], 
                            partition_key: str) -> Dict[str, str]:
        """Partition data across distributed nodes"""
        # Convert to dask dataframe
        df = pd.DataFrame(data)
        ddf = dd.from_pandas(df, npartitions=10)
        
        # Partition based on key
        partitions = ddf.groupby(partition_key).apply(
            lambda x: x.to_json(), meta=('json', 'str')
        ).compute()
        
        # Store partitions in Redis
        partition_locations = {}
        for key, value in partitions.items():
            partition_id = f"partition:{partition_key}:{key}"
            self.redis_client.set(partition_id, value)
            partition_locations[str(key)] = partition_id
            
        return partition_locations
    
    def get_partition(self, partition_id: str) -> List[Dict[str, Any]]:
        """Retrieve partition data"""
        data = self.redis_client.get(partition_id)
        if data:
            return json.loads(data)
        return []
    
    def process_partition(self, partition_id: str, 
                         func: Callable[[List[Dict[str, Any]]], Any]) -> Any:
        """Process partition data with given function"""
        data = self.get_partition(partition_id)
        return self.dask_client.submit(func, data).result()

class InteractiveVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def create_interactive_dashboard(self, save_path: str = None):
        """Create an interactive dashboard with Plotly"""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Partition Distribution',
                'Density Heatmap',
                'Cluster Analysis',
                'Time Series'
            )
        )
        
        # Get partition stats
        stats = self.grid_manager.get_partition_stats()
        
        # Partition distribution
        points_per_partition = list(stats['points_per_partition'].values())
        fig.add_trace(
            go.Histogram(x=points_per_partition, name='Points per Partition'),
            row=1, col=1
        )
        
        # Density heatmap
        points = [(float(k.split(',')[0]), float(k.split(',')[1])) 
                 for k in self.grid_manager._recovery_state.keys()]
        lat, lon = zip(*points)
        fig.add_trace(
            go.Densitymapbox(
                lat=lat, lon=lon,
                radius=10,
                name='Density'
            ),
            row=1, col=2
        )
        
        # Cluster analysis
        clusters = self.grid_manager.density_analyzer.cluster_analysis(points)
        for cluster_id, cluster_points in clusters.items():
            if cluster_points:
                cluster_lat, cluster_lon = zip(*cluster_points)
                fig.add_trace(
                    go.Scattermapbox(
                        lat=cluster_lat,
                        lon=cluster_lon,
                        mode='markers',
                        name=f'Cluster {cluster_id}'
                    ),
                    row=2, col=1
                )
        
        # Time series
        if self.grid_manager.history.history:
            times = []
            counts = []
            for snapshot in self.grid_manager.history.history:
                times.append(snapshot['timestamp'])
                counts.append(snapshot['stats']['total_points'])
            
            fig.add_trace(
                go.Scatter(x=times, y=counts, name='Total Points'),
                row=2, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            mapbox_style="carto-positron",
            mapbox=dict(
                center=dict(lat=np.mean(lat), lon=np.mean(lon)),
                zoom=10
            )
        )
        
        if save_path:
            fig.write_html(save_path)
        
        return fig
    
    def create_time_analysis_dashboard(self, time_partitions: Dict[str, List[Dict[str, Any]]],
                                     save_path: str = None):
        """Create time-based analysis dashboard"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Points Over Time',
                'Partition Growth',
                'Hourly Distribution',
                'Cumulative Growth'
            )
        )
        
        # Points over time
        times = sorted(time_partitions.keys())
        counts = [len(time_partitions[t]) for t in times]
        
        fig.add_trace(
            go.Scatter(x=times, y=counts, name='Points'),
            row=1, col=1
        )
        
        # Partition growth
        growth_rate = [
            (counts[i] - counts[i-1]) / counts[i-1] if i > 0 and counts[i-1] > 0 else 0
            for i in range(len(counts))
        ]
        
        fig.add_trace(
            go.Bar(x=times, y=growth_rate, name='Growth Rate'),
            row=1, col=2
        )
        
        # Hourly distribution
        hours = [datetime.fromisoformat(t).hour for t in times]
        fig.add_trace(
            go.Histogram(x=hours, name='Hourly Distribution'),
            row=2, col=1
        )
        
        # Cumulative growth
        cumulative = np.cumsum(counts)
        fig.add_trace(
            go.Scatter(x=times, y=cumulative, name='Cumulative Points'),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True
        )
        
        if save_path:
            fig.write_html(save_path)
        
        return fig

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        self.density_analyzer = DensityAnalyzer(self)
        self.advanced_analyzer = AdvancedClusterAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.spatial_index = SpatialIndexManager()
        self.time_strategy = TimePartitionStrategy('timestamp')
        self.distributed_manager = DistributedPartitionManager()
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)
        elif isinstance(self.grid, S2Grid):
            # Convert S2 cell to polygon
            cell = CellId(int(cell_id))
            vertices = []
            for i in range(4):
                vertex = cell.vertex(i)
                ll = vertex.to_lat_lng()
                vertices.append((ll.lng().degrees, ll.lat().degrees))
            polygon = Polygon(vertices)
            
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
        """Perform spatial join between points and polygons using grid cells"""
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

class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None, 
                       show_history: bool = False,
                       highlight_cells: Set[str] = None,
                       show_density: bool = False,
                       show_clusters: bool = False):
        """Enhanced visualization with multiple layers"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) 
                                for k in self.grid_manager._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) 
                                for k in self.grid_manager._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Create color maps
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            point_colormap = cm.LinearColormap(
                colors=['yellow', 'orange', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            if show_density:
                density_metrics = self.grid_manager.density_analyzer.calculate_density_metrics(
                    [(float(k.split(',')[0]), float(k.split(',')[1])) 
                     for k in self.grid_manager._recovery_state.keys()],
                    5  # Use fixed precision for visualization
                )
                max_density = max(density_metrics.values())
                density_colormap = cm.LinearColormap(
                    colors=['blue', 'purple', 'red'],
                    vmin=0,
                    vmax=max_density
                )
            
            # Create feature groups for layers
            grid_layer = folium.FeatureGroup(name='Grid Cells')
            density_layer = folium.FeatureGroup(name='Density Heatmap')
            cluster_layer = folium.FeatureGroup(name='Clusters')
            history_layer = folium.FeatureGroup(name='Historical Growth')
            
            # Plot current partitions
            for cell_id, count in stats['points_per_partition'].items():
                color = 'blue' if highlight_cells and cell_id in highlight_cells else point_colormap(count)
                
                try:
                    cell_poly = self.grid_manager.get_cell_polygon(cell_id)
                    folium.GeoJson(
                        cell_poly.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=f"Cell: {cell_id}<br>Points: {count}"
                    ).add_to(grid_layer)
                    
                    if show_density:
                        density = density_metrics.get(cell_id, 0)
                        folium.CircleMarker(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.sqrt(density) * 10,
                            color=density_colormap(density),
                            popup=f"Density: {density:.2f}",
                            fill=True
                        ).add_to(density_layer)
                        
                except Exception as e:
                    print(f"Error plotting cell {cell_id}: {str(e)}")
            
            # Add historical growth if requested
            if show_history and self.grid_manager.history.history:
                for cell_id in stats['points_per_partition'].keys():
                    growth = self.grid_manager.history.get_partition_growth(cell_id)
                    if growth:
                        times, counts = zip(*growth)
                        folium.Circle(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.mean(counts) * 100,
                            popup=f"Growth: {counts}",
                            color='green',
                            fill=True
                        ).add_to(history_layer)
            
            # Add clustering if requested
            if show_clusters:
                points = [(float(k.split(',')[0]), float(k.split(',')[1])) 
                         for k in self.grid_manager._recovery_state.keys()]
                clusters = self.grid_manager.density_analyzer.cluster_analysis(points)
                
                for cluster_id, cluster_points in clusters.items():
                    if cluster_points:
                        cluster_color = f'#{hash(cluster_id) % 0xFFFFFF:06x}'
                        for point in cluster_points:
                            folium.CircleMarker(
                                location=point,
                                radius=5,
                                color=cluster_color,
                                popup=f"Cluster: {cluster_id}",
                                fill=True
                            ).add_to(cluster_layer)
            
            # Add all layers to map
            grid_layer.add_to(m)
            if show_density:
                density_layer.add_to(m)
                density_colormap.add_to(m)
            if show_clusters:
                cluster_layer.add_to(m)
            if show_history:
                history_layer.add_to(m)
            point_colormap.add_to(m)
            
            # Add fullscreen option
            plugins.Fullscreen().add_to(m)
            
            # Add search box
            m.add_child(plugins.Search(
                layer=grid_layer,
                search_label='cell_id',
                position='topright'
            ))
            
            if save_path:
                m.save(save_path)
            return m
            
        except ImportError:
            print("Visualization requires folium and branca packages")
            return None

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        self.density_analyzer = DensityAnalyzer(self)
        self.advanced_analyzer = AdvancedClusterAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.spatial_index = SpatialIndexManager()
        self.time_strategy = TimePartitionStrategy('timestamp')
        self.distributed_manager = DistributedPartitionManager()
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)
        elif isinstance(self.grid, S2Grid):
            # Convert S2 cell to polygon
            cell = CellId(int(cell_id))
            vertices = []
            for i in range(4):
                vertex = cell.vertex(i)
                ll = vertex.to_lat_lng()
                vertices.append((ll.lng().degrees, ll.lat().degrees))
            polygon = Polygon(vertices)
            
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
        """Perform spatial join between points and polygons using grid cells"""
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

class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None, 
                       show_history: bool = False,
                       highlight_cells: Set[str] = None,
                       show_density: bool = False,
                       show_clusters: bool = False):
        """Enhanced visualization with multiple layers"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) 
                                for k in self.grid_manager._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) 
                                for k in self.grid_manager._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Create color maps
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            point_colormap = cm.LinearColormap(
                colors=['yellow', 'orange', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            if show_density:
                density_metrics = self.grid_manager.density_analyzer.calculate_density_metrics(
                    [(float(k.split(',')[0]), float(k.split(',')[1])) 
                     for k in self.grid_manager._recovery_state.keys()],
                    5  # Use fixed precision for visualization
                )
                max_density = max(density_metrics.values())
                density_colormap = cm.LinearColormap(
                    colors=['blue', 'purple', 'red'],
                    vmin=0,
                    vmax=max_density
                )
            
            # Create feature groups for layers
            grid_layer = folium.FeatureGroup(name='Grid Cells')
            density_layer = folium.FeatureGroup(name='Density Heatmap')
            cluster_layer = folium.FeatureGroup(name='Clusters')
            history_layer = folium.FeatureGroup(name='Historical Growth')
            
            # Plot current partitions
            for cell_id, count in stats['points_per_partition'].items():
                color = 'blue' if highlight_cells and cell_id in highlight_cells else point_colormap(count)
                
                try:
                    cell_poly = self.grid_manager.get_cell_polygon(cell_id)
                    folium.GeoJson(
                        cell_poly.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=f"Cell: {cell_id}<br>Points: {count}"
                    ).add_to(grid_layer)
                    
                    if show_density:
                        density = density_metrics.get(cell_id, 0)
                        folium.CircleMarker(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.sqrt(density) * 10,
                            color=density_colormap(density),
                            popup=f"Density: {density:.2f}",
                            fill=True
                        ).add_to(density_layer)
                        
                except Exception as e:
                    print(f"Error plotting cell {cell_id}: {str(e)}")
            
            # Add historical growth if requested
            if show_history and self.grid_manager.history.history:
                for cell_id in stats['points_per_partition'].keys():
                    growth = self.grid_manager.history.get_partition_growth(cell_id)
                    if growth:
                        times, counts = zip(*growth)
                        folium.Circle(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.mean(counts) * 100,
                            popup=f"Growth: {counts}",
                            color='green',
                            fill=True
                        ).add_to(history_layer)
            
            # Add clustering if requested
            if show_clusters:
                points = [(float(k.split(',')[0]), float(k.split(',')[1])) 
                         for k in self.grid_manager._recovery_state.keys()]
                clusters = self.grid_manager.density_analyzer.cluster_analysis(points)
                
                for cluster_id, cluster_points in clusters.items():
                    if cluster_points:
                        cluster_color = f'#{hash(cluster_id) % 0xFFFFFF:06x}'
                        for point in cluster_points:
                            folium.CircleMarker(
                                location=point,
                                radius=5,
                                color=cluster_color,
                                popup=f"Cluster: {cluster_id}",
                                fill=True
                            ).add_to(cluster_layer)
            
            # Add all layers to map
            grid_layer.add_to(m)
            if show_density:
                density_layer.add_to(m)
                density_colormap.add_to(m)
            if show_clusters:
                cluster_layer.add_to(m)
            if show_history:
                history_layer.add_to(m)
            point_colormap.add_to(m)
            
            # Add fullscreen option
            plugins.Fullscreen().add_to(m)
            
            # Add search box
            m.add_child(plugins.Search(
                layer=grid_layer,
                search_label='cell_id',
                position='topright'
            ))
            
            if save_path:
                m.save(save_path)
            return m
            
        except ImportError:
            print("Visualization requires folium and branca packages")
            return None

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        self.density_analyzer = DensityAnalyzer(self)
        self.advanced_analyzer = AdvancedClusterAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.spatial_index = SpatialIndexManager()
        self.time_strategy = TimePartitionStrategy('timestamp')
        self.distributed_manager = DistributedPartitionManager()
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)
        elif isinstance(self.grid, S2Grid):
            # Convert S2 cell to polygon
            cell = CellId(int(cell_id))
            vertices = []
            for i in range(4):
                vertex = cell.vertex(i)
                ll = vertex.to_lat_lng()
                vertices.append((ll.lng().degrees, ll.lat().degrees))
            polygon = Polygon(vertices)
            
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
        """Perform spatial join between points and polygons using grid cells"""
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

class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None, 
                       show_history: bool = False,
                       highlight_cells: Set[str] = None,
                       show_density: bool = False,
                       show_clusters: bool = False):
        """Enhanced visualization with multiple layers"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) 
                                for k in self.grid_manager._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) 
                                for k in self.grid_manager._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Add layer control
            folium.LayerControl().add_to(m)
            
            # Create color maps
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            point_colormap = cm.LinearColormap(
                colors=['yellow', 'orange', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            if show_density:
                density_metrics = self.grid_manager.density_analyzer.calculate_density_metrics(
                    [(float(k.split(',')[0]), float(k.split(',')[1])) 
                     for k in self.grid_manager._recovery_state.keys()],
                    5  # Use fixed precision for visualization
                )
                max_density = max(density_metrics.values())
                density_colormap = cm.LinearColormap(
                    colors=['blue', 'purple', 'red'],
                    vmin=0,
                    vmax=max_density
                )
            
            # Create feature groups for layers
            grid_layer = folium.FeatureGroup(name='Grid Cells')
            density_layer = folium.FeatureGroup(name='Density Heatmap')
            cluster_layer = folium.FeatureGroup(name='Clusters')
            history_layer = folium.FeatureGroup(name='Historical Growth')
            
            # Plot current partitions
            for cell_id, count in stats['points_per_partition'].items():
                color = 'blue' if highlight_cells and cell_id in highlight_cells else point_colormap(count)
                
                try:
                    cell_poly = self.grid_manager.get_cell_polygon(cell_id)
                    folium.GeoJson(
                        cell_poly.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': 'black',
                            'weight': 1,
                            'fillOpacity': 0.6
                        },
                        popup=f"Cell: {cell_id}<br>Points: {count}"
                    ).add_to(grid_layer)
                    
                    if show_density:
                        density = density_metrics.get(cell_id, 0)
                        folium.CircleMarker(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.sqrt(density) * 10,
                            color=density_colormap(density),
                            popup=f"Density: {density:.2f}",
                            fill=True
                        ).add_to(density_layer)
                        
                except Exception as e:
                    print(f"Error plotting cell {cell_id}: {str(e)}")
            
            # Add historical growth if requested
            if show_history and self.grid_manager.history.history:
                for cell_id in stats['points_per_partition'].keys():
                    growth = self.grid_manager.history.get_partition_growth(cell_id)
                    if growth:
                        times, counts = zip(*growth)
                        folium.Circle(
                            location=self.grid_manager.grid.decode_cell(cell_id),
                            radius=np.mean(counts) * 100,
                            popup=f"Growth: {counts}",
                            color='green',
                            fill=True
                        ).add_to(history_layer)
            
            # Add clustering if requested
            if show_clusters:
                points = [(float(k.split(',')[0]), float(k.split(',')[1])) 
                         for k in self.grid_manager._recovery_state.keys()]
                clusters = self.grid_manager.density_analyzer.cluster_analysis(points)
                
                for cluster_id, cluster_points in clusters.items():
                    if cluster_points:
                        cluster_color = f'#{hash(cluster_id) % 0xFFFFFF:06x}'
                        for point in cluster_points:
                            folium.CircleMarker(
                                location=point,
                                radius=5,
                                color=cluster_color,
                                popup=f"Cluster: {cluster_id}",
                                fill=True
                            ).add_to(cluster_layer)
            
            # Add all layers to map
            grid_layer.add_to(m)
            if show_density:
                density_layer.add_to(m)
                density_colormap.add_to(m)
            if show_clusters:
                cluster_layer.add_to(m)
            if show_history:
                history_layer.add_to(m)
            point_colormap.add_to(m)
            
            # Add fullscreen option
            plugins.Fullscreen().add_to(m)
            
            # Add search box
            m.add_child(plugins.Search(
                layer=grid_layer,
                search_label='cell_id',
                position='topright'
            ))
            
            if save_path:
                m.save(save_path)
            return m
            
        except ImportError:
            print("Visualization requires folium and branca packages")
            return None

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash', 
                 rebalance_threshold: float = 0.3,
                 max_points_per_partition: int = 1000):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        self.history = PartitionHistory()
        self.cache = SpatialCache()
        self.rebalance_threshold = rebalance_threshold
        self.max_points_per_partition = max_points_per_partition
        self.density_analyzer = DensityAnalyzer(self)
        self.advanced_analyzer = AdvancedClusterAnalyzer(self)
        self.load_balancer = LoadBalancer(self)
        self.spatial_index = SpatialIndexManager()
        self.time_strategy = TimePartitionStrategy('timestamp')
        self.distributed_manager = DistributedPartitionManager()
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int,
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
    
    @lru_cache(maxsize=1000)
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get the polygon representation of a grid cell"""
        cached = self.cache.get(cell_id)
        if cached is not None:
            return cached
            
        if isinstance(self.grid, GeohashGrid):
            # Convert geohash bounds to polygon
            lat, lng = self.grid.decode_cell(cell_id)
            precision = len(cell_id)
            lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
            polygon = Polygon([
                (lng - lng_err, lat - lat_err),
                (lng + lng_err, lat - lat_err),
                (lng + lng_err, lat + lat_err),
                (lng - lng_err, lat + lat_err)
            ])
        elif isinstance(self.grid, H3Grid):
            # Convert H3 cell to polygon
            boundary = h3.h3_to_geo_boundary(cell_id)
            polygon = Polygon(boundary)