import unittest
from datetime import datetime, timedelta
import pytz
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
    GeoPoint
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