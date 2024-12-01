import unittest
from datetime import datetime, timedelta
import tempfile
import os
import json
import yaml
import pandas as pd
import io
import zipfile
from pathlib import Path

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    IndexMaintenanceStats,
    StatisticsStore
)
from ..src.storage.index.exporter import (
    StatisticsExporter,
    ExportFormat,
    ExportMetadata
)

class TestStatisticsExporter(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        
        # Initialize store and exporter
        self.store = StatisticsStore(self.db_path)
        self.exporter = StatisticsExporter(self.store)
        
        # Create sample data
        self._create_sample_data()
        
    def tearDown(self):
        # Clean up temporary files
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)
        
    def _create_sample_data(self):
        """Create sample statistics for testing."""
        base_time = datetime.now() - timedelta(days=1)
        
        for i in range(24):  # 24 hours of data
            stats = IndexStats(
                index_name="test_index",
                table_name="test_table",
                index_type="btree",
                created_at=base_time + timedelta(hours=i),
                usage=IndexUsageStats(
                    total_reads=1000 + i * 100,
                    total_writes=500 + i * 50,
                    avg_read_time_ms=1.0 + i * 0.1,
                    avg_write_time_ms=2.0 + i * 0.1,
                    cache_hits=800 + i * 10,
                    cache_misses=200 + i * 5,
                    last_used=base_time + timedelta(hours=i)
                ),
                size=IndexSizeStats(
                    total_entries=10000 + i * 1000,
                    depth=4,
                    size_bytes=102400 + i * 1024,
                    fragmentation_ratio=0.1 + i * 0.01,
                    last_compacted=base_time
                ),
                condition=IndexConditionStats(
                    condition_string="status = 'active'",
                    selectivity=0.3,
                    false_positive_rate=0.1,
                    evaluation_time_ms=0.3,
                    last_optimized=base_time
                )
            )
            self.store.save_stats(stats)
            
            # Add some snapshots
            self.store.save_snapshot(
                "test_index",
                "performance",
                {
                    "read_time": 1.0 + i * 0.1,
                    "write_time": 2.0 + i * 0.1
                }
            )
            
    def test_json_export(self):
        # Test uncompressed JSON export
        output_path = os.path.join(self.temp_dir, "stats.json")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.JSON,
            compress=False
        )
        
        # Verify file exists and is valid JSON
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            data = json.load(f)
            
        self.assertIn("metadata", data)
        self.assertIn("statistics", data)
        self.assertEqual(len(data["statistics"]), 24)
        
        # Verify metadata
        self.assertEqual(metadata.index_count, 1)
        self.assertEqual(metadata.record_count, 24)
        self.assertEqual(metadata.format, ExportFormat.JSON)
        
        # Test compressed JSON export
        output_path = os.path.join(self.temp_dir, "stats.zip")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.JSON,
            compress=True
        )
        
        self.assertTrue(os.path.exists(output_path))
        self.assertTrue(zipfile.is_zipfile(output_path))
        
    def test_csv_export(self):
        output_path = os.path.join(self.temp_dir, "stats.csv")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.CSV
        )
        
        # Verify file exists and is valid CSV
        self.assertTrue(os.path.exists(output_path))
        df = pd.read_csv(output_path)
        
        # Verify data structure
        self.assertEqual(len(df), 24)
        self.assertIn("index_name", df.columns)
        self.assertIn("usage_total_reads", df.columns)
        self.assertIn("size_total_entries", df.columns)
        
        # Test with string buffer
        buffer = io.StringIO()
        self.exporter.export_stats(
            buffer,
            format=ExportFormat.CSV
        )
        
        buffer.seek(0)
        content = buffer.read()
        self.assertTrue(content.startswith("index_name,"))
        
    def test_yaml_export(self):
        output_path = os.path.join(self.temp_dir, "stats.yaml")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.YAML
        )
        
        # Verify file exists and is valid YAML
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            data = yaml.safe_load(f)
            
        self.assertIn("metadata", data)
        self.assertIn("statistics", data)
        
    def test_parquet_export(self):
        output_path = os.path.join(self.temp_dir, "stats.parquet")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.PARQUET
        )
        
        # Verify file exists and is valid Parquet
        self.assertTrue(os.path.exists(output_path))
        df = pd.read_parquet(output_path)
        
        self.assertEqual(len(df), 24)
        self.assertTrue(all(col in df.columns for col in [
            "index_name",
            "usage_total_reads",
            "size_total_entries"
        ]))
        
    def test_import_export_roundtrip(self):
        # Export data
        export_path = os.path.join(self.temp_dir, "export.json")
        export_metadata = self.exporter.export_stats(
            export_path,
            format=ExportFormat.JSON
        )
        
        # Clear database
        os.remove(self.db_path)
        self.store = StatisticsStore(self.db_path)
        self.exporter = StatisticsExporter(self.store)
        
        # Import data
        import_metadata = self.exporter.import_stats(
            export_path,
            format=ExportFormat.JSON
        )
        
        # Verify data was restored
        stats = self.store.get_stats_history("test_index")
        self.assertEqual(len(stats), 24)
        
        # Verify metadata matches
        self.assertEqual(export_metadata.index_count, import_metadata.index_count)
        self.assertEqual(export_metadata.record_count, import_metadata.record_count)
        
    def test_selective_export(self):
        # Create another index
        stats = IndexStats(
            index_name="another_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(),
            size=IndexSizeStats()
        )
        self.store.save_stats(stats)
        
        # Export only one index
        output_path = os.path.join(self.temp_dir, "selective.json")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.JSON,
            index_names=["test_index"]
        )
        
        self.assertEqual(metadata.index_count, 1)
        
        with open(output_path, 'r') as f:
            data = json.load(f)
            self.assertTrue(all(
                s["index_name"] == "test_index"
                for s in data["statistics"]
            ))
            
    def test_time_range_export(self):
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=12)
        
        output_path = os.path.join(self.temp_dir, "timerange.json")
        metadata = self.exporter.export_stats(
            output_path,
            format=ExportFormat.JSON,
            start_time=start_time,
            end_time=end_time
        )
        
        # Should only include last 12 hours
        self.assertLess(metadata.record_count, 24)
        
    def test_format_detection(self):
        # Test JSON detection
        self.assertEqual(
            self.exporter._detect_format("stats.json"),
            ExportFormat.JSON
        )
        
        # Test CSV detection
        self.assertEqual(
            self.exporter._detect_format("stats.csv"),
            ExportFormat.CSV
        )
        
        # Test YAML detection
        self.assertEqual(
            self.exporter._detect_format("stats.yaml"),
            ExportFormat.YAML
        )
        
        # Test invalid format
        with self.assertRaises(ValueError):
            self.exporter._detect_format("stats.invalid")
            
    def test_validation(self):
        # Test with invalid data
        invalid_data = {
            "metadata": {
                "version": "1.0"
            }
            # Missing statistics
        }
        
        with self.assertRaises(ValueError):
            self.exporter._validate_import(invalid_data)
            
        # Test with invalid statistics
        invalid_data = {
            "metadata": {"version": "1.0"},
            "statistics": [{
                "index_name": "test"
                # Missing required fields
            }]
        }
        
        with self.assertRaises(ValueError):
            self.exporter._validate_import(invalid_data)
            
    def test_dict_flattening(self):
        nested = {
            "a": {
                "b": {
                    "c": 1
                },
                "d": 2
            },
            "e": 3
        }
        
        flat = self.exporter._flatten_dict(nested)
        self.assertEqual(flat["a_b_c"], 1)
        self.assertEqual(flat["a_d"], 2)
        self.assertEqual(flat["e"], 3)
        
        # Test unflattening
        unflat = self.exporter._unflatten_dict(flat)
        self.assertEqual(unflat["a"]["b"]["c"], 1)
        self.assertEqual(unflat["a"]["d"], 2)
        self.assertEqual(unflat["e"], 3) 