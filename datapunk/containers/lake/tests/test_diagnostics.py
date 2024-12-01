import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch, MagicMock
import psutil

from ..src.storage.index.diagnostics import (
    DiagnosticsManager,
    MetricType,
    AlertLevel,
    HealthStatus,
    PerformanceMetrics,
    Alert
)
from ..src.storage.index.distributed import (
    DistributedManager,
    Node,
    NodeState
)
from ..src.storage.index.sharding import (
    ShardManager,
    ShardState,
    ShardInfo
)
from ..src.storage.index.consensus import (
    RaftConsensus,
    NodeRole,
    ConsensusState
)
from ..src.storage.index.stats import StatisticsStore
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.monitor import IndexMonitor
from ..src.storage.index.security import SecurityManager

class TestDiagnosticsSystem(unittest.TestCase):
    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "diagnostics_config.json"
        
        # Create test configuration
        config = {
            "metrics": {
                "collection_interval_seconds": 1,
                "history_size": 100,
                "aggregation_window_minutes": 1
            },
            "health": {
                "check_interval_seconds": 1,
                "cpu_threshold_percent": 80,
                "memory_threshold_percent": 85,
                "disk_threshold_percent": 90,
                "max_error_rate": 0.01
            },
            "alerts": {
                "max_alerts": 100,
                "alert_retention_days": 1,
                "throttle_interval_seconds": 60
            },
            "tracing": {
                "enabled": True,
                "sample_rate": 1.0,
                "max_spans": 100
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        # Initialize components
        self.store = StatisticsStore(Path(self.temp_dir) / "test.db")
        self.manager = IndexManager(self.store)
        self.monitor = IndexMonitor(
            self.store,
            self.manager,
            None,  # No optimizer needed
            None   # No config needed
        )
        self.security = SecurityManager(None)  # No config needed
        
        # Initialize distributed manager with mock nodes
        self.distributed = DistributedManager(
            self.store,
            self.manager,
            self.monitor,
            self.security,
            None,  # No config needed
            "node1"
        )
        
        # Add test nodes
        self.distributed.nodes.update({
            "node1": Node(
                node_id="node1",
                role=NodeRole.PRIMARY,
                host="localhost",
                port=8001,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes=set(),
                version="1.0.0"
            ),
            "node2": Node(
                node_id="node2",
                role=NodeRole.REPLICA,
                host="localhost",
                port=8002,
                state=NodeState.ACTIVE,
                last_heartbeat=datetime.now(),
                indexes=set(),
                version="1.0.0"
            )
        })
        
        # Initialize sharding manager with test shards
        self.sharding = ShardManager(
            self.distributed,
            None  # No config needed
        )
        
        # Add test shards
        self.sharding.shards.update({
            "shard1": ShardInfo(
                shard_id="shard1",
                index_name="test_index",
                key_range=(0, 100),
                node_id="node1",
                state=ShardState.ACTIVE,
                size_bytes=1024 * 1024,  # 1MB
                record_count=1000,
                created_at=datetime.now(),
                last_modified=datetime.now()
            ),
            "shard2": ShardInfo(
                shard_id="shard2",
                index_name="test_index",
                key_range=(100, 200),
                node_id="node2",
                state=ShardState.ACTIVE,
                size_bytes=2 * 1024 * 1024,  # 2MB
                record_count=2000,
                created_at=datetime.now(),
                last_modified=datetime.now()
            )
        })
        
        # Initialize consensus with test state
        self.consensus = RaftConsensus(
            self.distributed,
            self.monitor,
            None,  # No config needed
            "node1"
        )
        
        # Initialize diagnostics manager
        self.diagnostics = DiagnosticsManager(
            self.distributed,
            self.sharding,
            self.consensus,
            self.monitor,
            self.config_path
        )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    async def test_health_checks(self, mock_disk, mock_memory, mock_cpu):
        """Test health status checks."""
        # Mock system metrics
        mock_cpu.return_value = 90.0  # High CPU
        mock_memory.return_value = MagicMock(percent=50.0)  # Normal memory
        mock_disk.return_value = MagicMock(percent=95.0)  # High disk
        
        # Run health check
        status = self.diagnostics._check_node_health()
        
        # Verify status
        self.assertEqual(status.node_id, "node1")
        self.assertEqual(status.cpu_percent, 90.0)
        self.assertEqual(status.memory_percent, 50.0)
        self.assertEqual(status.disk_usage_percent, 95.0)
        
        # Verify alerts generated
        cpu_alerts = [
            a for a in self.diagnostics.alerts
            if "CPU" in a.message
        ]
        disk_alerts = [
            a for a in self.diagnostics.alerts
            if "disk" in a.message
        ]
        
        self.assertTrue(cpu_alerts)
        self.assertTrue(disk_alerts)
        self.assertEqual(cpu_alerts[0].level, AlertLevel.WARNING)
        self.assertEqual(disk_alerts[0].level, AlertLevel.ERROR)
        
    async def test_metrics_collection(self):
        """Test metrics collection."""
        # Collect metrics
        self.diagnostics._collect_distributed_metrics()
        self.diagnostics._collect_sharding_metrics()
        self.diagnostics._collect_consensus_metrics()
        
        # Verify metrics recorded
        self.assertIn("distributed.active_nodes", self.diagnostics.metrics)
        self.assertIn("sharding.total_shards", self.diagnostics.metrics)
        self.assertIn("consensus.term", self.diagnostics.metrics)
        
        # Verify metric values
        self.assertEqual(
            self.diagnostics.metrics["distributed.active_nodes"][-1][1],
            2  # Two active nodes
        )
        self.assertEqual(
            self.diagnostics.metrics["sharding.total_shards"][-1][1],
            2  # Two shards
        )
        
    def test_shard_balance(self):
        """Test shard balance calculation."""
        balance = self.diagnostics._calculate_shard_balance()
        
        # With current setup (1MB and 2MB shards)
        # Standard deviation = 0.5MB, mean = 1.5MB
        # CV = 0.33, score = 0.67
        self.assertAlmostEqual(balance, 0.67, places=2)
        
    async def test_performance_metrics(self):
        """Test performance metrics calculation."""
        # Add some operation timings
        self.diagnostics.operation_timings["op1"] = [10.0, 20.0, 30.0]
        self.diagnostics.operation_timings["op2"] = [15.0, 25.0, 35.0]
        
        # Get performance metrics
        metrics = self.diagnostics.get_performance_metrics()
        
        # Verify metrics
        self.assertAlmostEqual(metrics.operation_latency_ms, 22.5)  # Average
        self.assertGreaterEqual(metrics.throughput_ops, 0)
        self.assertEqual(metrics.error_rate, 0.0)
        self.assertGreaterEqual(metrics.shard_balance_score, 0)
        
    def test_alert_management(self):
        """Test alert creation and management."""
        # Create some alerts
        for i in range(5):
            self.diagnostics.create_alert(
                AlertLevel.WARNING,
                "test",
                f"Test alert {i}",
                {"value": i}
            )
            
        # Verify alerts created
        self.assertEqual(len(self.diagnostics.alerts), 5)
        
        # Verify alert properties
        alert = self.diagnostics.alerts[0]
        self.assertEqual(alert.level, AlertLevel.WARNING)
        self.assertEqual(alert.source, "test")
        self.assertIn("Test alert", alert.message)
        
        # Test alert cleanup
        old_alert = Alert(
            alert_id="old",
            level=AlertLevel.INFO,
            source="test",
            message="Old alert",
            timestamp=datetime.now() - timedelta(days=2),
            metrics={},
            context={}
        )
        self.diagnostics.alerts.append(old_alert)
        
        # Run cleanup
        asyncio.run(self.diagnostics._cleanup_old_data())
        
        # Verify old alert removed
        self.assertNotIn(old_alert, self.diagnostics.alerts)
        
    def test_metric_retention(self):
        """Test metric retention management."""
        # Add metrics
        for i in range(200):  # More than history_size
            self.diagnostics.metrics["test"].append(
                (datetime.now(), i)
            )
            
        # Verify size limited
        self.assertEqual(
            len(self.diagnostics.metrics["test"]),
            self.diagnostics.config["metrics"]["history_size"]
        )
        
        # Verify oldest metrics removed
        values = [v for _, v in self.diagnostics.metrics["test"]]
        self.assertGreater(min(values), 0)
        
    @patch('psutil.Process')
    def test_system_metrics(self, mock_process):
        """Test system metrics collection."""
        # Mock process metrics
        mock_process.return_value.open_files.return_value = ["file1", "file2"]
        mock_process.return_value.threads.return_value = ["thread1", "thread2"]
        
        # Collect metrics
        self.diagnostics._collect_system_metrics()
        
        # Verify metrics collected
        self.assertIn("system.open_files", self.diagnostics.metrics)
        self.assertIn("system.thread_count", self.diagnostics.metrics)
        
        # Verify values
        self.assertEqual(
            self.diagnostics.metrics["system.open_files"][-1][1],
            2
        )
        self.assertEqual(
            self.diagnostics.metrics["system.thread_count"][-1][1],
            2
        ) 