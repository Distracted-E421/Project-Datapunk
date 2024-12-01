import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import time

from ..src.storage.index.backup import (
    BackupManager,
    BackupMetadata,
    RecoveryPoint
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.monitor import IndexMonitor

class TestBackupSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.backup_dir = Path(self.temp_dir) / "backups"
        self.db_path = Path(self.temp_dir) / "test.db"
        self.config_path = Path(self.temp_dir) / "backup_config.json"
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.manager = IndexManager(self.store)
        self.monitor = IndexMonitor(
            self.store,
            self.manager,
            None,  # No optimizer needed for tests
            None   # No config needed for monitor
        )
        
        # Create test configuration
        config = {
            "retention": {
                "full_backups_days": 7,
                "incremental_backups_days": 2,
                "recovery_points_count": 10
            },
            "scheduling": {
                "full_backup_interval_hours": 24,
                "incremental_backup_interval_minutes": 15
            },
            "performance": {
                "compression_level": 6,
                "max_concurrent_backups": 2,
                "chunk_size_mb": 32
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        # Initialize backup manager
        self.backup_manager = BackupManager(
            self.store,
            self.manager,
            self.monitor,
            self.backup_dir,
            self.config_path
        )
        
        # Create test index
        self.test_index_data = {
            "name": "test_index",
            "type": "btree",
            "entries": [
                {"key": "a", "value": 1},
                {"key": "b", "value": 2},
                {"key": "c", "value": 3}
            ]
        }
        self.manager.import_index("test_index", self.test_index_data)
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def test_full_backup_creation(self):
        """Test creating a full backup."""
        # Create backup
        backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Verify backup exists
        self.assertIn(backup_id, self.backup_manager.backup_metadata)
        metadata = self.backup_manager.backup_metadata[backup_id]
        
        self.assertEqual(metadata.index_name, "test_index")
        self.assertEqual(metadata.backup_type, "full")
        self.assertIsNone(metadata.parent_backup_id)
        
        # Verify backup file exists
        backup_path = (
            self.backup_dir / "full" / f"{backup_id}.backup"
        )
        self.assertTrue(backup_path.exists())
        
    def test_incremental_backup(self):
        """Test incremental backup creation."""
        # Create full backup first
        full_backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Modify index data
        modified_data = self.test_index_data.copy()
        modified_data["entries"].append({"key": "d", "value": 4})
        self.manager.import_index("test_index", modified_data)
        
        # Create incremental backup
        incr_backup_id = self.backup_manager.create_backup(
            "test_index",
            "incremental",
            async_backup=False
        )
        
        # Verify incremental backup
        metadata = self.backup_manager.backup_metadata[incr_backup_id]
        self.assertEqual(metadata.backup_type, "incremental")
        self.assertEqual(metadata.parent_backup_id, full_backup_id)
        
    def test_backup_restoration(self):
        """Test restoring from backup."""
        # Create initial backup
        backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Modify index data
        modified_data = self.test_index_data.copy()
        modified_data["entries"].append({"key": "d", "value": 4})
        self.manager.import_index("test_index", modified_data)
        
        # Restore from backup
        self.assertTrue(
            self.backup_manager.restore_backup(backup_id)
        )
        
        # Verify restored data
        restored_data = self.manager.export_index("test_index")
        self.assertEqual(
            len(restored_data["entries"]),
            len(self.test_index_data["entries"])
        )
        
    def test_recovery_points(self):
        """Test recovery point creation and restoration."""
        # Create recovery point
        transaction_id = "test_transaction"
        backup_id = self.backup_manager.create_recovery_point(
            transaction_id,
            {"test_index"}
        )
        
        # Modify data
        modified_data = self.test_index_data.copy()
        modified_data["entries"].append({"key": "d", "value": 4})
        self.manager.import_index("test_index", modified_data)
        
        # Restore to recovery point
        self.assertTrue(
            self.backup_manager.restore_to_point(transaction_id)
        )
        
        # Verify restored data
        restored_data = self.manager.export_index("test_index")
        self.assertEqual(
            len(restored_data["entries"]),
            len(self.test_index_data["entries"])
        )
        
    def test_backup_verification(self):
        """Test backup verification."""
        # Create backup
        backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Verify backup
        self.assertTrue(
            self.backup_manager.verify_backup(backup_id)
        )
        
        # Corrupt backup file
        backup_path = (
            self.backup_dir / "full" / f"{backup_id}.backup"
        )
        with open(backup_path, 'wb') as f:
            f.write(b"corrupted data")
            
        # Verify corrupted backup
        self.assertFalse(
            self.backup_manager.verify_backup(backup_id)
        )
        
    def test_backup_cleanup(self):
        """Test cleanup of old backups."""
        # Create old backup
        old_backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Modify timestamp to make it old
        metadata = self.backup_manager.backup_metadata[old_backup_id]
        metadata.timestamp = datetime.now() - timedelta(days=30)
        self.backup_manager._save_metadata(metadata)
        
        # Create new backup
        new_backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Run cleanup
        self.backup_manager.cleanup_old_backups()
        
        # Verify old backup removed
        self.assertNotIn(old_backup_id, self.backup_manager.backup_metadata)
        self.assertIn(new_backup_id, self.backup_manager.backup_metadata)
        
    def test_async_backup(self):
        """Test asynchronous backup creation."""
        # Create async backup
        backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=True
        )
        
        # Wait for backup to complete
        time.sleep(1)
        
        # Verify backup completed
        self.assertIn(backup_id, self.backup_manager.backup_metadata)
        
    def test_backup_to_different_name(self):
        """Test restoring backup to different index name."""
        # Create backup
        backup_id = self.backup_manager.create_backup(
            "test_index",
            "full",
            async_backup=False
        )
        
        # Restore to different name
        self.assertTrue(
            self.backup_manager.restore_backup(
                backup_id,
                "restored_index"
            )
        )
        
        # Verify restored data
        restored_data = self.manager.export_index("restored_index")
        self.assertEqual(
            len(restored_data["entries"]),
            len(self.test_index_data["entries"])
        )
        
    def test_recovery_point_limit(self):
        """Test recovery point count limitation."""
        # Create maximum number of recovery points
        max_points = self.backup_manager.config["retention"]["recovery_points_count"]
        
        for i in range(max_points + 5):
            self.backup_manager.create_recovery_point(
                f"transaction_{i}",
                {"test_index"}
            )
            
        # Verify only max points kept
        self.assertEqual(
            len(self.backup_manager.recovery_points),
            max_points
        )
        
        # Verify most recent points kept
        self.assertEqual(
            self.backup_manager.recovery_points[-1].transaction_id,
            f"transaction_{max_points + 4}"
        )