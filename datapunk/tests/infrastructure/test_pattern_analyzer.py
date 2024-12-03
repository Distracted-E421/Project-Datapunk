import unittest
from datetime import datetime, timedelta
import tempfile
import os
import json
import numpy as np
from src.infrastructure.pattern_analyzer import (
    PatternAnalyzer,
    ServiceMetric,
    PatternType
)

class TestPatternAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PatternAnalyzer(
            window_size=timedelta(hours=1),
            min_confidence=0.8,
            anomaly_threshold=2.0
        )

    def test_periodic_pattern_detection(self):
        # Create periodic data
        base_time = datetime.now()
        for i in range(20):
            # Sine wave pattern
            value = np.sin(i * np.pi / 5) + 1
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="cpu_usage",
                value=value,
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        patterns = self.analyzer.get_recent_patterns(pattern_type=PatternType.PERIODIC)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0].pattern_type, PatternType.PERIODIC)

    def test_burst_pattern_detection(self):
        # Create normal data with a burst
        base_time = datetime.now()
        for i in range(15):
            value = 1.0
            if 5 <= i <= 9:  # Create burst
                value = 3.0
            
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="requests",
                value=value,
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        patterns = self.analyzer.get_recent_patterns(pattern_type=PatternType.BURST)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0].pattern_type, PatternType.BURST)

    def test_gradual_change_detection(self):
        # Create gradually increasing data
        base_time = datetime.now()
        for i in range(15):
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="memory_usage",
                value=float(i),  # Linear increase
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        patterns = self.analyzer.get_recent_patterns(pattern_type=PatternType.GRADUAL_INCREASE)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0].pattern_type, PatternType.GRADUAL_INCREASE)

    def test_anomaly_detection(self):
        # Create normal data with an anomaly
        base_time = datetime.now()
        for i in range(15):
            value = 1.0
            if i == 7:  # Create anomaly
                value = 5.0
            
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="error_rate",
                value=value,
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        patterns = self.analyzer.get_recent_patterns(pattern_type=PatternType.ANOMALY)
        self.assertTrue(len(patterns) > 0)
        self.assertEqual(patterns[0].pattern_type, PatternType.ANOMALY)

    def test_pattern_summary(self):
        # Add metrics for different pattern types
        base_time = datetime.now()
        
        # Add periodic pattern
        for i in range(20):
            value = np.sin(i * np.pi / 5) + 1
            metric = ServiceMetric(
                service_name="service1",
                metric_name="metric1",
                value=value,
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        # Add burst pattern
        for i in range(15):
            value = 1.0 if i < 5 or i > 9 else 3.0
            metric = ServiceMetric(
                service_name="service2",
                metric_name="metric2",
                value=value,
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        summary = self.analyzer.get_pattern_summary()
        self.assertIn('total_patterns', summary)
        self.assertIn('pattern_types', summary)
        self.assertIn('unique_services', summary)
        self.assertTrue(summary['total_patterns'] > 0)
        self.assertTrue(len(summary['pattern_types']) > 0)
        self.assertEqual(summary['unique_services'], 2)

    def test_pattern_export(self):
        # Add some test patterns
        base_time = datetime.now()
        for i in range(10):
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="test_metric",
                value=float(i),
                timestamp=base_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        # Export patterns to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            self.analyzer.export_patterns(tmp.name)
            
            # Read and verify exported data
            with open(tmp.name, 'r') as f:
                exported_data = json.load(f)
                
            self.assertTrue(isinstance(exported_data, list))
            if len(exported_data) > 0:
                pattern = exported_data[0]
                self.assertIn('type', pattern)
                self.assertIn('confidence', pattern)
                self.assertIn('start_time', pattern)
                self.assertIn('end_time', pattern)
                self.assertIn('affected_services', pattern)
                self.assertIn('description', pattern)
            
            # Cleanup
            os.unlink(tmp.name)

    def test_metric_cleanup(self):
        # Add old metrics
        old_time = datetime.now() - timedelta(hours=2)
        for i in range(5):
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="test_metric",
                value=1.0,
                timestamp=old_time + timedelta(minutes=i)
            )
            self.analyzer.metrics_history.append(metric)

        # Add recent metrics
        recent_time = datetime.now() - timedelta(minutes=30)
        for i in range(5):
            metric = ServiceMetric(
                service_name="test_service",
                metric_name="test_metric",
                value=1.0,
                timestamp=recent_time + timedelta(minutes=i)
            )
            self.analyzer.add_metric(metric)

        # Verify old metrics are cleaned up
        all_timestamps = [m.timestamp for m in self.analyzer.metrics_history]
        for timestamp in all_timestamps:
            self.assertTrue(
                datetime.now() - timestamp <= self.analyzer.window_size
            )

if __name__ == '__main__':
    unittest.main() 