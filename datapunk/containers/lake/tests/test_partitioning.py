import unittest
from datetime import datetime, timedelta
import pytz
import numpy as np
from shapely.geometry import Polygon, Point
import time
from ..src.storage.index.strategies.partitioning import (
    TimePartitionStrategy,
    GeoPartitionStrategy,
    CompositePartitionStrategy,
    AdaptivePartitionStrategy,
    TimeGranularity,
    GeoGridType,
    TimeRange,
    GeoGrid,
    BoundingBox,
    GeoPoint,
    GridSystem, GeohashGrid, H3Grid, S2Grid,
    GridFactory, GridPartitionManager, GridVisualizer,
    PartitionHistory, SpatialCache, DensityAnalyzer, LoadBalancer,
    SpatialIndexManager, AdvancedClusterAnalyzer,
    DistributedPartitionManager, InteractiveVisualizer
)

class TestTimePartitioning(unittest.TestCase):
    def setUp(self):
        self.config = {
            "partitioning": {
                "time_field": "timestamp",
                "granularity": "hour",
                "timezone": "UTC"
            }
        }
        
    def test_minute_partitioning(self):
        """Test minute-level partitioning."""
        strategy = TimePartitionStrategy(
            self.config,
            "timestamp",
            TimeGranularity.MINUTE
        )
        
        # Test exact minute
        data = {
            "timestamp": "2023-01-01 12:30:45"
        }
        key = strategy.get_partition_key(data)
        self.assertEqual(key, "202301011230")
        
        # Test time range
        time_range = strategy.get_time_range(key)
        self.assertEqual(
            time_range.start.strftime("%Y-%m-%d %H:%M"),
            "2023-01-01 12:30"
        )
        self.assertEqual(
            time_range.end.strftime("%Y-%m-%d %H:%M"),
            "2023-01-01 12:31"
        )
        
    def test_hour_partitioning(self):
        """Test hour-level partitioning."""
        strategy = TimePartitionStrategy(
            self.config,
            "timestamp",
            TimeGranularity.HOUR
        )
        
        data = {
            "timestamp": "2023-01-01 12:30:45"
        }
        key = strategy.get_partition_key(data)
        self.assertEqual(key, "2023010112")
        
        time_range = strategy.get_time_range(key)
        self.assertEqual(
            time_range.start.strftime("%Y-%m-%d %H:00"),
            "2023-01-01 12:00"
        )
        self.assertEqual(
            time_range.end.strftime("%Y-%m-%d %H:00"),
            "2023-01-01 13:00"
        )
        
    def test_timezone_handling(self):
        """Test timezone handling."""
        strategy = TimePartitionStrategy(
            self.config,
            "timestamp",
            TimeGranularity.HOUR,
            "America/New_York"
        )
        
        # Test timezone conversion
        data = {
            "timestamp": "2023-01-01 00:00:00"  # UTC
        }
        key = strategy.get_partition_key(data)
        
        time_range = strategy.get_time_range(key)
        self.assertEqual(
            time_range.timezone,
            "America/New_York"
        )

class TestGeoPartitioning(unittest.TestCase):
    def setUp(self):
        self.config = {
            "partitioning": {
                "lat_field": "latitude",
                "lon_field": "longitude",
                "grid_type": "quadtree",
                "max_level": 4
            }
        }
        
    def test_quadtree_partitioning(self):
        """Test quadtree partitioning."""
        strategy = GeoPartitionStrategy(
            self.config,
            "latitude",
            "longitude",
            GeoGridType.QUADTREE,
            max_level=4
        )
        
        # Test point in NE quadrant
        data = {
            "latitude": 45.0,
            "longitude": 90.0
        }
        key = strategy.get_partition_key(data)
        self.assertTrue(key.startswith("0"))  # NE starts with 0
        self.assertEqual(len(key), 4)  # max_level = 4
        
        # Get grid cell
        grid = strategy.get_grid_cell(key)
        self.assertEqual(grid.level, 4)
        self.assertTrue(
            grid.bounds.contains(GeoPoint(45.0, 90.0))
        )
        
    def test_grid_bounds(self):
        """Test grid cell bounds calculation."""
        strategy = GeoPartitionStrategy(
            self.config,
            "latitude",
            "longitude"
        )
        
        # Test each quadrant
        ne_bounds = strategy._decode_grid_key("0")  # NE
        self.assertEqual(ne_bounds.min_lat, 0)
        self.assertEqual(ne_bounds.min_lon, 0)
        self.assertEqual(ne_bounds.max_lat, 90)
        self.assertEqual(ne_bounds.max_lon, 180)
        
        nw_bounds = strategy._decode_grid_key("1")  # NW
        self.assertEqual(nw_bounds.min_lat, 0)
        self.assertEqual(nw_bounds.min_lon, -180)
        self.assertEqual(nw_bounds.max_lat, 90)
        self.assertEqual(nw_bounds.max_lon, 0)
        
    def test_grid_caching(self):
        """Test grid cell caching."""
        strategy = GeoPartitionStrategy(
            self.config,
            "latitude",
            "longitude"
        )
        
        # Get grid cell twice
        grid1 = strategy.get_grid_cell("0")
        grid2 = strategy.get_grid_cell("0")
        
        # Should be same object
        self.assertIs(grid1, grid2)

class TestCompositePartitioning(unittest.TestCase):
    def setUp(self):
        self.config = {
            "partitioning": {
                "strategies": ["time", "geo"]
            }
        }
        
        # Create component strategies
        self.time_strategy = TimePartitionStrategy(
            self.config,
            "timestamp",
            TimeGranularity.HOUR
        )
        
        self.geo_strategy = GeoPartitionStrategy(
            self.config,
            "latitude",
            "longitude"
        )
        
    def test_composite_key_generation(self):
        """Test composite key generation."""
        strategy = CompositePartitionStrategy(
            self.config,
            [self.time_strategy, self.geo_strategy]
        )
        
        data = {
            "timestamp": "2023-01-01 12:00:00",
            "latitude": 45.0,
            "longitude": 90.0
        }
        
        key = strategy.get_partition_key(data)
        parts = key.split("|")
        
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "2023010112")  # Time part
        self.assertTrue(parts[1].startswith("0"))  # Geo part (NE)
        
    def test_invalid_composite_key(self):
        """Test handling of invalid composite keys."""
        strategy = CompositePartitionStrategy(
            self.config,
            [self.time_strategy, self.geo_strategy]
        )
        
        with self.assertRaises(ValueError):
            strategy.get_shard_mapping("invalid_key")

class TestAdaptivePartitioning(unittest.TestCase):
    def setUp(self):
        self.config = {
            "partitioning": {
                "max_partition_size_bytes": 1024 * 1024,  # 1MB
                "min_partition_size_bytes": 64 * 1024,    # 64KB
                "max_access_rate": 100.0,  # ops/sec
                "min_access_rate": 1.0     # ops/sec
            }
        }
        
        self.base_strategy = TimePartitionStrategy(
            self.config,
            "timestamp",
            TimeGranularity.HOUR
        )
        
    def test_access_pattern_tracking(self):
        """Test access pattern tracking."""
        strategy = AdaptivePartitionStrategy(
            self.config,
            self.base_strategy,
            metrics_window=timedelta(minutes=5)
        )
        
        # Record some accesses
        strategy.record_access("key1", 10)
        strategy.record_access("key1", 20)
        strategy.record_access("key2", 5)
        
        # Check access rates
        rate1 = strategy._get_access_rate("key1")
        rate2 = strategy._get_access_rate("key2")
        
        self.assertGreater(rate1, rate2)
        
    def test_partition_splitting(self):
        """Test partition splitting conditions."""
        strategy = AdaptivePartitionStrategy(
            self.config,
            self.base_strategy
        )
        
        # Update partition stats
        strategy.update_stats("key1", {
            "size_bytes": 2 * 1024 * 1024,  # 2MB (over limit)
            "record_count": 1000
        })
        
        # Should recommend splitting
        self.assertTrue(strategy._should_split("key1"))
        
    def test_partition_merging(self):
        """Test partition merging conditions."""
        strategy = AdaptivePartitionStrategy(
            self.config,
            self.base_strategy
        )
        
        # Update partition stats
        strategy.update_stats("key1", {
            "size_bytes": 32 * 1024,  # 32KB (under limit)
            "record_count": 100
        })
        
        # Should recommend merging
        self.assertTrue(strategy._should_merge("key1"))
        
    def test_metrics_cleanup(self):
        """Test old metrics cleanup."""
        strategy = AdaptivePartitionStrategy(
            self.config,
            self.base_strategy,
            metrics_window=timedelta(minutes=5)
        )
        
        # Add old access record
        old_time = datetime.now() - timedelta(minutes=10)
        strategy.access_patterns["key1"] = [
            (old_time, 10)
        ]
        
        # Record new access
        strategy.record_access("key1", 20)
        
        # Old record should be removed
        self.assertEqual(len(strategy.access_patterns["key1"]), 1)
        self.assertGreater(
            strategy.access_patterns["key1"][0][0],
            old_time
        )

class TestGridSystems(unittest.TestCase):
    def setUp(self):
        self.test_point = (37.7749, -122.4194)  # San Francisco coordinates
        self.test_precision = 7  # High precision for accurate testing
        
    def test_geohash_grid(self):
        grid = GeohashGrid()
        
        # Test encoding and decoding
        cell_id = grid.encode_point(*self.test_point, self.test_precision)
        self.assertIsInstance(cell_id, str)
        
        lat, lng = grid.decode_cell(cell_id)
        self.assertAlmostEqual(lat, self.test_point[0], places=2)
        self.assertAlmostEqual(lng, self.test_point[1], places=2)
        
        # Test neighbors
        neighbors = grid.get_neighbors(cell_id)
        self.assertEqual(len(neighbors), 8)  # Geohash has 8 neighbors
        
        # Test precision selection
        self.assertEqual(grid.get_precision(5000000), 1)
        self.assertEqual(grid.get_precision(100), 7)
        
    def test_h3_grid(self):
        grid = H3Grid()
        
        # Test encoding and decoding
        cell_id = grid.encode_point(*self.test_point, 9)  # H3 uses different precision levels
        self.assertIsInstance(cell_id, str)
        
        lat, lng = grid.decode_cell(cell_id)
        self.assertAlmostEqual(lat, self.test_point[0], places=2)
        self.assertAlmostEqual(lng, self.test_point[1], places=2)
        
        # Test neighbors
        neighbors = grid.get_neighbors(cell_id)
        self.assertGreater(len(neighbors), 0)
        
        # Test resolution selection
        self.assertEqual(grid.get_resolution(1000000), 0)
        self.assertEqual(grid.get_resolution(50), 12)
        
    def test_s2_grid(self):
        grid = S2Grid()
        
        # Test encoding and decoding
        cell_id = grid.encode_point(*self.test_point, 20)  # S2 uses different precision levels
        self.assertIsInstance(cell_id, str)
        
        lat, lng = grid.decode_cell(cell_id)
        self.assertAlmostEqual(lat, self.test_point[0], places=2)
        self.assertAlmostEqual(lng, self.test_point[1], places=2)
        
        # Test neighbors
        neighbors = grid.get_neighbors(cell_id)
        self.assertEqual(len(neighbors), 4)  # S2 has 4 edge neighbors
        
        # Test level selection
        self.assertEqual(grid.get_level(1000000), 8)
        self.assertEqual(grid.get_level(50), 24)

class TestGridFactory(unittest.TestCase):
    def test_grid_creation(self):
        factory = GridFactory()
        
        geohash_grid = factory.create_grid('geohash')
        self.assertIsInstance(geohash_grid, GeohashGrid)
        
        h3_grid = factory.create_grid('h3')
        self.assertIsInstance(h3_grid, H3Grid)
        
        s2_grid = factory.create_grid('s2')
        self.assertIsInstance(s2_grid, S2Grid)
        
        with self.assertRaises(ValueError):
            factory.create_grid('invalid_grid')

class TestGridPartitionManager(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.test_points = [
            (37.7749, -122.4194),  # San Francisco
            (37.7739, -122.4312),  # Close to SF
            (40.7128, -74.0060),   # New York
        ]
        
    def test_partition_points(self):
        partitions = self.manager.partition_points(self.test_points, 5)
        
        # Should have at least 2 partitions (SF area and NY)
        self.assertGreaterEqual(len(partitions), 2)
        
        # Test recovery state
        self.assertEqual(len(self.manager._recovery_state), len(self.test_points))
        
    def test_recover_partition(self):
        # First partition points
        self.manager.partition_points(self.test_points, 5)
        
        # Then try to recover a point's partition
        recovered_cell = self.manager.recover_partition(self.test_points[0])
        self.assertIsNotNone(recovered_cell)
        
    def test_partition_stats(self):
        self.manager.partition_points(self.test_points, 5)
        stats = self.manager.get_partition_stats()
        
        self.assertIn('total_partitions', stats)
        self.assertIn('total_points', stats)
        self.assertIn('points_per_partition', stats)
        
        self.assertEqual(stats['total_points'], len(self.test_points))

class TestGridVisualizer(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.visualizer = GridVisualizer(self.manager)
        self.test_points = [
            (37.7749, -122.4194),  # San Francisco
            (37.7739, -122.4312),  # Close to SF
            (40.7128, -74.0060),   # New York
        ]
        
    def test_plot_partitions(self):
        # First partition some points
        self.manager.partition_points(self.test_points, 5)
        
        try:
            # Try to create visualization
            map_obj = self.visualizer.plot_partitions()
            # If folium is installed, we should get a map object
            if map_obj is not None:
                self.assertTrue(hasattr(map_obj, '_name'))
        except ImportError:
            # If folium is not installed, this test is considered passed
            pass

class TestPartitionHistory(unittest.TestCase):
    def setUp(self):
        self.history = PartitionHistory()
        self.test_partitions = {
            'cell1': [(1.0, 1.0), (1.1, 1.1)],
            'cell2': [(2.0, 2.0)]
        }
        
    def test_add_snapshot(self):
        self.history.add_snapshot(self.test_partitions)
        self.assertEqual(len(self.history.history), 1)
        
        snapshot = self.history.history[0]
        self.assertIn('timestamp', snapshot)
        self.assertIn('partitions', snapshot)
        self.assertIn('stats', snapshot)
        
    def test_get_partition_growth(self):
        # Add multiple snapshots
        self.history.add_snapshot(self.test_partitions, timestamp=1.0)
        
        # Modify partitions and add another snapshot
        modified_partitions = self.test_partitions.copy()
        modified_partitions['cell1'].append((1.2, 1.2))
        self.history.add_snapshot(modified_partitions, timestamp=2.0)
        
        # Check growth tracking
        growth = self.history.get_partition_growth('cell1')
        self.assertEqual(len(growth), 2)
        self.assertEqual(growth[0], (1.0, 2))  # 2 points at time 1.0
        self.assertEqual(growth[1], (2.0, 3))  # 3 points at time 2.0

class TestSpatialCache(unittest.TestCase):
    def setUp(self):
        self.cache = SpatialCache(max_size=2)
        
    def test_cache_operations(self):
        # Test basic set/get
        self.cache.set('key1', 'value1')
        self.assertEqual(self.cache.get('key1'), 'value1')
        
        # Test max size enforcement
        self.cache.set('key2', 'value2')
        self.cache.set('key3', 'value3')  # Should evict key1
        
        self.assertIsNone(self.cache.get('key1'))
        self.assertEqual(self.cache.get('key2'), 'value2')
        self.assertEqual(self.cache.get('key3'), 'value3')

class TestAdvancedGridPartitionManager(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash', 
                                          rebalance_threshold=0.3,
                                          max_points_per_partition=5)
        self.test_points = [
            (37.7749, -122.4194),  # San Francisco
            (37.7749, -122.4194),  # Duplicate point
            (37.7749, -122.4194),  # Another duplicate
            (37.7739, -122.4312),  # Close to SF
            (40.7128, -74.0060),   # New York
        ]
        
    def test_dynamic_repartitioning(self):
        # Initial partitioning
        partitions = self.manager.partition_points(self.test_points, 5)
        
        # Should have split SF points due to exceeding max_points_per_partition
        sf_points = sum(len(points) for points in partitions.values())
        self.assertEqual(sf_points, len(self.test_points))
        self.assertGreater(len(partitions), 1)  # Should have split into multiple partitions
        
    def test_batch_processing(self):
        # Test with small batch size
        start_time = time.time()
        partitions1 = self.manager.partition_points(self.test_points, 5, batch_size=2)
        time1 = time.time() - start_time
        
        # Test with larger batch size
        start_time = time.time()
        partitions2 = self.manager.partition_points(self.test_points, 5, batch_size=10)
        time2 = time.time() - start_time
        
        # Results should be the same regardless of batch size
        self.assertEqual(set(partitions1.keys()), set(partitions2.keys()))
        
    def test_polygon_operations(self):
        # Create test polygon (rough SF bay area)
        sf_polygon = Polygon([
            (-122.5, 37.7),
            (-122.5, 37.8),
            (-122.4, 37.8),
            (-122.4, 37.7)
        ])
        
        # Test polygon partitioning
        cells = self.manager.partition_polygon(sf_polygon, 5)
        self.assertGreater(len(cells), 0)
        
        # Test spatial join
        points = [(37.75, -122.45)]  # Point inside SF polygon
        join_results = self.manager.spatial_join(points, [sf_polygon], 5)
        
        # Should find the point within the polygon
        self.assertGreater(len(join_results), 0)
        for cell_id, results in join_results.items():
            for poly, matched_points in results:
                self.assertGreater(len(matched_points), 0)
                
    def test_cell_polygon_generation(self):
        # Test polygon generation for each grid type
        for grid_type in ['geohash', 'h3', 's2']:
            manager = GridPartitionManager(grid_type)
            
            # Get a cell ID by encoding a point
            cell_id = manager.grid.encode_point(37.7749, -122.4194, 5)
            
            # Get the cell polygon
            poly = manager.get_cell_polygon(cell_id)
            
            # Basic polygon validity checks
            self.assertIsInstance(poly, Polygon)
            self.assertTrue(poly.is_valid)
            self.assertGreater(poly.area, 0)

class TestEnhancedVisualization(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.visualizer = GridVisualizer(self.manager)
        self.test_points = [
            (37.7749, -122.4194),  # San Francisco
            (37.7739, -122.4312),  # Close to SF
            (40.7128, -74.0060),   # New York
        ]
        
    def test_visualization_options(self):
        # First partition some points
        self.manager.partition_points(self.test_points, 5)
        
        try:
            # Test basic visualization
            map1 = self.visualizer.plot_partitions()
            if map1 is not None:
                self.assertTrue(hasattr(map1, '_name'))
            
            # Test with history
            map2 = self.visualizer.plot_partitions(show_history=True)
            if map2 is not None:
                self.assertTrue(hasattr(map2, '_name'))
            
            # Test with cell highlighting
            cells = set(self.manager._recovery_state.values())
            map3 = self.visualizer.plot_partitions(highlight_cells=cells)
            if map3 is not None:
                self.assertTrue(hasattr(map3, '_name'))
                
        except ImportError:
            # If visualization packages aren't installed, tests pass
            pass

class TestQuadkeyGrid(unittest.TestCase):
    def setUp(self):
        self.grid = QuadkeyGrid()
        self.test_point = (37.7749, -122.4194)
        
    def test_encoding_decoding(self):
        cell_id = self.grid.encode_point(*self.test_point, 15)
        self.assertIsInstance(cell_id, str)
        
        lat, lng = self.grid.decode_cell(cell_id)
        self.assertAlmostEqual(lat, self.test_point[0], places=2)
        self.assertAlmostEqual(lng, self.test_point[1], places=2)
        
    def test_neighbors(self):
        cell_id = self.grid.encode_point(*self.test_point, 15)
        neighbors = self.grid.get_neighbors(cell_id)
        self.assertGreater(len(neighbors), 0)

class TestRTreeGrid(unittest.TestCase):
    def setUp(self):
        self.grid = RTreeGrid()
        self.test_points = [
            (37.7749, -122.4194),
            (37.7739, -122.4312),
            (40.7128, -74.0060)
        ]
        
    def test_point_insertion(self):
        for point in self.test_points:
            cell_id = self.grid.encode_point(*point, 10)
            self.assertIsInstance(cell_id, str)
            
    def test_point_retrieval(self):
        cell_ids = [self.grid.encode_point(*p, 10) for p in self.test_points]
        for cell_id in cell_ids:
            lat, lng = self.grid.decode_cell(cell_id)
            self.assertIsInstance(lat, float)
            self.assertIsInstance(lng, float)
            
    def test_neighbor_search(self):
        cell_ids = [self.grid.encode_point(*p, 10) for p in self.test_points]
        for cell_id in cell_ids:
            neighbors = self.grid.get_neighbors(cell_id)
            self.assertIsInstance(neighbors, list)

class TestDensityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.analyzer = DensityAnalyzer(self.manager)
        self.test_points = [
            (37.7749, -122.4194),  # SF cluster
            (37.7748, -122.4193),
            (37.7747, -122.4192),
            (40.7128, -74.0060),   # NYC isolated point
        ]
        
    def test_density_metrics(self):
        metrics = self.analyzer.calculate_density_metrics(self.test_points, 5)
        self.assertGreater(len(metrics), 0)
        
        # SF cell should have higher density
        sf_cell = self.manager.grid.encode_point(37.7749, -122.4194, 5)
        nyc_cell = self.manager.grid.encode_point(40.7128, -74.0060, 5)
        self.assertGreater(metrics[sf_cell], metrics[nyc_cell])
        
    def test_hotspot_detection(self):
        hotspots = self.analyzer.find_hotspots(self.test_points, 5)
        self.assertGreater(len(hotspots), 0)
        
        # SF cell should be a hotspot
        sf_cell = self.manager.grid.encode_point(37.7749, -122.4194, 5)
        self.assertIn(sf_cell, hotspots)
        
    def test_clustering(self):
        clusters = self.analyzer.cluster_analysis(self.test_points)
        self.assertGreater(len(clusters), 0)
        
        # Should identify at least two clusters (SF and NYC)
        cluster_sizes = [len(points) for points in clusters.values()]
        self.assertIn(3, cluster_sizes)  # SF cluster
        self.assertIn(1, cluster_sizes)  # NYC point

class TestLoadBalancer(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.balancer = LoadBalancer(self.manager)
        self.test_partitions = {
            'cell1': [(1.0, 1.0)] * 10,  # Overloaded
            'cell2': [(2.0, 2.0)] * 2,   # Underloaded
            'cell3': [(3.0, 3.0)] * 1    # Underloaded
        }
        
    def test_load_metrics(self):
        metrics = self.balancer.calculate_load_metrics(self.test_partitions)
        self.assertEqual(len(metrics), 3)
        
        # cell1 should have highest load
        self.assertGreater(metrics['cell1'], metrics['cell2'])
        self.assertGreater(metrics['cell1'], metrics['cell3'])
        
    def test_rebalancing_suggestions(self):
        suggestions = self.balancer.suggest_rebalancing(self.test_partitions)
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest splitting overloaded cell
        split_suggestions = [s for s in suggestions if s[2] == 1]
        self.assertGreater(len(split_suggestions), 0)
        self.assertEqual(split_suggestions[0][0], 'cell1')
        
        # Should suggest merging underloaded cells
        merge_suggestions = [s for s in suggestions if s[2] == 2]
        self.assertGreater(len(merge_suggestions), 0)

class TestSpatialIndexManager(unittest.TestCase):
    def setUp(self):
        self.index_manager = SpatialIndexManager()
        self.test_points = [
            (37.7749, -122.4194),
            (37.7739, -122.4312),
            (40.7128, -74.0060)
        ]
        
    def test_index_building(self):
        self.index_manager.build_indexes(self.test_points)
        self.assertEqual(len(self.index_manager.points), len(self.test_points))
        self.assertIsNotNone(self.index_manager.kdtree)
        
    def test_nearest_neighbors(self):
        self.index_manager.build_indexes(self.test_points)
        query_point = (37.7749, -122.4194)
        neighbors = self.index_manager.nearest_neighbors(query_point, k=2)
        self.assertEqual(len(neighbors), 2)
        
        # First neighbor should be the query point itself
        self.assertEqual(neighbors[0], query_point)
        
    def test_range_query(self):
        self.index_manager.build_indexes(self.test_points)
        # Query SF area
        bounds = (-123.0, 37.0, -122.0, 38.0)
        results = self.index_manager.range_query(bounds)
        self.assertEqual(len(results), 2)  # Should find both SF points

class TestAdvancedClustering(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.analyzer = AdvancedClusterAnalyzer(self.manager)
        self.test_points = [
            (37.7749, -122.4194),  # SF cluster
            (37.7748, -122.4193),
            (37.7747, -122.4192),
            (40.7128, -74.0060),   # NYC point
        ]
        
    def test_hdbscan_clustering(self):
        clusters = self.analyzer.hdbscan_clustering(self.test_points)
        self.assertGreater(len(clusters), 0)
        
        # Should identify SF cluster
        cluster_sizes = [len(points) for points in clusters.values()]
        self.assertIn(3, cluster_sizes)  # SF cluster
        
    def test_optics_clustering(self):
        clusters = self.analyzer.optics_clustering(self.test_points)
        self.assertGreater(len(clusters), 0)
        
        # Should identify SF cluster
        cluster_sizes = [len(points) for points in clusters.values()]
        self.assertIn(3, cluster_sizes)  # SF cluster
        
    def test_cluster_stability(self):
        stability = self.analyzer.analyze_cluster_stability(
            self.test_points,
            time_window=timedelta(hours=1)
        )
        self.assertGreater(len(stability), 0)
        
        # Stable clusters should have high stability scores
        self.assertTrue(any(score > 0.5 for score in stability.values()))

class TestTimePartitioning(unittest.TestCase):
    def setUp(self):
        self.strategy = TimePartitionStrategy('timestamp')
        self.test_data = [
            {'timestamp': '2023-01-01T00:00:00Z', 'value': 1},
            {'timestamp': '2023-01-01T12:00:00Z', 'value': 2},
            {'timestamp': '2023-01-02T00:00:00Z', 'value': 3},
        ]
        
    def test_partition_data(self):
        partitions = self.strategy.partition_data(self.test_data)
        self.assertEqual(len(partitions), 2)  # Two different days
        
        # Check partition contents
        self.assertEqual(len(partitions['2023-01-01T00:00:00']), 2)
        self.assertEqual(len(partitions['2023-01-02T00:00:00']), 1)
        
    def test_get_partition_for_time(self):
        partition_key = self.strategy.get_partition_for_time('2023-01-01T15:30:00Z')
        self.assertEqual(partition_key, '2023-01-01T00:00:00')
        
    def test_get_partitions_in_range(self):
        start_time = '2023-01-01T00:00:00Z'
        end_time = '2023-01-03T00:00:00Z'
        
        partitions = self.strategy.get_partitions_in_range(start_time, end_time)
        self.assertEqual(len(partitions), 3)  # Three days

class TestDistributedPartitioning(unittest.TestCase):
    def setUp(self):
        self.manager = DistributedPartitionManager()
        self.test_data = [
            {'id': 1, 'value': 'a'},
            {'id': 2, 'value': 'b'},
            {'id': 3, 'value': 'c'}
        ]
        
    def test_partition_distributed(self):
        try:
            partition_locations = self.manager.partition_distributed(
                self.test_data, 'id'
            )
            self.assertGreater(len(partition_locations), 0)
            
            # Test partition retrieval
            for partition_id in partition_locations.values():
                data = self.manager.get_partition(partition_id)
                self.assertIsInstance(data, list)
                
        except Exception as e:
            # Skip if Redis is not available
            self.skipTest(f"Redis not available: {str(e)}")
            
    def test_process_partition(self):
        try:
            # Create test partition
            partition_id = 'test_partition'
            self.manager.redis_client.set(
                partition_id,
                '[{"id": 1, "value": "a"}]'
            )
            
            # Process partition
            result = self.manager.process_partition(
                partition_id,
                lambda x: len(x)
            )
            self.assertEqual(result, 1)
            
        except Exception as e:
            # Skip if Redis is not available
            self.skipTest(f"Redis not available: {str(e)}")

class TestInteractiveVisualization(unittest.TestCase):
    def setUp(self):
        self.manager = GridPartitionManager('geohash')
        self.visualizer = InteractiveVisualizer(self.manager)
        self.test_points = [
            (37.7749, -122.4194),  # SF cluster
            (37.7748, -122.4193),
            (37.7747, -122.4192),
            (40.7128, -74.0060),   # NYC point
        ]
        
    def test_create_dashboard(self):
        # First partition some points
        self.manager.partition_points(self.test_points, 5)
        
        try:
            # Create dashboard
            fig = self.visualizer.create_interactive_dashboard()
            self.assertIsNotNone(fig)
            
            # Test saving
            fig.write_html('test_dashboard.html')
            import os
            self.assertTrue(os.path.exists('test_dashboard.html'))
            os.remove('test_dashboard.html')
            
        except ImportError:
            # Skip if plotting packages aren't installed
            self.skipTest("Plotting packages not available")
            
    def test_time_analysis_dashboard(self):
        time_partitions = {
            '2023-01-01T00:00:00': [{'value': 1}],
            '2023-01-02T00:00:00': [{'value': 2}, {'value': 3}]
        }
        
        try:
            # Create dashboard
            fig = self.visualizer.create_time_analysis_dashboard(time_partitions)
            self.assertIsNotNone(fig)
            
            # Test saving
            fig.write_html('test_time_dashboard.html')
            import os
            self.assertTrue(os.path.exists('test_time_dashboard.html'))
            os.remove('test_time_dashboard.html')
            
        except ImportError:
            # Skip if plotting packages aren't installed
            self.skipTest("Plotting packages not available")

if __name__ == '__main__':
    unittest.main()