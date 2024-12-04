import unittest
from datetime import datetime, timedelta
import numpy as np
from datapunk.lib.resource.resource_predictor import (
    ResourcePredictor,
    ResourceMetrics,
    ResourcePrediction
)

class TestResourcePredictor(unittest.TestCase):
    def setUp(self):
        self.predictor = ResourcePredictor(
            history_window=24,
            forecast_window=12,
            confidence_threshold=0.8,
            update_interval=1
        )

    def _generate_test_metrics(self, hours: int, pattern: str = 'linear') -> None:
        """Generate test metrics with different patterns."""
        base_time = datetime.now() - timedelta(hours=hours)
        
        for hour in range(hours):
            if pattern == 'linear':
                value = hour * 0.1
            elif pattern == 'sine':
                value = np.sin(hour * np.pi / 12) * 0.5 + 0.5
            elif pattern == 'step':
                value = 0.3 if hour < hours/2 else 0.7
            else:
                value = 0.5

            metric = ResourceMetrics(
                timestamp=base_time + timedelta(hours=hour),
                cpu_usage=value,
                memory_usage=value + 0.1,
                disk_usage=value + 0.2,
                network_bandwidth=value + 0.3,
                request_count=int(value * 100)
            )
            self.predictor.add_metrics(metric)

    def test_model_training(self):
        """Test if models are properly trained with sufficient data."""
        self._generate_test_metrics(48, 'linear')
        
        # Check if models were created
        self.assertTrue(len(self.predictor.models) > 0)
        self.assertTrue(len(self.predictor.scalers) > 0)

    def test_resource_prediction(self):
        """Test resource usage prediction."""
        self._generate_test_metrics(48, 'linear')
        
        # Test prediction for each resource type
        resource_types = ['cpu', 'memory', 'disk', 'network', 'requests']
        hours_ahead = 6
        
        for resource_type in resource_types:
            predictions = self.predictor.predict_resource_usage(resource_type, hours_ahead)
            
            self.assertEqual(len(predictions), hours_ahead)
            for prediction in predictions:
                self.assertEqual(prediction.resource_type, resource_type)
                self.assertTrue(0 <= prediction.confidence <= 1)
                self.assertIsInstance(prediction.predicted_value, float)

    def test_capacity_planning(self):
        """Test capacity planning recommendations."""
        self._generate_test_metrics(48, 'linear')
        
        plan = self.predictor.get_capacity_plan()
        
        # Check plan structure
        self.assertIn('cpu', plan)
        self.assertIn('memory', plan)
        self.assertIn('disk', plan)
        self.assertIn('network', plan)
        self.assertIn('requests', plan)
        
        # Check plan details
        for resource_type, details in plan.items():
            self.assertIn('current_usage', details)
            self.assertIn('max_predicted', details)
            self.assertIn('avg_predicted', details)
            self.assertIn('confidence', details)
            self.assertIn('recommended_capacity', details)
            
            self.assertTrue(details['recommended_capacity'] >= details['max_predicted'])
            self.assertTrue(0 <= details['confidence'] <= 1)

    def test_prediction_with_different_patterns(self):
        """Test predictions with different resource usage patterns."""
        patterns = ['linear', 'sine', 'step']
        
        for pattern in patterns:
            self.predictor = ResourcePredictor()  # Reset predictor
            self._generate_test_metrics(48, pattern)
            
            predictions = self.predictor.predict_resource_usage('cpu', 6)
            self.assertTrue(len(predictions) > 0)
            
            # Verify predictions are within reasonable bounds
            for pred in predictions:
                self.assertTrue(0 <= pred.predicted_value <= 1)
                self.assertTrue(0 <= pred.confidence <= 1)

    def test_insufficient_history(self):
        """Test handling of insufficient history."""
        self._generate_test_metrics(6, 'linear')  # Less than forecast window
        
        with self.assertRaises(ValueError):
            self.predictor.predict_resource_usage('cpu', 6)

    def test_model_updates(self):
        """Test model updates based on update interval."""
        self._generate_test_metrics(48, 'linear')
        initial_update_time = self.predictor.last_update
        
        # Add more metrics within update interval
        self._generate_test_metrics(1, 'linear')
        self.assertEqual(initial_update_time, self.predictor.last_update)
        
        # Force update interval to pass
        self.predictor.last_update = datetime.now() - timedelta(hours=2)
        self._generate_test_metrics(1, 'linear')
        self.assertNotEqual(initial_update_time, self.predictor.last_update)

    def test_cleanup_old_metrics(self):
        """Test cleanup of old metrics."""
        # Add metrics for 48 hours
        self._generate_test_metrics(48, 'linear')
        
        # Verify only recent metrics are kept
        all_timestamps = [m.timestamp for m in self.predictor.metrics_history]
        oldest_allowed = datetime.now() - timedelta(hours=self.predictor.history_window)
        
        for timestamp in all_timestamps:
            self.assertTrue(timestamp >= oldest_allowed)

if __name__ == '__main__':
    unittest.main() 