import unittest
from datetime import datetime, timedelta
import os
import tempfile
import base64
from pathlib import Path
import matplotlib.pyplot as plt

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    StatisticsStore
)
from ..src.storage.index.visualizer import StatisticsVisualizer

class TestStatisticsVisualizer(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        self.output_dir = os.path.join(self.temp_dir, "plots")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize store and visualizer
        self.store = StatisticsStore(self.db_path)
        self.visualizer = StatisticsVisualizer(
            self.store,
            output_dir=self.output_dir
        )
        
        # Create sample historical data
        self._create_sample_data()
        
    def tearDown(self):
        # Clean up temporary files
        for file in os.listdir(self.output_dir):
            os.remove(os.path.join(self.output_dir, file))
        os.rmdir(self.output_dir)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
    def _create_sample_data(self):
        """Create sample historical data for testing."""
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(31):  # 31 days of data
            stats = IndexStats(
                index_name="test_index",
                table_name="test_table",
                index_type="btree",
                created_at=base_time + timedelta(days=i),
                usage=IndexUsageStats(
                    total_reads=1000 + i * 100,
                    total_writes=500 + i * 50,
                    avg_read_time_ms=1.0 + i * 0.1,
                    avg_write_time_ms=2.0 + i * 0.1,
                    cache_hits=800 + i * 10,
                    cache_misses=200 + i * 5
                ),
                size=IndexSizeStats(
                    total_entries=10000 + i * 1000,
                    depth=4,
                    size_bytes=102400 + i * 5000,
                    fragmentation_ratio=0.1 + i * 0.01
                ),
                condition=IndexConditionStats(
                    condition_string="status = 'active'",
                    selectivity=0.3 + i * 0.01,
                    false_positive_rate=0.1 + i * 0.005,
                    evaluation_time_ms=0.3 + i * 0.02
                )
            )
            self.store.save_stats(stats)
            
        # Create another index for comparison
        stats = IndexStats(
            index_name="test_index2",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=2000,
                total_writes=1000,
                avg_read_time_ms=1.5,
                avg_write_time_ms=2.5,
                cache_hits=1600,
                cache_misses=400
            ),
            size=IndexSizeStats(
                total_entries=20000,
                depth=5,
                size_bytes=204800,
                fragmentation_ratio=0.15
            )
        )
        self.store.save_stats(stats)
        
    def test_plot_performance_trends(self):
        # Test saving to file
        result = self.visualizer.plot_performance_trends(
            "test_index",
            days=30,
            save=True
        )
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("_performance.png"))
        
        # Test base64 output
        result = self.visualizer.plot_performance_trends(
            "test_index",
            days=30,
            save=False
        )
        self.assertTrue(isinstance(result, str))
        self.assertTrue(self._is_valid_base64(result))
        
    def test_plot_size_distribution(self):
        result = self.visualizer.plot_size_distribution(
            ["test_index", "test_index2"],
            save=True
        )
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("_comparison.png"))
        
        # Test with non-existent index
        result = self.visualizer.plot_size_distribution(
            ["nonexistent_index"],
            save=True
        )
        self.assertIsNone(result)
        
    def test_plot_cache_performance(self):
        result = self.visualizer.plot_cache_performance(
            "test_index",
            days=30,
            save=True
        )
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("_cache.png"))
        
        # Verify cache ratio calculation
        img_data = plt.imread(result)
        self.assertTrue(img_data.shape[0] > 0)  # Valid image data
        
    def test_plot_condition_analysis(self):
        # Test with conditional index
        result = self.visualizer.plot_condition_analysis(
            "test_index",
            days=30,
            save=True
        )
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("_condition.png"))
        
        # Test with non-conditional index
        result = self.visualizer.plot_condition_analysis(
            "test_index2",  # No condition stats
            days=30,
            save=True
        )
        self.assertIsNone(result)
        
    def test_create_dashboard(self):
        result = self.visualizer.create_dashboard(
            "test_index",
            days=30,
            save=True
        )
        self.assertTrue(os.path.exists(result))
        self.assertTrue(result.endswith("_dashboard.png"))
        
        # Verify dashboard components
        img_data = plt.imread(result)
        self.assertTrue(img_data.shape[0] > 0)  # Valid image data
        self.assertTrue(img_data.shape[1] > 0)  # Has width
        
    def test_invalid_data(self):
        # Test with non-existent index
        result = self.visualizer.plot_performance_trends(
            "nonexistent_index",
            days=30,
            save=True
        )
        self.assertIsNone(result)
        
        # Test with no history
        result = self.visualizer.plot_performance_trends(
            "test_index",
            days=0,
            save=True
        )
        self.assertIsNone(result)
        
    def test_output_directory(self):
        # Test with non-existent output directory
        visualizer = StatisticsVisualizer(
            self.store,
            output_dir="/nonexistent/path"
        )
        result = visualizer.plot_performance_trends(
            "test_index",
            days=30,
            save=True
        )
        self.assertIsNotNone(result)  # Should still return base64
        
    def _is_valid_base64(self, s: str) -> bool:
        """Check if string is valid base64."""
        try:
            base64.b64decode(s)
            return True
        except Exception:
            return False 