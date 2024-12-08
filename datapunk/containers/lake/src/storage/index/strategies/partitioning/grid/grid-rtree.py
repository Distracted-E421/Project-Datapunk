from typing import List, Tuple
from rtree import index
from shapely.geometry import Polygon
from .base_grid import GridSystem

class RTreeGrid(GridSystem):
    """R-tree based grid system"""
    
    def __init__(self):
        self.idx = index.Index()
        self.cell_counter = 0
        self.cell_bounds = {}
        
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to an R-tree cell ID"""
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
        """Decode an R-tree cell ID to its center point"""
        bounds = self.cell_bounds[cell_id]
        return ((bounds[1] + bounds[3]) / 2, 
                (bounds[0] + bounds[2]) / 2)
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring R-tree cells"""
        bounds = self.cell_bounds[cell_id]
        return [str(i) for i in self.idx.intersection(bounds)]
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of an R-tree cell"""
        bounds = self.cell_bounds[cell_id]
        return Polygon([
            (bounds[0], bounds[1]),  # minx, miny
            (bounds[2], bounds[1]),  # maxx, miny
            (bounds[2], bounds[3]),  # maxx, maxy
            (bounds[0], bounds[3])   # minx, maxy
        ])
    
    def range_query(self, bounds: Tuple[float, float, float, float]) -> List[str]:
        """Find all cells that intersect with given bounds"""
        return [str(i) for i in self.idx.intersection(bounds)]
    
    def nearest_neighbors(self, lat: float, lng: float, k: int = 5) -> List[str]:
        """Find k nearest cells to a point"""
        return [str(i) for i in self.idx.nearest((lng, lat, lng, lat), k)]
    
    def clear(self):
        """Clear all cells"""
        self.idx = index.Index()
        self.cell_counter = 0
        self.cell_bounds.clear() 