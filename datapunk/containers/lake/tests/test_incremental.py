import unittest
from datetime import datetime, timedelta
import tempfile
import os
import json
import shutil
from pathlib import Path

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    StatisticsStore
)
from ..src.storage.index.exporter import (
    StatisticsExporter,
    ExportFormat
)
from ..src.storage.index.incremental import (
    IncrementalExporter,
    ChangeSet,
    IncrementalMetadata
)
from ..src.storage.index.compression import CompressionLevel
from ..src.storage.index.migration import Migration

class TestMigration(Migration):
    """Test migration implementation."""
    
    def __init__(self):
        super().__init__("1.1.0", "Test migration")
        self.changes = ["Added new field"]
        
    def upgrade(self, data):
        """Add new_field to all records."""
        for record in data.get("statistics", []):
            record["new_field"] = "test"
        data["version"] = self.version
        return data
        
    def downgrade(self, data):
        """Remove new_field from all records."""
        for record in data.get("statistics", []):
            record.pop("new_field", None)
        data["version"] = "1.0.0"
        return data
        
    def validate(self, data):
        return isinstance(data, dict)

class TestIncrementalExporter(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        self.export_dir = os.path.join(self.temp_dir, "exports")
        self.migrations_dir = os.path.join(self.temp_dir, "migrations")
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.exporter = StatisticsExporter(self.store)
        self.incremental = IncrementalExporter(
            self.store,
            self.exporter,
            self.export_dir,
            compression_level=CompressionLevel.BALANCED,
            migrations_dir=self.migrations_dir
        )
        
        # Create initial data
        self._create_initial_data()
        
    def tearDown(self):
        # Clean up temporary files
        shutil.rmtree(self.temp_dir)
        
    def _create_initial_data(self):
        """Create initial test data."""
        base_time = datetime.now() - timedelta(days=1)
        
        for i in range(5):
            stats = IndexStats(
                index_name=f"index_{i}",
                table_name="test_table",
                index_type="btree",
                created_at=base_time,
                usage=IndexUsageStats(
                    total_reads=1000,
                    total_writes=500,
                    avg_read_time_ms=1.0,
                    avg_write_time_ms=2.0,
                    cache_hits=800,
                    cache_misses=200
                ),
                size=IndexSizeStats(
                    total_entries=10000,
                    depth=4,
                    size_bytes=102400,
                    fragmentation_ratio=0.1
                )
            )
            self.store.save_stats(stats)
            
    def _create_changes(self):
        """Create test changes."""
        # Add new index
        stats = IndexStats(
            index_name="new_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(),
            size=IndexSizeStats()
        )
        self.store.save_stats(stats)
        
        # Modify existing index
        stats = IndexStats(
            index_name="index_0",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=2000,  # Modified
                total_writes=1000  # Modified
            ),
            size=IndexSizeStats()
        )
        self.store.save_stats(stats)
        
    def test_base_export(self):
        # Create base export
        metadata = self.incremental.create_base_export()
        
        # Verify base export was created
        self.assertTrue(os.path.exists(os.path.join(self.export_dir, "base")))
        self.assertTrue(self.incremental.state_file.exists())
        
        # Verify metadata
        self.assertEqual(metadata.increment_count, 0)
        self.assertEqual(metadata.total_changes, 5)  # Initial records
        
        # Verify state file
        with open(self.incremental.state_file, 'r') as f:
            state = json.load(f)
            self.assertIn("base_export", state)
            self.assertEqual(len(state["increments"]), 0)
            
    def test_incremental_export(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Create changes
        self._create_changes()
        
        # Create increment
        metadata = self.incremental.export_increment()
        
        # Verify increment was created
        self.assertTrue(os.path.exists(os.path.join(self.export_dir, "increments")))
        
        # Verify metadata
        self.assertEqual(metadata.increment_count, 1)
        self.assertEqual(metadata.total_changes, 2)  # 1 new, 1 modified
        
        # Verify increment content
        increment_path = os.path.join(
            self.export_dir,
            "increments",
            "increment_0.json"
        )
        with open(increment_path, 'r') as f:
            data = json.load(f)
            self.assertIn("new_index", data["changes"]["added"])
            self.assertIn("index_0", data["changes"]["modified"])
            
    def test_rebuild_export(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Create and export changes
        self._create_changes()
        self.incremental.export_increment()
        
        # Rebuild full export
        output_path = os.path.join(self.temp_dir, "full_export.json")
        metadata = self.incremental.rebuild_full_export(output_path)
        
        # Verify rebuilt export
        with open(output_path, 'r') as f:
            data = json.load(f)
            stats = data["statistics"]
            
            # Should include all records
            self.assertEqual(len(stats), 6)  # 5 original + 1 new
            
            # Should have updated data
            modified_stat = next(
                s for s in stats
                if s["index_name"] == "index_0"
            )
            self.assertEqual(modified_stat["usage"]["total_reads"], 2000)
            
    def test_integrity_verification(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Verify initial integrity
        self.assertTrue(self.incremental.verify_integrity())
        
        # Corrupt base export
        base_path = Path(self.incremental.state["base_export"]["path"])
        with open(base_path, 'w') as f:
            f.write("corrupted")
            
        # Verify integrity fails
        self.assertFalse(self.incremental.verify_integrity())
        
    def test_cleanup(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Create multiple increments
        for _ in range(3):
            self._create_changes()
            self.incremental.export_increment()
            
        # Set old timestamps
        old_time = datetime.now() - timedelta(days=31)
        self.incremental.state["increments"][0]["timestamp"] = old_time.isoformat()
        self.incremental._save_state()
        
        # Clean up old increments
        self.incremental.cleanup_old_increments(max_age_days=30, max_count=2)
        
        # Verify cleanup
        self.assertEqual(len(self.incremental.state["increments"]), 2)
        
    def test_change_detection(self):
        # Create base export
        self.incremental.create_base_export()
        base_time = datetime.now()
        
        # No changes
        changes = self.incremental._detect_changes(base_time)
        self.assertEqual(len(changes.added), 0)
        self.assertEqual(len(changes.modified), 0)
        self.assertEqual(len(changes.deleted), 0)
        
        # Create changes
        self._create_changes()
        
        # Detect changes
        changes = self.incremental._detect_changes(base_time)
        self.assertEqual(len(changes.added), 1)  # new_index
        self.assertEqual(len(changes.modified), 1)  # index_0
        self.assertEqual(len(changes.deleted), 0)
        
    def test_minimum_changes(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Create minor change
        stats = IndexStats(
            index_name="index_0",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=1001  # Minor change
            ),
            size=IndexSizeStats()
        )
        self.store.save_stats(stats)
        
        # Try to create increment with high minimum
        result = self.incremental.export_increment(min_changes=10)
        self.assertIsNone(result)  # Should not create increment
        
    def test_concurrent_exports(self):
        # Create base export
        self.incremental.create_base_export()
        
        # Create changes
        self._create_changes()
        
        # Export with different formats concurrently
        json_meta = self.incremental.export_increment(format=ExportFormat.JSON)
        yaml_meta = self.incremental.export_increment(format=ExportFormat.YAML)
        
        # Second export should be None (no new changes)
        self.assertIsNotNone(json_meta)
        self.assertIsNone(yaml_meta)
        
    def test_error_handling(self):
        # Try to export increment without base
        with self.assertRaises(ValueError):
            self.incremental.export_increment()
            
        # Try to rebuild without base
        with self.assertRaises(ValueError):
            self.incremental.rebuild_full_export("output.json")
            
        # Create base export
        self.incremental.create_base_export()
        
        # Corrupt state file
        with open(self.incremental.state_file, 'w') as f:
            f.write("corrupted")
            
        # Should handle corrupted state
        self.assertEqual(self.incremental._load_state(), {}) 
        
    def test_compression_settings(self):
        """Test different compression settings."""
        # Test with different compression levels
        for level in CompressionLevel:
            exporter = IncrementalExporter(
                self.store,
                self.exporter,
                os.path.join(self.temp_dir, f"export_{level.value}"),
                compression_level=level
            )
            
            metadata = exporter.create_base_export()
            self.assertIn("compression_info", metadata.__dict__)
            self.assertGreater(
                metadata.compression_info["compression_ratio"],
                1.0
            )
            
    def test_compression_disabled(self):
        """Test exports with compression disabled."""
        metadata = self.incremental.create_base_export(compress=False)
        self.assertEqual(
            metadata.compression_info["algorithm"],
            "none"
        )
        self.assertEqual(
            metadata.compression_info["compression_ratio"],
            1.0
        )
        
    def test_compressed_rebuild(self):
        """Test rebuilding from compressed exports."""
        # Create base export with compression
        self.incremental.create_base_export()
        
        # Create and export changes
        self._create_changes()
        self.incremental.export_increment()
        
        # Rebuild with different compression settings
        output_path = os.path.join(self.temp_dir, "rebuilt.json")
        metadata = self.incremental.rebuild_full_export(
            output_path,
            compress=True
        )
        
        # Verify the rebuilt file exists and is valid
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["statistics"]), 6)  # 5 original + 1 new
            
    def test_compression_error_handling(self):
        """Test handling of compression errors."""
        # Create corrupted compressed file
        base_path = os.path.join(self.export_dir, "base")
        os.makedirs(base_path, exist_ok=True)
        corrupted_file = os.path.join(base_path, "base.json.zst")
        with open(corrupted_file, 'wb') as f:
            f.write(b"corrupted data")
            
        self.incremental.state = {
            "base_export": {
                "path": corrupted_file,
                "metadata": {},
                "compression": {
                    "algorithm": "zst",
                    "compression_ratio": 2.0
                },
                "checksum": "dummy"
            },
            "increments": [],
            "last_export": datetime.now().isoformat()
        }
        self.incremental._save_state()
        
        # Attempt to rebuild from corrupted file
        output_path = os.path.join(self.temp_dir, "rebuilt.json")
        with self.assertRaises(Exception):
            self.incremental.rebuild_full_export(output_path)
            
    def test_large_export_compression(self):
        """Test compression of large exports."""
        # Create many records
        base_time = datetime.now() - timedelta(days=1)
        for i in range(1000):  # Create 1000 records
            stats = IndexStats(
                index_name=f"large_index_{i}",
                table_name="test_table",
                index_type="btree",
                created_at=base_time,
                usage=IndexUsageStats(
                    total_reads=1000,
                    total_writes=500,
                    avg_read_time_ms=1.0,
                    avg_write_time_ms=2.0,
                    cache_hits=800,
                    cache_misses=200
                ),
                size=IndexSizeStats(
                    total_entries=10000,
                    depth=4,
                    size_bytes=102400,
                    fragmentation_ratio=0.1
                )
            )
            self.store.save_stats(stats)
            
        # Create base export
        metadata = self.incremental.create_base_export()
        
        # Verify compression ratio for large dataset
        self.assertGreater(
            metadata.compression_info["compression_ratio"],
            2.0  # Expect good compression for repetitive data
        )
        
    def test_compression_metadata_persistence(self):
        """Test persistence of compression metadata."""
        # Create base export
        metadata = self.incremental.create_base_export()
        
        # Verify compression info is saved in state
        with open(self.incremental.state_file, 'r') as f:
            state = json.load(f)
            self.assertIn("compression", state["base_export"])
            self.assertEqual(
                state["base_export"]["compression"]["algorithm"],
                metadata.compression_info["algorithm"]
            )
            
        # Create increment
        self._create_changes()
        inc_metadata = self.incremental.export_increment()
        
        # Verify increment compression info is saved
        with open(self.incremental.state_file, 'r') as f:
            state = json.load(f)
            self.assertIn("compression", state["increments"][0])
            self.assertEqual(
                state["increments"][0]["compression"]["algorithm"],
                inc_metadata.compression_info["algorithm"]
            )
        
    def test_migration_creation(self):
        """Test creating new migrations."""
        version = "1.1.0"
        description = "Test migration"
        
        file_path = self.incremental.create_migration(version, description)
        self.assertTrue(file_path.exists())
        
        # Verify migration info
        info = self.incremental.get_migration_info(version)
        self.assertIsNone(info)  # Not loaded yet
        
    def test_data_migration(self):
        """Test migrating data between versions."""
        # Create migration file
        migration_file = Path(self.migrations_dir) / "migration_1.1.0.py"
        migration_file.parent.mkdir(exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write('''
from typing import Dict, Any
from ...tests.test_incremental import TestMigration

class Migration(TestMigration):
    pass
''')
        
        # Create base export
        self.incremental.create_base_export(version="1.0.0")
        
        # Create changes
        self._create_changes()
        
        # Export with migration
        metadata = self.incremental.export_increment(
            target_version="1.1.0"
        )
        
        self.assertEqual(metadata.version, "1.1.0")
        
        # Verify migrated data
        increment_path = Path(metadata.path)
        with open(increment_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["version"], "1.1.0")
            for record in data["records"]:
                self.assertIn("new_field", record)
                
    def test_rebuild_with_migration(self):
        """Test rebuilding with data migration."""
        # Create migration file
        migration_file = Path(self.migrations_dir) / "migration_1.1.0.py"
        migration_file.parent.mkdir(exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write('''
from typing import Dict, Any
from ...tests.test_incremental import TestMigration

class Migration(TestMigration):
    pass
''')
        
        # Create base export
        self.incremental.create_base_export(version="1.0.0")
        
        # Create and export changes
        self._create_changes()
        self.incremental.export_increment()
        
        # Rebuild with migration
        output_path = os.path.join(self.temp_dir, "rebuilt.json")
        metadata = self.incremental.rebuild_full_export(
            output_path,
            target_version="1.1.0"
        )
        
        self.assertEqual(metadata.version, "1.1.0")
        
        # Verify migrated data
        with open(output_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["version"], "1.1.0")
            for record in data["statistics"]:
                self.assertIn("new_field", record)
                
    def test_migration_error_handling(self):
        """Test handling of migration errors."""
        # Create invalid migration file
        migration_file = Path(self.migrations_dir) / "migration_1.1.0.py"
        migration_file.parent.mkdir(exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write('''
from typing import Dict, Any
from ..migration import Migration

class Migration(Migration):
    def __init__(self):
        super().__init__("1.1.0", "Error migration")
        
    def upgrade(self, data):
        raise ValueError("Test error")
        
    def downgrade(self, data):
        return data
        
    def validate(self, data):
        return True
''')
        
        # Create base export
        self.incremental.create_base_export(version="1.0.0")
        
        # Attempt migration
        with self.assertRaises(ValueError):
            self.incremental.export_increment(target_version="1.1.0")
            
    def test_backward_compatibility(self):
        """Test backward compatibility of migrations."""
        # Create base export with newer version
        metadata = self.incremental.create_base_export(version="1.1.0")
        self.assertEqual(metadata.version, "1.1.0")
        
        # Create migration file
        migration_file = Path(self.migrations_dir) / "migration_1.1.0.py"
        migration_file.parent.mkdir(exist_ok=True)
        
        with open(migration_file, 'w') as f:
            f.write('''
from typing import Dict, Any
from ...tests.test_incremental import TestMigration

class Migration(TestMigration):
    pass
''')
        
        # Export increment with downgrade
        self._create_changes()
        metadata = self.incremental.export_increment(
            target_version="1.0.0"
        )
        
        self.assertEqual(metadata.version, "1.0.0")
        
        # Verify downgraded data
        increment_path = Path(metadata.path)
        with open(increment_path, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["version"], "1.0.0")
            for record in data["records"]:
                self.assertNotIn("new_field", record)