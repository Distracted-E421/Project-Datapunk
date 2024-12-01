import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime
import time

from ..src.storage.index.migration import (
    Migration,
    MigrationManager,
    MigrationInfo,
    MigrationEvent,
    MigrationHistory
)

class TestMigration(Migration):
    """Test migration implementation."""
    
    def __init__(self, version: str, description: str):
        super().__init__(version, description)
        self.changes = [
            f"Change 1 for {version}",
            f"Change 2 for {version}"
        ]
        
    def upgrade(self, data):
        data["upgraded"] = True
        data["version"] = self.version
        return data
        
    def downgrade(self, data):
        data["upgraded"] = False
        data["version"] = self.version
        return data

class DependentMigration(TestMigration):
    """Test migration with dependencies."""
    
    def __init__(self, version: str, description: str, dependencies: list):
        super().__init__(version, description)
        self.dependencies = dependencies

class SchemaValidatedMigration(TestMigration):
    """Test migration with schema validation."""
    
    def __init__(self, version: str, description: str):
        super().__init__(version, description)
        self.schema = {
            "type": "object",
            "properties": {
                "version": {"type": "string"},
                "content": {"type": "string"},
                "upgraded": {"type": "boolean"}
            },
            "required": ["version", "content"]
        }

class TestMigrationSystem(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.migrations_dir = Path(self.temp_dir) / "migrations"
        self.migrations_dir.mkdir()
        self.history_file = self.migrations_dir / "history.json"
        self.manager = MigrationManager(
            self.migrations_dir,
            history_file=self.history_file
        )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_migration_file(
        self,
        version: str,
        migration_class: str = "TestMigration",
        dependencies: List[str] = None
    ):
        """Create a test migration file."""
        deps = f", dependencies={dependencies}" if dependencies else ""
        
        content = f'''
from typing import Dict, Any
from ...tests.test_migration import {migration_class}

class Migration({migration_class}):
    def __init__(self):
        super().__init__(
            version="{version}",
            description="Test migration {version}"{deps}
        )
'''
        
        file_path = self.migrations_dir / f"migration_{version}.py"
        with open(file_path, 'w') as f:
            f.write(content)
            
        return file_path
        
    def test_migration_hooks(self):
        """Test migration lifecycle hooks."""
        version = "1.0.1"
        self._create_migration_file(version)
        self.manager._load_migrations()
        
        # Track hook calls
        hook_calls = []
        def hook_callback(data):
            hook_calls.append(data.get("version"))
            
        # Register hooks
        migration = self.manager.migrations[version]
        for event in MigrationEvent:
            migration.add_hook(event, hook_callback)
            
        # Perform migration
        data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(data, version)
        
        # Verify hooks were called
        self.assertEqual(len(hook_calls), 4)  # validation + upgrade hooks
        
    def test_migration_history(self):
        """Test migration history tracking."""
        # Create migrations
        versions = ["1.0.1", "1.0.2"]
        for version in versions:
            self._create_migration_file(version)
        self.manager._load_migrations()
        
        # Perform migrations
        data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(data, "1.0.2")
        
        # Verify history
        history = self.manager.get_migration_history()
        self.assertEqual(len(history), 2)
        
        # Verify history file
        self.assertTrue(self.history_file.exists())
        with open(self.history_file, 'r') as f:
            history_data = json.load(f)
            self.assertEqual(len(history_data), 2)
            
        # Test filtering
        filtered = self.manager.get_migration_history(version="1.0.1")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].version, "1.0.1")
        
        # Test limiting
        limited = self.manager.get_migration_history(limit=1)
        self.assertEqual(len(limited), 1)
        self.assertEqual(limited[0].version, "1.0.2")
        
    def test_dry_run(self):
        """Test dry run migration."""
        version = "1.0.1"
        self._create_migration_file(version)
        self.manager._load_migrations()
        
        # Original data
        data = {"version": "1.0.0", "content": "test"}
        original = data.copy()
        
        # Perform dry run
        result = self.manager.dry_run(data, version)
        
        # Verify original data unchanged
        self.assertEqual(data, original)
        
        # Verify simulated changes
        self.assertEqual(result["version"], version)
        self.assertTrue(result["upgraded"])
        
        # Verify no history recorded
        self.assertEqual(len(self.manager.get_migration_history()), 0)
        
    def test_schema_validation(self):
        """Test schema validation during migration."""
        version = "1.0.1"
        self._create_migration_file(version, "SchemaValidatedMigration")
        self.manager._load_migrations()
        
        # Valid data
        valid_data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(valid_data, version)
        
        # Invalid data
        invalid_data = {"version": "1.0.0"}  # Missing required content
        with self.assertRaises(ValueError):
            self.manager.migrate(invalid_data, version)
            
    def test_dependencies(self):
        """Test migration dependencies."""
        # Create dependent migrations
        self._create_migration_file("1.0.1")
        self._create_migration_file(
            "1.1.0",
            "DependentMigration",
            dependencies=["1.0.1"]
        )
        self.manager._load_migrations()
        
        # Test valid dependency chain
        data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(data, "1.1.0")
        
        # Test missing dependency
        self._create_migration_file(
            "1.2.0",
            "DependentMigration",
            dependencies=["missing_version"]
        )
        self.manager._load_migrations()
        
        with self.assertRaises(ValueError):
            self.manager.migrate(data, "1.2.0")
            
    def test_global_hooks(self):
        """Test global migration hooks."""
        versions = ["1.0.1", "1.0.2"]
        for version in versions:
            self._create_migration_file(version)
        self.manager._load_migrations()
        
        # Track hook calls
        hook_calls = []
        def global_hook(data):
            hook_calls.append(data.get("version"))
            
        # Register global hook
        self.manager.register_global_hook(
            MigrationEvent.AFTER_UPGRADE,
            global_hook
        )
        
        # Perform migration
        data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(data, "1.0.2")
        
        # Verify hook calls
        self.assertEqual(len(hook_calls), 2)
        
    def test_error_handling(self):
        """Test error handling and history recording."""
        # Create migration that raises error
        content = '''
from typing import Dict, Any
from ..migration import Migration

class Migration(Migration):
    def __init__(self):
        super().__init__("1.0.1", "Error migration")
        
    def upgrade(self, data):
        raise ValueError("Test error")
        
    def downgrade(self, data):
        return data
        
    def validate(self, data):
        return True
'''
        
        file_path = self.migrations_dir / "migration_1.0.1.py"
        with open(file_path, 'w') as f:
            f.write(content)
            
        self.manager._load_migrations()
        
        # Attempt migration
        data = {"version": "1.0.0", "content": "test"}
        with self.assertRaises(ValueError):
            self.manager.migrate(data, "1.0.1")
            
        # Verify error recorded in history
        history = self.manager.get_migration_history()
        self.assertEqual(len(history), 1)
        self.assertFalse(history[0].success)
        self.assertEqual(history[0].error, "Test error")
        
    def test_performance_tracking(self):
        """Test migration performance tracking."""
        version = "1.0.1"
        self._create_migration_file(version)
        self.manager._load_migrations()
        
        # Add delay to migration
        migration = self.manager.migrations[version]
        original_upgrade = migration.upgrade
        def slow_upgrade(data):
            time.sleep(0.1)  # 100ms delay
            return original_upgrade(data)
        migration.upgrade = slow_upgrade
        
        # Perform migration
        data = {"version": "1.0.0", "content": "test"}
        self.manager.migrate(data, version)
        
        # Verify timing recorded
        history = self.manager.get_migration_history()
        self.assertEqual(len(history), 1)
        self.assertGreaterEqual(history[0].duration_ms, 100)