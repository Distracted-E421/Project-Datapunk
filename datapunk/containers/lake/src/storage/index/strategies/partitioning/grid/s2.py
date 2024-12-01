from typing import List, Tuple
from s2sphere import CellId, LatLng
from shapely.geometry import Polygon
from .base import GridSystem

class S2Grid(GridSystem):
    """S2-based hierarchical grid system"""
    
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to an S2 cell ID"""
        ll = LatLng.from_degrees(lat, lng)
        cell = CellId.from_lat_lng(ll).parent(precision)
        return str(cell.id())
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        """Decode an S2 cell ID to its center point"""
        cell = CellId(int(cell_id))
        ll = cell.to_lat_lng()
        return ll.lat().degrees, ll.lng().degrees
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring S2 cells"""
        cell = CellId(int(cell_id))
        neighbors = []
        for i in range(4):  # Get all 4 adjacent cells
            neighbor = cell.get_edge_neighbors()[i]
            neighbors.append(str(neighbor.id()))
        return neighbors
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of an S2 cell"""
        cell = CellId(int(cell_id))
        vertices = []
        for i in range(4):
            vertex = cell.vertex(i)
            ll = vertex.to_lat_lng()
            vertices.append((ll.lng().degrees, ll.lat().degrees))
        return Polygon(vertices)
    
    def get_level(self, meters: float) -> int:
        """Get appropriate level for given distance in meters"""
        level_map = {
            1000000: 8,   # ~700km
            100000: 12,   # ~50km
            10000: 16,    # ~3km
            1000: 20,     # ~200m
            100: 24,      # ~10m
        }
        return next((l for m, l in level_map.items() if meters >= m), 24)
    
    def get_children(self, cell_id: str) -> List[str]:
        """Get child cells at next level"""
        cell = CellId(int(cell_id))
        return [str(child.id()) for child in cell.children()]
    
    def get_parent(self, cell_id: str) -> str:
        """Get parent cell at previous level"""
        cell = CellId(int(cell_id))
        return str(cell.parent().id())
    
    def contains(self, parent_id: str, child_id: str) -> bool:
        """Check if one cell contains another"""
        parent = CellId(int(parent_id))
        child = CellId(int(child_id))
        return parent.contains(child) 