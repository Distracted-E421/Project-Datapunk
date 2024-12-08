from typing import Dict, Type, List
from .base_grid import GridSystem
from .geohash import GeohashGrid
from .h3 import H3Grid
from .s2 import S2Grid
from .quadkey import QuadkeyGrid
from .rtree import RTreeGrid

class GridFactory:
    """Factory class for creating grid systems"""
    
    _grid_types: Dict[str, Type[GridSystem]] = {
        'geohash': GeohashGrid,
        'h3': H3Grid,
        's2': S2Grid,
        'quadkey': QuadkeyGrid,
        'rtree': RTreeGrid
    }
    
    @classmethod
    def create_grid(cls, grid_type: str) -> GridSystem:
        """Create a grid system instance"""
        if grid_type not in cls._grid_types:
            raise ValueError(f"Unsupported grid system: {grid_type}")
        return cls._grid_types[grid_type]()
    
    @classmethod
    def register_grid_type(cls, name: str, grid_class: Type[GridSystem]):
        """Register a new grid system type"""
        cls._grid_types[name] = grid_class
    
    @classmethod
    def get_available_grids(cls) -> List[str]:
        """Get list of available grid system types"""
        return list(cls._grid_types.keys()) 