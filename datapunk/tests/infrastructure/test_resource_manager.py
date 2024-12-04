import unittest
import time
from unittest.mock import patch, MagicMock
from datapunk.lib.resource.resource_manager import ResourceManager, ResourceThresholds, ResourceMetrics

class TestResourceManager(unittest.TestCase):
    def setUp(self):
        self.resource_manager = ResourceManager(
            thresholds=ResourceThresholds(
                cpu_threshold=0.8,
                memory_threshold=0.85,
                io_concurrency=200
            ),
            monitoring_interval=1
        )

    def tearDown(self):
        if self.resource_manager.running:
            self.resource_manager.stop_monitoring()

    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_io_counters')
    def test_collect_metrics(self, mock_io, mock_memory, mock_cpu):
        # Setup mocks
        mock_cpu.return_value = 75.0  # 75% CPU usage
        mock_memory.return_value = MagicMock(percent=80.0)  # 80% memory usage
        mock_io.return_value = MagicMock(read_time=100, write_time=200)

        # Collect metrics
        metrics = self.resource_manager._collect_metrics()

        # Verify metrics
        self.assertEqual(metrics.cpu_usage, 0.75)
        self.assertEqual(metrics.memory_usage, 0.8)
        self.assertEqual(metrics.io_wait, 300)

    def test_detect_spike(self):
        # Prepare test data
        normal_metrics = ResourceMetrics(
            cpu_usage=0.5,
            memory_usage=0.6,
            io_wait=100,
            timestamp=time.time()
        )

        spike_metrics = ResourceMetrics(
            cpu_usage=0.9,
            memory_usage=0.6,
            io_wait=100,
            timestamp=time.time()
        )

        # Add normal metrics history
        for i in range(10):
            self.resource_manager._store_metrics(normal_metrics)

        # Test no spike detection
        self.assertFalse(self.resource_manager._detect_spike(normal_metrics))

        # Test spike detection
        self.assertTrue(self.resource_manager._detect_spike(spike_metrics))

    def test_resource_allocation(self):
        with patch.object(self.resource_manager, '_collect_metrics') as mock_collect:
            mock_collect.return_value = ResourceMetrics(
                cpu_usage=0.5,
                memory_usage=0.6,
                io_wait=100,
                timestamp=time.time()
            )

            allocation = self.resource_manager.get_resource_allocation()
            
            self.assertIn('cpu_allocation', allocation)
            self.assertIn('memory_allocation', allocation)
            self.assertIn('io_concurrency', allocation)
            
            # Test allocation calculations
            self.assertAlmostEqual(allocation['cpu_allocation'], 0.4)  # (1 - 0.5) * 0.8
            self.assertAlmostEqual(allocation['memory_allocation'], 0.32)  # (1 - 0.6) * 0.8
            self.assertEqual(allocation['io_concurrency'], 200)

    def test_metrics_summary(self):
        # Add test metrics
        test_metrics = [
            ResourceMetrics(cpu_usage=0.5, memory_usage=0.6, io_wait=100, timestamp=time.time()),
            ResourceMetrics(cpu_usage=0.7, memory_usage=0.8, io_wait=200, timestamp=time.time())
        ]

        for metric in test_metrics:
            self.resource_manager._store_metrics(metric)

        summary = self.resource_manager.get_metrics_summary()

        self.assertIn('avg_cpu_usage', summary)
        self.assertIn('avg_memory_usage', summary)
        self.assertIn('peak_cpu_usage', summary)
        self.assertIn('peak_memory_usage', summary)

        self.assertAlmostEqual(summary['avg_cpu_usage'], 0.6)
        self.assertAlmostEqual(summary['avg_memory_usage'], 0.7)
        self.assertAlmostEqual(summary['peak_cpu_usage'], 0.7)
        self.assertAlmostEqual(summary['peak_memory_usage'], 0.8)

    def test_threshold_adjustment(self):
        new_thresholds = ResourceThresholds(
            cpu_threshold=0.9,
            memory_threshold=0.95,
            io_concurrency=300
        )

        self.resource_manager.adjust_thresholds(new_thresholds)

        self.assertEqual(self.resource_manager.thresholds.cpu_threshold, 0.9)
        self.assertEqual(self.resource_manager.thresholds.memory_threshold, 0.95)
        self.assertEqual(self.resource_manager.thresholds.io_concurrency, 300)

if __name__ == '__main__':
    unittest.main() 