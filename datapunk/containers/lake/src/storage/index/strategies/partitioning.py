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

class GridPartitionManager:
    def __init__(self, grid_type: str = 'geohash'):
        self.grid = GridFactory.create_grid(grid_type)
        self._recovery_state: Dict[str, Any] = {}
        
    def partition_points(self, points: List[Tuple[float, float]], precision: int) -> Dict[str, List[Tuple[float, float]]]:
        partitions = {}
        for lat, lng in points:
            try:
                cell_id = self.grid.encode_point(lat, lng, precision)
                if cell_id not in partitions:
                    partitions[cell_id] = []
                partitions[cell_id].append((lat, lng))
                # Save state for recovery
                self._recovery_state[f"{lat},{lng}"] = cell_id
            except Exception as e:
                print(f"Error partitioning point ({lat}, {lng}): {str(e)}")
        return partitions
    
    def recover_partition(self, point: Tuple[float, float]) -> str:
        """Recover the partition for a given point from saved state"""
        point_key = f"{point[0]},{point[1]}"
        return self._recovery_state.get(point_key)
    
    def get_partition_stats(self) -> Dict[str, Any]:
        """Get statistics about the current partitioning"""
        stats = {
            'total_partitions': len(set(self._recovery_state.values())),
            'total_points': len(self._recovery_state),
            'points_per_partition': {}
        }
        
        for cell_id in set(self._recovery_state.values()):
            stats['points_per_partition'][cell_id] = list(self._recovery_state.values()).count(cell_id)
            
        return stats

# Visualization support
class GridVisualizer:
    def __init__(self, grid_manager: GridPartitionManager):
        self.grid_manager = grid_manager
        
    def plot_partitions(self, save_path: str = None):
        """Generate a visualization of the current partitioning"""
        try:
            import folium
            import branca.colormap as cm
            
            # Create base map
            center_lat = np.mean([float(k.split(',')[0]) for k in self._recovery_state.keys()])
            center_lng = np.mean([float(k.split(',')[1]) for k in self._recovery_state.keys()])
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Create color map based on number of points in each partition
            stats = self.grid_manager.get_partition_stats()
            max_points = max(stats['points_per_partition'].values())
            colormap = cm.LinearColormap(
                colors=['yellow', 'red'],
                vmin=0,
                vmax=max_points
            )
            
            # Plot partitions
            for cell_id, count in stats['points_per_partition'].items():
                lat, lng = self.grid_manager.grid.decode_cell(cell_id)
                folium.CircleMarker(
                    location=[lat, lng],
                    radius=10,
                    popup=f"Cell: {cell_id}<br>Points: {count}",
                    color=colormap(count),
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