from typing import List, Tuple
import h3
from shapely.geometry import Polygon
from .base import GridSystem

class H3Grid(GridSystem):
    """H3-based hexagonal grid system"""
    
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to an H3 cell ID"""
        h3_cell = h3.geo_to_h3(lat, lng, precision)
        return str(h3_cell)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        """Decode an H3 cell ID to its center point"""
        lat, lng = h3.h3_to_geo(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring H3 cells"""
        return [str(n) for n in h3.k_ring(cell_id, 1)]
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of an H3 cell"""
        boundary = h3.h3_to_geo_boundary(cell_id)
        return Polygon(boundary)
    
    def get_resolution(self, meters: float) -> int:
        """Get appropriate resolution for given distance in meters"""
        resolution_map = {
            1000000: 0,  # ~1107.71km
            100000: 3,   # ~82.31km
            10000: 6,    # ~6.10km
            1000: 9,     # ~0.45km
            100: 12,     # ~0.03km
        }
        return next((r for m, r in resolution_map.items() if meters >= m), 12)
    
    def get_children(self, cell_id: str) -> List[str]:
        """Get child cells at next resolution"""
        return [str(c) for c in h3.h3_to_children(cell_id)]
    
    def get_parent(self, cell_id: str) -> str:
        """Get parent cell at previous resolution"""
        return str(h3.h3_to_parent(cell_id))
    
    def get_distance(self, cell_id1: str, cell_id2: str) -> int:
        """Get grid distance between two cells"""
        return h3.h3_distance(cell_id1, cell_id2) 