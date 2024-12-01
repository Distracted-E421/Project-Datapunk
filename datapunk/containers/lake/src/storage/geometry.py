from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass

@dataclass
class Point:
    """A point in n-dimensional space."""
    coordinates: np.ndarray
    
    def __init__(self, *coords):
        self.coordinates = np.array(coords, dtype=float)
        
    def dimension(self) -> int:
        return len(self.coordinates)
        
    def distance_to(self, other: 'Point') -> float:
        return np.sqrt(np.sum((self.coordinates - other.coordinates) ** 2))
        
    def __getitem__(self, index: int) -> float:
        return self.coordinates[index]
        
    def __len__(self) -> int:
        return len(self.coordinates)

class BoundingBox:
    """Axis-aligned bounding box in n-dimensional space."""
    
    def __init__(self, min_point: Point, max_point: Point):
        if len(min_point) != len(max_point):
            raise ValueError("Points must have same dimension")
        self.min_point = min_point
        self.max_point = max_point
        
    @staticmethod
    def empty() -> 'BoundingBox':
        """Create an empty bounding box."""
        return BoundingBox(
            Point(float('inf'), float('inf')),
            Point(float('-inf'), float('-inf'))
        )
        
    def dimension(self) -> int:
        return len(self.min_point)
        
    def center(self) -> Point:
        coords = (self.min_point.coordinates + self.max_point.coordinates) / 2
        return Point(*coords)
        
    def area(self) -> float:
        """Calculate the area (volume in n-dimensions) of the box."""
        if not self.is_valid():
            return 0
        sides = self.max_point.coordinates - self.min_point.coordinates
        return float(np.prod(sides))
        
    def perimeter(self) -> float:
        """Calculate the perimeter (surface area in n-dimensions) of the box."""
        if not self.is_valid():
            return 0
        sides = self.max_point.coordinates - self.min_point.coordinates
        return float(np.sum(sides))
        
    def union(self, other: 'BoundingBox') -> 'BoundingBox':
        """Create a new box that contains both boxes."""
        min_coords = np.minimum(self.min_point.coordinates, other.min_point.coordinates)
        max_coords = np.maximum(self.max_point.coordinates, other.max_point.coordinates)
        return BoundingBox(Point(*min_coords), Point(*max_coords))
        
    def intersection(self, other: 'BoundingBox') -> Optional['BoundingBox']:
        """Create a new box that represents the intersection."""
        min_coords = np.maximum(self.min_point.coordinates, other.min_point.coordinates)
        max_coords = np.minimum(self.max_point.coordinates, other.max_point.coordinates)
        
        if np.any(min_coords > max_coords):
            return None
            
        return BoundingBox(Point(*min_coords), Point(*max_coords))
        
    def intersection_area(self, other: 'BoundingBox') -> float:
        """Calculate the area of intersection between two boxes."""
        intersection = self.intersection(other)
        return intersection.area() if intersection else 0
        
    def contains_point(self, point: Point) -> bool:
        """Check if the box contains a point."""
        return np.all(
            (point.coordinates >= self.min_point.coordinates) &
            (point.coordinates <= self.max_point.coordinates)
        )
        
    def contains_box(self, other: 'BoundingBox') -> bool:
        """Check if this box fully contains another box."""
        return np.all(
            (other.min_point.coordinates >= self.min_point.coordinates) &
            (other.max_point.coordinates <= self.max_point.coordinates)
        )
        
    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if two boxes intersect."""
        return np.all(
            (self.min_point.coordinates <= other.max_point.coordinates) &
            (self.max_point.coordinates >= other.min_point.coordinates)
        )
        
    def distance_to_point(self, point: Point) -> float:
        """Calculate the minimum distance from the box to a point."""
        # For each dimension, get the distance to the closest face
        diff = np.maximum(0,
            np.maximum(
                self.min_point.coordinates - point.coordinates,
                point.coordinates - self.max_point.coordinates
            )
        )
        return float(np.sqrt(np.sum(diff * diff)))
        
    def is_valid(self) -> bool:
        """Check if the box is valid (min <= max in all dimensions)."""
        return np.all(self.min_point.coordinates <= self.max_point.coordinates)
        
    def expand(self, margin: float) -> 'BoundingBox':
        """Create a new box expanded by a margin in all directions."""
        margin_vector = np.full_like(self.min_point.coordinates, margin)
        min_coords = self.min_point.coordinates - margin_vector
        max_coords = self.max_point.coordinates + margin_vector
        return BoundingBox(Point(*min_coords), Point(*max_coords))

@dataclass
class Polygon:
    """A polygon defined by a list of points."""
    points: List[Point]
    
    def __init__(self, points: List[Point]):
        if len(points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        self.points = points
        
    def bounding_box(self) -> BoundingBox:
        """Calculate the bounding box of the polygon."""
        coords = np.array([p.coordinates for p in self.points])
        min_coords = np.min(coords, axis=0)
        max_coords = np.max(coords, axis=0)
        return BoundingBox(Point(*min_coords), Point(*max_coords))
        
    def area(self) -> float:
        """Calculate the area of the polygon using the shoelace formula."""
        if len(self.points) < 3:
            return 0
            
        # Convert to 2D if necessary
        points_2d = [(p[0], p[1]) for p in self.points]
        points_2d.append(points_2d[0])  # Close the polygon
        
        area = 0
        for i in range(len(points_2d) - 1):
            x1, y1 = points_2d[i]
            x2, y2 = points_2d[i + 1]
            area += x1 * y2 - x2 * y1
            
        return abs(area) / 2
        
    def contains_point(self, point: Point) -> bool:
        """Check if the polygon contains a point using ray casting."""
        if len(self.points) < 3:
            return False
            
        # Convert to 2D if necessary
        x, y = point[0], point[1]
        points_2d = [(p[0], p[1]) for p in self.points]
        
        inside = False
        j = len(points_2d) - 1
        
        for i in range(len(points_2d)):
            xi, yi = points_2d[i]
            xj, yj = points_2d[j]
            
            if ((yi > y) != (yj > y) and
                x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
                
            j = i
            
        return inside
        
    def intersects_box(self, box: BoundingBox) -> bool:
        """Check if the polygon intersects with a bounding box."""
        # First check if any polygon point is inside the box
        if any(box.contains_point(p) for p in self.points):
            return True
            
        # Then check if any box edge intersects any polygon edge
        box_points = [
            Point(box.min_point[0], box.min_point[1]),
            Point(box.max_point[0], box.min_point[1]),
            Point(box.max_point[0], box.max_point[1]),
            Point(box.min_point[0], box.max_point[1])
        ]
        
        # Check polygon edges against box edges
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            
            for j in range(len(box_points)):
                b1 = box_points[j]
                b2 = box_points[(j + 1) % len(box_points)]
                
                if self._line_segments_intersect(
                    (p1[0], p1[1]), (p2[0], p2[1]),
                    (b1[0], b1[1]), (b2[0], b2[1])
                ):
                    return True
                    
        return False
        
    @staticmethod
    def _line_segments_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                               p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """Check if two line segments intersect."""
        def ccw(A: Tuple[float, float], B: Tuple[float, float],
                C: Tuple[float, float]) -> bool:
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
            
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4) 