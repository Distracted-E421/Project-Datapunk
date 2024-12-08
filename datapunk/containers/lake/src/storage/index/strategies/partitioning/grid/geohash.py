from typing import List, Tuple
import pygeohash as pgh
from shapely.geometry import Polygon
from .base_grid import GridSystem

class GeohashGrid(GridSystem):
    """Geohash-based grid system"""
    
    def encode_point(self, lat: float, lng: float, precision: int) -> str:
        """Encode a point to a Geohash"""
        return pgh.encode(lat, lng, precision)
    
    def decode_cell(self, cell_id: str) -> Tuple[float, float]:
        """Decode a Geohash to its center point"""
        lat, lng = pgh.decode(cell_id)
        return lat, lng
    
    def get_neighbors(self, cell_id: str) -> List[str]:
        """Get neighboring Geohashes"""
        return list(pgh.neighbors(cell_id).values())
    
    def get_cell_polygon(self, cell_id: str) -> Polygon:
        """Get polygon representation of a Geohash cell"""
        lat, lng = self.decode_cell(cell_id)
        lat_err, lng_err = pgh.decode_exactly(cell_id)[2:]
        
        return Polygon([
            (lng - lng_err, lat - lat_err),
            (lng + lng_err, lat - lat_err),
            (lng + lng_err, lat + lat_err),
            (lng - lng_err, lat + lat_err)
        ])
    
    def get_precision(self, meters: float) -> int:
        """Get appropriate precision for given distance in meters"""
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