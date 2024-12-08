from typing import List, Tuple
import quadkey
from shapely.geometry import Polygon
from .base_grid import GridSystem

class QuadkeyGrid(GridSystem):
    """Quadkey-based grid system (Microsoft Bing Maps)"""
    
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to a Quadkey"""
        return quadkey.from_geo((lat, lng), precision)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        """Decode a Quadkey to its center point"""
        lat, lng = quadkey.to_geo(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring Quadkeys"""
        return quadkey.neighbors(cell_id)
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of a Quadkey cell"""
        bounds = quadkey.to_tile(cell_id)
        return Polygon([
            (bounds.west, bounds.south),
            (bounds.east, bounds.south),
            (bounds.east, bounds.north),
            (bounds.west, bounds.north)
        ])
    
    def get_children(self, cell_id: str) -> List[str]:
        """Get child cells at next level"""
        return [
            cell_id + '0',
            cell_id + '1',
            cell_id + '2',
            cell_id + '3'
        ]
    
    def get_parent(self, cell_id: str) -> str:
        """Get parent cell at previous level"""
        return cell_id[:-1] if cell_id else ''
    
    def get_level(self, meters: float) -> int:
        """Get appropriate level for given distance in meters"""
        level_map = {
            5000000: 2,   # ~5000km
            1250000: 4,   # ~1250km
            156000: 6,    # ~156km
            39000: 8,     # ~39km
            4900: 10,     # ~5km
            1222: 12,     # ~1.2km
            153: 14,      # ~150m
            19: 16,       # ~20m
        }
        return next((l for m, l in level_map.items() if meters >= m), 16) 