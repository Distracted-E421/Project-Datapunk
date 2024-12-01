import unittest
import numpy as np
from typing import List

from ..src.storage.geometry import Point, BoundingBox, Polygon
from ..src.storage.index.rtree import RTreeIndex

class TestPoint(unittest.TestCase):
    def test_creation(self):
        p = Point(1.0, 2.0)
        self.assertEqual(p.dimension(), 2)
        self.assertEqual(p[0], 1.0)
        self.assertEqual(p[1], 2.0)
        
    def test_distance(self):
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)
        self.assertEqual(p1.distance_to(p2), 5.0)
        
    def test_indexing(self):
        p = Point(1.0, 2.0, 3.0)
        self.assertEqual(len(p), 3)
        self.assertEqual(p[2], 3.0)

class TestBoundingBox(unittest.TestCase):
    def setUp(self):
        self.box1 = BoundingBox(Point(0, 0), Point(2, 2))
        self.box2 = BoundingBox(Point(1, 1), Point(3, 3))
        
    def test_creation(self):
        with self.assertRaises(ValueError):
            BoundingBox(Point(0, 0), Point(1, 1, 1))
            
    def test_empty(self):
        box = BoundingBox.empty()
        self.assertFalse(box.is_valid())
        
    def test_area(self):
        self.assertEqual(self.box1.area(), 4.0)
        
    def test_perimeter(self):
        self.assertEqual(self.box1.perimeter(), 8.0)
        
    def test_union(self):
        union = self.box1.union(self.box2)
        self.assertEqual(union.min_point[0], 0)
        self.assertEqual(union.max_point[0], 3)
        
    def test_intersection(self):
        intersection = self.box1.intersection(self.box2)
        self.assertIsNotNone(intersection)
        self.assertEqual(intersection.min_point[0], 1)
        self.assertEqual(intersection.max_point[0], 2)
        
    def test_contains_point(self):
        self.assertTrue(self.box1.contains_point(Point(1, 1)))
        self.assertFalse(self.box1.contains_point(Point(3, 3)))
        
    def test_contains_box(self):
        small_box = BoundingBox(Point(0.5, 0.5), Point(1.5, 1.5))
        self.assertTrue(self.box1.contains_box(small_box))
        self.assertFalse(self.box1.contains_box(self.box2))
        
    def test_intersects(self):
        self.assertTrue(self.box1.intersects(self.box2))
        non_intersecting = BoundingBox(Point(3, 3), Point(4, 4))
        self.assertFalse(self.box1.intersects(non_intersecting))
        
    def test_distance_to_point(self):
        self.assertEqual(self.box1.distance_to_point(Point(3, 3)), np.sqrt(2))
        self.assertEqual(self.box1.distance_to_point(Point(1, 1)), 0)

class TestPolygon(unittest.TestCase):
    def setUp(self):
        self.square = Polygon([
            Point(0, 0),
            Point(2, 0),
            Point(2, 2),
            Point(0, 2)
        ])
        
    def test_creation(self):
        with self.assertRaises(ValueError):
            Polygon([Point(0, 0), Point(1, 1)])
            
    def test_bounding_box(self):
        bbox = self.square.bounding_box()
        self.assertEqual(bbox.min_point[0], 0)
        self.assertEqual(bbox.max_point[0], 2)
        
    def test_area(self):
        self.assertEqual(self.square.area(), 4.0)
        
    def test_contains_point(self):
        self.assertTrue(self.square.contains_point(Point(1, 1)))
        self.assertFalse(self.square.contains_point(Point(3, 3)))
        
    def test_intersects_box(self):
        box = BoundingBox(Point(1, 1), Point(3, 3))
        self.assertTrue(self.square.intersects_box(box))
        
        non_intersecting = BoundingBox(Point(3, 3), Point(4, 4))
        self.assertFalse(self.square.intersects_box(non_intersecting))

class TestRTreeIndex(unittest.TestCase):
    def setUp(self):
        self.index = RTreeIndex(
            name="test_rtree",
            table_name="test_table",
            columns=["geom"],
            max_entries=4
        )
        
        # Create some test data
        self.points = [
            (Point(1, 1), "A"),
            (Point(2, 2), "B"),
            (Point(3, 3), "C"),
            (Point(4, 4), "D"),
            (Point(5, 5), "E")
        ]
        
        for point, value in self.points:
            bbox = BoundingBox(point, point)
            self.index.insert(bbox, value)
            
    def test_search(self):
        # Search around point B
        search_box = BoundingBox(Point(1.5, 1.5), Point(2.5, 2.5))
        results = self.index.search(search_box)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "B")
        
        # Search larger area
        search_box = BoundingBox(Point(0, 0), Point(3, 3))
        results = self.index.search(search_box)
        self.assertEqual(len(results), 3)
        self.assertIn("A", results)
        self.assertIn("B", results)
        self.assertIn("C", results)
        
    def test_nearest(self):
        # Find nearest to point (2.2, 2.2)
        query_point = Point(2.2, 2.2)
        results = self.index.nearest(query_point, k=2)
        
        self.assertEqual(len(results), 2)
        # B should be closest
        self.assertEqual(results[0][0], "B")
        
    def test_statistics(self):
        stats = self.index.get_statistics()
        self.assertEqual(stats.total_entries, 5)
        self.assertTrue(stats.depth >= 2)  # Should have split at least once
        self.assertTrue(stats.avg_insert_time_ms > 0)
        
    def test_large_dataset(self):
        # Create a larger dataset to test performance
        large_index = RTreeIndex(
            name="large_rtree",
            table_name="test_table",
            columns=["geom"]
        )
        
        # Insert 1000 random points
        np.random.seed(42)
        points = []
        for i in range(1000):
            x = np.random.uniform(0, 100)
            y = np.random.uniform(0, 100)
            point = Point(x, y)
            bbox = BoundingBox(point, point)
            points.append((bbox, f"P{i}"))
            large_index.insert(bbox, f"P{i}")
            
        # Test search performance
        search_box = BoundingBox(Point(40, 40), Point(60, 60))
        results = large_index.search(search_box)
        
        # Verify results
        for value in results:
            original_point = next(p[0].min_point for p in points if p[1] == value)
            self.assertTrue(search_box.contains_point(original_point))
            
        # Test nearest neighbor performance
        query_point = Point(50, 50)
        nearest = large_index.nearest(query_point, k=10)
        self.assertEqual(len(nearest), 10)
        
        # Verify distances are in ascending order
        distances = [dist for _, dist in nearest]
        self.assertEqual(distances, sorted(distances))
        
    def test_concurrent_operations(self):
        import threading
        import random
        
        def insert_random_points(thread_id: int, count: int):
            for i in range(count):
                x = random.uniform(0, 100)
                y = random.uniform(0, 100)
                point = Point(x, y)
                bbox = BoundingBox(point, point)
                self.index.insert(bbox, f"T{thread_id}P{i}")
                
        # Create multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(
                target=insert_random_points,
                args=(i, 100)
            )
            threads.append(thread)
            
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for completion
        for thread in threads:
            thread.join()
            
        # Verify the index is still consistent
        stats = self.index.get_statistics()
        self.assertEqual(stats.total_entries, 305)  # 5 original + 300 new
        
        # Test search still works
        search_box = BoundingBox(Point(0, 0), Point(100, 100))
        results = self.index.search(search_box)
        self.assertEqual(len(results), 305) 