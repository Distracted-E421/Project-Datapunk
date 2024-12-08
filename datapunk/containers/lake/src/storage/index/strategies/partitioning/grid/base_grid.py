from abc import ABC, abstractmethod
from typing import List, Tuple
from shapely.geometry import Polygon

class GridSystem(ABC):
    """Abstract base class for grid systems"""
    
    @abstractmethod
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to a grid cell ID"""
        pass
    
    @abstractmethod
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        """Decode a cell ID to its center point"""
        pass
    
    @abstractmethod
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring cell IDs"""
        pass
        
    @abstractmethod
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of a cell"""
        pass 