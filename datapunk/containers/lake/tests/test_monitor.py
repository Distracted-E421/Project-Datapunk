import unittest
import tempfile
import shutil
from pathlib import Path
import json
from datetime import datetime, timedelta

from ..src.storage.index.monitor import (
    IndexMonitor,
    IndexHealth,
    AlertSeverity,
    PerformanceMetrics,
    MaintenanceTask,
    IndexAlert
)
from ..src.storage.index.stats import (
    StatisticsStore,
    IndexStats,
    IndexUsageStats,
    IndexSizeStats
)
from ..src.storage.index.manager import IndexManager
from ..src.storage.index.optimizer import IndexOptimizer

class TestIndexMonitoring(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_stats.db"
        self.config_path = Path(self.temp_dir) / "monitor_config.json"
        
        # Initialize components
        self.store = StatisticsStore(self.db_path)
        self.manager = IndexManager(self.store)
        self.optimizer = IndexOptimizer(self.store)
        
        # Create test configuration
        config = {
            "metrics_retention_days": 7,
            "sampling_interval_seconds": 60,
            "alert_thresholds": {
                "latency_ms": 50,
                "throughput_qps": 100,
                "cache_hit_ratio": 0.7,
                "fragmentation_ratio": 0.2,
                "size_growth_ratio": 1.2
            },
            "health_thresholds": {
                "degraded": {
                    "latency_factor": 1.5,
                    "cache_hits": 0.6,
                    "fragmentation": 0.15
                },
                "critical": {
                    "latency_factor": 2.0,
                    "cache_hits": 0.4,
                    "fragmentation": 0.3
                }
            }
        }
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f)
            
        self.monitor = IndexMonitor(
            self.store,
            self.manager,
            self.optimizer,
            self.config_path
        )
        
        # Create test data
        self._create_test_data()
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        
    def _create_test_data(self):
        """Create test index statistics."""
        base_time = datetime.now() - timedelta(days=1)
        
        # Create healthy index stats
        healthy_stats = IndexStats(
            index_name="healthy_index",
            table_name="test_table",
            index_type="btree",
            created_at=base_time,
            usage=IndexUsageStats(
                total_reads=10000,
                total_writes=1000,
                avg_read_time_ms=10.0,
                avg_write_time_ms=5.0,
                cache_hits=8000,
                cache_misses=2000
            ),
            size=IndexSizeStats(
                total_entries=100000,
                depth=4,
                size_bytes=1024 * 1024,  # 1MB
                fragmentation_ratio=0.1
            )
        )
        
        # Create degraded index stats
        degraded_stats = IndexStats(
            index_name="degraded_index",
            table_name="test_table",
            index_type="btree",
            created_at=base_time,
            usage=IndexUsageStats(
                total_reads=5000,
                total_writes=2000,
                avg_read_time_ms=80.0,
                avg_write_time_ms=10.0,
                cache_hits=3000,
                cache_misses=2000
            ),
            size=IndexSizeStats(
                total_entries=100000,
                depth=5,
                size_bytes=2 * 1024 * 1024,  # 2MB
                fragmentation_ratio=0.25
            )
        )
        
        self.store.save_stats(healthy_stats)
        self.store.save_stats(degraded_stats)
        
    def test_metrics_collection(self):
        """Test metrics collection."""
        # Collect metrics
        self.monitor.collect_metrics("healthy_index")
        
        # Verify metrics recorded
        self.assertIn("healthy_index", self.monitor.metrics)
        metrics = self.monitor.metrics["healthy_index"][-1]
        
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertEqual(metrics.query_latency_ms, 10.0)
        self.assertGreater(metrics.throughput_qps, 0)
        self.assertEqual(metrics.cache_hit_ratio, 0.8)
        self.assertEqual(metrics.fragmentation_ratio, 0.1)
        
    def test_health_status(self):
        """Test health status updates."""
        # Check healthy index
        self.monitor.collect_metrics("healthy_index")
        self.assertEqual(
            self.monitor.health_status["healthy_index"],
            IndexHealth.HEALTHY
        )
        
        # Check degraded index
        self.monitor.collect_metrics("degraded_index")
        self.assertEqual(
            self.monitor.health_status["degraded_index"],
            IndexHealth.DEGRADED
        )
        
    def test_alert_generation(self):
        """Test alert generation."""
        # Collect metrics for degraded index
        self.monitor.collect_metrics("degraded_index")
        
        # Verify alerts generated
        alerts = [
            a for a in self.monitor.alerts
            if a.index_name == "degraded_index"
        ]
        
        self.assertGreater(len(alerts), 0)
        alert = alerts[0]
        
        self.assertIsInstance(alert, IndexAlert)
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertIsNotNone(alert.suggested_action)
        
    def test_maintenance_scheduling(self):
        """Test maintenance scheduling."""
        # Collect metrics for degraded index
        self.monitor.collect_metrics("degraded_index")
        
        # Verify maintenance tasks created
        tasks = [
            t for t in self.monitor.maintenance_tasks
            if t.index_name == "degraded_index"
        ]
        
        self.assertGreater(len(tasks), 0)
        task = tasks[0]
        
        self.assertIsInstance(task, MaintenanceTask)
        self.assertEqual(task.task_type, "REINDEX")
        self.assertIsNotNone(task.scheduled_time)
        self.assertIsNone(task.completed_time)
        
    def test_metrics_cleanup(self):
        """Test old metrics cleanup."""
        # Add old metrics
        old_time = datetime.now() - timedelta(days=10)
        old_metrics = PerformanceMetrics(
            query_latency_ms=10.0,
            throughput_qps=100.0,
            cache_hit_ratio=0.8,
            fragmentation_ratio=0.1,
            size_bytes=1024 * 1024,
            record_count=100000,
            last_updated=old_time
        )
        
        self.monitor.metrics["test_index"].append(old_metrics)
        
        # Add current metrics
        self.monitor.collect_metrics("test_index")
        
        # Verify old metrics removed
        metrics = self.monitor.metrics["test_index"]
        self.assertTrue(all(
            m.last_updated > datetime.now() - timedelta(
                days=self.monitor.config["metrics_retention_days"]
            )
            for m in metrics
        ))
        
    def test_health_report(self):
        """Test health report generation."""
        # Collect metrics
        self.monitor.collect_metrics("healthy_index")
        self.monitor.collect_metrics("degraded_index")
        
        # Get reports
        all_reports = self.monitor.get_health_report()
        single_report = self.monitor.get_health_report("healthy_index")
        
        # Verify all reports
        self.assertIn("healthy_index", all_reports)
        self.assertIn("degraded_index", all_reports)
        
        # Verify single report
        self.assertEqual(single_report["status"], "healthy")
        self.assertIn("metrics", single_report)
        self.assertIn("maintenance", single_report)
        self.assertIn("alerts", single_report)
        
    def test_performance_degradation(self):
        """Test performance degradation detection."""
        # Add baseline metrics
        baseline_metrics = PerformanceMetrics(
            query_latency_ms=10.0,
            throughput_qps=100.0,
            cache_hit_ratio=0.8,
            fragmentation_ratio=0.1,
            size_bytes=1024 * 1024,
            record_count=100000,
            last_updated=datetime.now() - timedelta(hours=1)
        )
        
        self.monitor.metrics["test_index"].append(baseline_metrics)
        
        # Add degraded metrics
        degraded_stats = IndexStats(
            index_name="test_index",
            table_name="test_table",
            index_type="btree",
            created_at=datetime.now(),
            usage=IndexUsageStats(
                total_reads=1000,
                total_writes=100,
                avg_read_time_ms=30.0,  # 3x baseline
                avg_write_time_ms=5.0,
                cache_hits=600,
                cache_misses=400
            ),
            size=IndexSizeStats(
                total_entries=100000,
                depth=4,
                size_bytes=1024 * 1024,
                fragmentation_ratio=0.1
            )
        )
        
        self.store.save_stats(degraded_stats)
        self.monitor.collect_metrics("test_index")
        
        # Verify degradation detected
        self.assertEqual(
            self.monitor.health_status["test_index"],
            IndexHealth.DEGRADED
        ) 