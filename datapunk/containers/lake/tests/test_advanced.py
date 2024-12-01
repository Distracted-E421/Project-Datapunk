import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import numpy as np

from ..src.storage.index.advanced import (
    AdvancedIndexManager,
    BitmapIndex,
    BloomFilter,
    BloomFilterConfig,
    MultiColumnIndex,
    MaterializedViewConfig,
    MaterializedViewManager,
    DynamicIndexRewriter,
    IndexFeature
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.optimizer import IndexOptimizer

class TestAdvancedIndexing(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_stats.db"
        self.config_path = Path(self.temp_dir) / "advanced_config.json"
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.manager = IndexManager(self.store)
        self.optimizer = IndexOptimizer(self.store)
        
        # Create test configuration
        config = {
            "bitmap_cardinality_threshold": 10,
            "bloom_filter": {
                "size_bits": 1000,
                "num_hashes": 3,
                "false_positive_rate": 0.01
            },
            "materialized_view": {
                "max_views": 5,
                "min_refresh_interval": 60
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        self.advanced = AdvancedIndexManager(
            self.store,
            self.manager,
            self.optimizer,
            self.config_path
        )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_bitmap_index(self):
        """Test bitmap index functionality."""
        # Create bitmap index
        index = self.advanced.create_bitmap_index("test_bitmap")
        
        # Add values
        self.assertTrue(index.add_value("A", 0))
        self.assertTrue(index.add_value("B", 1))
        self.assertTrue(index.add_value("A", 2))
        
        # Test queries
        result = index.query("=", "A")
        self.assertEqual(result.to01(), "101")
        
        result = index.query("in", ["A", "B"])
        self.assertEqual(result.to01(), "111")
        
        # Test cardinality threshold
        for i in range(20):
            index.add_value(f"value_{i}", i)
            
        self.assertFalse(index.add_value("overflow", 21))
        
    def test_bloom_filter(self):
        """Test bloom filter functionality."""
        # Create bloom filter
        filter = self.advanced.create_bloom_filter(
            "test_bloom",
            expected_items=100
        )
        
        # Add items
        test_items = ["item1", "item2", "item3"]
        for item in test_items:
            filter.add(item)
            
        # Test membership
        for item in test_items:
            self.assertTrue(filter.contains(item))
            
        # Test false positive rate
        false_positives = 0
        test_size = 1000
        for i in range(test_size):
            if filter.contains(f"non_existent_{i}"):
                false_positives += 1
                
        fp_rate = false_positives / test_size
        self.assertLess(fp_rate, 0.1)  # Should be well below 10%
        
        # Test merge
        other_filter = self.advanced.create_bloom_filter(
            "other_bloom",
            expected_items=100
        )
        other_filter.add("item4")
        
        filter.merge(other_filter)
        self.assertTrue(filter.contains("item4"))
        
    def test_multi_column_index(self):
        """Test multi-column index functionality."""
        # Create multi-column index
        columns = ["col1", "col2", "col3"]
        index = self.advanced.create_multi_column_index(
            "test_multi",
            columns
        )
        
        # Create test data
        data = [
            {"col1": 1, "col2": 10, "col3": 100},
            {"col1": 2, "col2": 20, "col3": 200},
            {"col1": 3, "col2": 30, "col3": 300},
            {"col1": None, "col2": 40, "col3": 400}
        ]
        
        # Analyze columns
        index.analyze_columns(data)
        
        # Test statistics
        self.assertEqual(
            index.column_stats["col1"]["distinct_count"],
            3
        )
        self.assertEqual(
            index.column_stats["col1"]["null_count"],
            1
        )
        
        # Test correlation matrix
        self.assertIsNotNone(index.correlation_matrix)
        self.assertEqual(
            index.correlation_matrix.shape,
            (3, 3)
        )
        
        # Test index order recommendation
        order = index.recommend_index_order()
        self.assertEqual(len(order), 3)
        self.assertIn("col1", order)
        
    def test_materialized_view(self):
        """Test materialized view functionality."""
        # Create view configuration
        config = MaterializedViewConfig(
            view_name="test_view",
            base_tables=["table1"],
            refresh_interval=60,
            query_pattern="SELECT col1, SUM(col2) FROM table1 GROUP BY col1",
            aggregations={
                "col1": "group_by",
                "col2": "sum"
            },
            last_refresh=datetime.now()
        )
        
        # Create view
        self.advanced.create_materialized_view(config)
        
        # Test data
        data = [
            {"col1": "A", "col2": 10},
            {"col1": "A", "col2": 20},
            {"col1": "B", "col2": 30}
        ]
        
        # Refresh view
        self.advanced.view_manager.refresh_view("test_view", data)
        
        # Get view data
        result = self.advanced.view_manager.get_view_data(
            "test_view",
            max_age_seconds=120
        )
        
        self.assertEqual(len(result), 2)  # Two groups
        self.assertEqual(
            sum(r["col2_sum"] for r in result),
            60  # Total sum
        )
        
    def test_dynamic_rewriting(self):
        """Test dynamic query rewriting."""
        # Add rewrite rule
        def condition(query: str) -> bool:
            return "table1" in query
            
        self.advanced.add_rewrite_rule(
            "table1",
            "table1_optimized",
            condition
        )
        
        # Test query rewriting
        query = "SELECT * FROM table1 WHERE col1 = 'value'"
        rewritten = self.advanced.rewriter.rewrite_query(query)
        
        self.assertIn("table1_optimized", rewritten)
        self.assertNotEqual(query, rewritten)
        
    def test_configuration_handling(self):
        """Test configuration handling."""
        # Test default config
        advanced_default = AdvancedIndexManager(
            self.store,
            self.manager,
            self.optimizer
        )
        self.assertIsNotNone(advanced_default.config)
        
        # Test custom config
        self.assertEqual(
            self.advanced.config["bitmap_cardinality_threshold"],
            10
        )
        
    def test_feature_integration(self):
        """Test integration of multiple features."""
        # Create bitmap index
        bitmap = self.advanced.create_bitmap_index("bitmap_test")
        bitmap.add_value("key1", 0)
        
        # Create bloom filter
        bloom = self.advanced.create_bloom_filter("bloom_test", 100)
        bloom.add("key1")
        
        # Create multi-column index
        multi = self.advanced.create_multi_column_index(
            "multi_test",
            ["col1", "col2"]
        )
        
        # Test combined usage
        # 1. Use bitmap to find rows
        matching_rows = bitmap.query("=", "key1")
        
        # 2. Verify with bloom filter
        self.assertTrue(bloom.contains("key1"))
        
        # 3. Get optimal column order
        columns = multi.recommend_index_order()
        self.assertEqual(len(columns), 2)
        
    def test_error_handling(self):
        """Test error handling in advanced features."""
        # Test invalid bitmap query
        bitmap = self.advanced.create_bitmap_index("error_test")
        with self.assertRaises(ValueError):
            bitmap.query("invalid_operator", "value")
            
        # Test invalid bloom filter merge
        bloom1 = self.advanced.create_bloom_filter("bloom1", 100)
        bloom2 = self.advanced.create_bloom_filter("bloom2", 200)
        with self.assertRaises(ValueError):
            bloom1.merge(bloom2)
            
        # Test invalid view refresh
        with self.assertRaises(ValueError):
            self.advanced.view_manager.refresh_view(
                "non_existent_view",
                []
            ) 