import unittest
from unittest.mock import Mock, patch
import threading
import time
from typing import Dict, Any

from ..src.storage.index.manager import IndexManager, IndexCreationRequest
from ..src.storage.index.core import IndexType, IndexStats, Index
from datetime import datetime

class TestIndexManager(unittest.TestCase):
    def setUp(self):
        self.manager = IndexManager(
            max_workers=2,
            enable_auto_maintenance=True,
            enable_advisor=True
        )
        
    def tearDown(self):
        self.manager.cleanup()
        
    def test_create_index(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        
        index = self.manager.create_index(request)
        
        self.assertIsNotNone(index)
        self.assertEqual(index.name, "test_index")
        self.assertEqual(index.table_name, "test_table")
        self.assertEqual(len(self.manager.indexes), 1)
        
        # Test duplicate creation
        with self.assertRaises(ValueError):
            self.manager.create_index(request)
            
        # Test invalid index type
        invalid_request = IndexCreationRequest(
            name="invalid_index",
            table_name="test_table",
            columns=["id"],
            index_type="invalid_type"
        )
        with self.assertRaises(ValueError):
            self.manager.create_index(invalid_request)
            
    def test_drop_index(self):
        # Create an index first
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.HASH
        )
        self.manager.create_index(request)
        
        # Test successful drop
        self.assertTrue(self.manager.drop_index("test_index"))
        self.assertEqual(len(self.manager.indexes), 0)
        
        # Test dropping non-existent index
        self.assertFalse(self.manager.drop_index("nonexistent"))
        
    def test_list_indexes(self):
        # Create multiple indexes
        requests = [
            IndexCreationRequest(
                name=f"index_{i}",
                table_name=f"table_{i//2}",  # Two indexes per table
                columns=["id"],
                index_type=IndexType.BTREE
            )
            for i in range(4)
        ]
        
        for request in requests:
            self.manager.create_index(request)
            
        # Test listing all indexes
        all_indexes = self.manager.list_indexes()
        self.assertEqual(len(all_indexes), 4)
        
        # Test listing indexes for specific table
        table_0_indexes = self.manager.list_indexes("table_0")
        self.assertEqual(len(table_0_indexes), 2)
        
    def test_rebuild_index(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        self.manager.create_index(request)
        
        # Test successful rebuild
        self.assertTrue(self.manager.rebuild_index("test_index"))
        
        # Test rebuilding non-existent index
        self.assertFalse(self.manager.rebuild_index("nonexistent"))
        
    def test_analyze_index_usage(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        self.manager.create_index(request)
        
        # Test analysis with advisor enabled
        analysis = self.manager.analyze_index_usage("test_table")
        self.assertIsInstance(analysis, dict)
        
        # Test analysis with advisor disabled
        self.manager.advisor = None
        with self.assertRaises(RuntimeError):
            self.manager.analyze_index_usage("test_table")
            
    def test_get_index_statistics(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        index = self.manager.create_index(request)
        
        # Test getting statistics for existing index
        stats = self.manager.get_index_statistics("test_index")
        self.assertIsInstance(stats, IndexStats)
        
        # Test getting statistics for non-existent index
        self.assertIsNone(self.manager.get_index_statistics("nonexistent"))
        
    def test_optimize_indexes(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        self.manager.create_index(request)
        
        # Mock advisor recommendations
        self.manager.advisor.get_recommendations = Mock(return_value=[
            {
                "action": "create",
                "params": {
                    "name": "new_index",
                    "table_name": "test_table",
                    "columns": ["name"],
                    "index_type": IndexType.HASH
                }
            },
            {
                "action": "drop",
                "index_name": "test_index"
            }
        ])
        
        # Test optimization
        changes = self.manager.optimize_indexes("test_table")
        self.assertEqual(len(changes), 2)
        self.assertEqual(len(self.manager.indexes), 1)
        self.assertIn("new_index", self.manager.indexes)
        
    def test_maintenance_thread(self):
        request = IndexCreationRequest(
            name="test_index",
            table_name="test_table",
            columns=["id"],
            index_type=IndexType.BTREE
        )
        index = self.manager.create_index(request)
        
        # Mock maintenance needs
        self.manager.maintenance.needs_maintenance = Mock(return_value=True)
        self.manager.maintenance.perform_maintenance = Mock()
        
        # Wait for maintenance cycle
        time.sleep(1)
        
        # Verify maintenance was attempted
        self.manager.maintenance.needs_maintenance.assert_called_with(index)
        
    def test_concurrent_operations(self):
        def create_indexes():
            for i in range(5):
                request = IndexCreationRequest(
                    name=f"index_{threading.get_ident()}_{i}",
                    table_name="test_table",
                    columns=["id"],
                    index_type=IndexType.BTREE
                )
                self.manager.create_index(request)
                
        # Create multiple threads
        threads = [
            threading.Thread(target=create_indexes)
            for _ in range(3)
        ]
        
        # Start all threads
        for thread in threads:
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Verify all indexes were created
        self.assertEqual(len(self.manager.indexes), 15)
        
    def test_cleanup(self):
        # Create some indexes
        for i in range(3):
            request = IndexCreationRequest(
                name=f"index_{i}",
                table_name="test_table",
                columns=["id"],
                index_type=IndexType.BTREE
            )
            self.manager.create_index(request)
            
        # Perform cleanup
        self.manager.cleanup()
        
        # Verify all indexes were cleaned up
        self.assertEqual(len(self.manager.indexes), 0)
        self.assertTrue(self.manager.executor._shutdown) 