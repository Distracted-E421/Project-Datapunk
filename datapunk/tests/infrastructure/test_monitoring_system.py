import unittest
import asyncio
from datetime import datetime, timedelta
from datapunk.lib.monitoring.monitoring_system import (
    MonitoringSystem,
    MetricDefinition,
    MetricType,
    AlertRule,
    AlertSeverity,
    Alert,
    HealthCheck,
    HealthStatus,
    AggregationMethod,
    MetricAggregation
)
import statistics
import numpy as np

class TestMonitoringSystem(unittest.TestCase):
    def setUp(self):
        self.monitoring = MonitoringSystem(
            retention_period=timedelta(hours=1),
            alert_check_interval=1.0,
            cleanup_interval=5.0
        )
        
        # Create test metric
        self.test_metric = MetricDefinition(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            labels={"service", "environment"}
        )
        self.monitoring.register_metric(self.test_metric)

    def tearDown(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.monitoring.stop())

    def test_metric_registration(self):
        """Test metric registration."""
        metric = MetricDefinition(
            name="cpu_usage",
            type=MetricType.GAUGE,
            description="CPU usage percentage",
            labels={"host", "service"},
            unit="percent"
        )
        self.monitoring.register_metric(metric)
        
        self.assertIn("cpu_usage", self.monitoring.metrics)
        self.assertEqual(self.monitoring.metrics["cpu_usage"].unit, "percent")

        # Test duplicate registration
        with self.assertRaises(ValueError):
            self.monitoring.register_metric(metric)

    def test_alert_rule_registration(self):
        """Test alert rule registration."""
        rule = AlertRule(
            name="high_cpu",
            metric_name="test_metric",
            condition="value > 90",
            severity=AlertSeverity.WARNING,
            duration=timedelta(minutes=5)
        )
        self.monitoring.register_alert_rule(rule)
        
        self.assertIn("high_cpu", self.monitoring.alert_rules)

        # Test duplicate registration
        with self.assertRaises(ValueError):
            self.monitoring.register_alert_rule(rule)

        # Test registration with non-existent metric
        invalid_rule = AlertRule(
            name="invalid_rule",
            metric_name="non_existent_metric",
            condition="value > 90",
            severity=AlertSeverity.WARNING,
            duration=timedelta(minutes=5)
        )
        with self.assertRaises(ValueError):
            self.monitoring.register_alert_rule(invalid_rule)

    def test_metric_recording(self):
        """Test metric value recording."""
        labels = {"service": "test", "environment": "prod"}
        
        # Record value
        self.monitoring.record_metric("test_metric", 42.0, labels)
        
        # Get values
        values = self.monitoring.get_metric_values("test_metric", labels=labels)
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0][1], 42.0)

        # Test missing labels
        with self.assertRaises(ValueError):
            self.monitoring.record_metric("test_metric", 42.0, {"service": "test"})

    def test_alert_evaluation(self):
        """Test alert evaluation."""
        # Create alert rule
        rule = AlertRule(
            name="test_alert",
            metric_name="test_metric",
            condition="value > 90",
            severity=AlertSeverity.WARNING,
            duration=timedelta(minutes=5)
        )
        self.monitoring.register_alert_rule(rule)

        # Record values that should trigger alert
        labels = {"service": "test", "environment": "prod"}
        self.monitoring.record_metric("test_metric", 95.0, labels)

        # Evaluate rule
        self.monitoring._evaluate_alert_rule(rule)
        
        # Check alert was created
        alerts = self.monitoring.get_active_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].rule.name, "test_alert")
        self.assertEqual(alerts[0].value, 95.0)

    def test_alert_resolution(self):
        """Test alert resolution."""
        # Create and trigger alert
        rule = AlertRule(
            name="test_alert",
            metric_name="test_metric",
            condition="value > 90",
            severity=AlertSeverity.WARNING,
            duration=timedelta(minutes=5)
        )
        self.monitoring.register_alert_rule(rule)
        
        labels = {"service": "test", "environment": "prod"}
        self.monitoring.record_metric("test_metric", 95.0, labels)
        self.monitoring._evaluate_alert_rule(rule)
        
        # Record value that should resolve alert
        self.monitoring.record_metric("test_metric", 85.0, labels)
        self.monitoring._evaluate_alert_rule(rule)
        
        # Check alert was resolved
        self.assertEqual(len(self.monitoring.get_active_alerts()), 0)

    def test_alert_callbacks(self):
        """Test alert notification callbacks."""
        received_alerts = []
        def alert_callback(alert: Alert):
            received_alerts.append(alert)

        self.monitoring.add_alert_callback(alert_callback)

        # Create and trigger alert
        rule = AlertRule(
            name="test_alert",
            metric_name="test_metric",
            condition="value > 90",
            severity=AlertSeverity.WARNING,
            duration=timedelta(minutes=5)
        )
        self.monitoring.register_alert_rule(rule)
        
        labels = {"service": "test", "environment": "prod"}
        self.monitoring.record_metric("test_metric", 95.0, labels)
        self.monitoring._evaluate_alert_rule(rule)
        
        # Check callback was called
        self.assertEqual(len(received_alerts), 1)
        self.assertEqual(received_alerts[0].rule.name, "test_alert")

    async def test_monitoring_lifecycle(self):
        """Test monitoring system start/stop."""
        # Start monitoring
        await self.monitoring.start()
        self.assertTrue(self.monitoring._running)
        self.assertEqual(len(self.monitoring._tasks), 2)
        
        # Stop monitoring
        await self.monitoring.stop()
        self.assertFalse(self.monitoring._running)
        self.assertEqual(len(self.monitoring._tasks), 0)

    def test_metrics_summary(self):
        """Test metrics summary generation."""
        labels = {"service": "test", "environment": "prod"}
        
        # Record some values
        self.monitoring.record_metric("test_metric", 42.0, labels)
        self.monitoring.record_metric("test_metric", 44.0, labels)
        self.monitoring.record_metric("test_metric", 46.0, labels)
        
        # Get summary
        summary = self.monitoring.get_metrics_summary()
        
        self.assertIn("test_metric", summary)
        metric_summary = summary["test_metric"]
        self.assertEqual(metric_summary["type"], "gauge")
        
        # Get values for our labels
        label_key = '{"environment": "prod", "service": "test"}'
        values = metric_summary["values"][label_key]
        
        self.assertEqual(values["current"], 46.0)
        self.assertEqual(values["min"], 42.0)
        self.assertEqual(values["max"], 46.0)
        self.assertAlmostEqual(values["avg"], 44.0)

    async def test_data_cleanup(self):
        """Test old data cleanup."""
        labels = {"service": "test", "environment": "prod"}
        
        # Record old data
        old_time = datetime.now() - timedelta(hours=2)
        self.monitoring.metric_values["test_metric"]["test_labels"].append(
            (old_time, 42.0)
        )
        
        # Record recent data
        self.monitoring.record_metric("test_metric", 44.0, labels)
        
        # Run cleanup
        await self.monitoring._cleanup_old_data()
        
        # Verify old data was removed
        values = self.monitoring.get_metric_values("test_metric")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0][1], 44.0)

    async def test_health_check_registration(self):
        """Test health check registration and execution."""
        # Create health check
        check_results = {'status': True}
        def test_check():
            return check_results['status']

        check = HealthCheck(
            name="test_check",
            check_function=test_check,
            interval=timedelta(seconds=1),
            timeout=1.0,
            description="Test health check"
        )
        
        # Register check
        self.monitoring.register_health_check(check)
        self.assertIn("test_check", self.monitoring.health_checks)
        
        # Test initial status
        status = self.monitoring.get_health_status(["test_check"])
        self.assertTrue(status["test_check"].status)
        
        # Test failed check
        check_results['status'] = False
        await self.monitoring._run_single_health_check("test_check", check)
        status = self.monitoring.get_health_status(["test_check"])
        self.assertFalse(status["test_check"].status)
        self.assertEqual(status["test_check"].consecutive_failures, 1)

    async def test_health_check_dependencies(self):
        """Test health check dependency handling."""
        def check_func():
            return True

        # Create dependent checks
        base_check = HealthCheck(
            name="base_check",
            check_function=check_func,
            interval=timedelta(seconds=1),
            timeout=1.0
        )
        
        dependent_check = HealthCheck(
            name="dependent_check",
            check_function=check_func,
            interval=timedelta(seconds=1),
            timeout=1.0,
            dependencies=["base_check"]
        )
        
        # Test dependency validation
        with self.assertRaises(ValueError):
            self.monitoring.register_health_check(dependent_check)
        
        # Register checks in correct order
        self.monitoring.register_health_check(base_check)
        self.monitoring.register_health_check(dependent_check)
        
        # Test dependency failure
        self.monitoring.health_status["base_check"] = HealthStatus(
            name="base_check",
            status=False,
            last_check=datetime.now(),
            last_success=None,
            last_failure=datetime.now(),
            consecutive_failures=1
        )
        
        await self.monitoring._run_single_health_check("dependent_check", dependent_check)
        status = self.monitoring.get_health_status(["dependent_check"])
        self.assertFalse(status["dependent_check"].status)
        self.assertIn("Dependency", status["dependent_check"].error_message)

    def test_metric_aggregation(self):
        """Test metric aggregation registration and computation."""
        # Register test metric
        metric = MetricDefinition(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            labels={"service"}
        )
        self.monitoring.register_metric(metric)
        
        # Create aggregation
        aggregation = MetricAggregation(
            name="test_aggregation",
            source_metric="test_metric",
            method=AggregationMethod.AVG,
            interval=timedelta(minutes=5),
            labels={"service": "test"}
        )
        
        # Register aggregation
        self.monitoring.register_aggregation(aggregation)
        self.assertIn("test_aggregation", self.monitoring.aggregations)
        
        # Record some values
        labels = {"service": "test"}
        self.monitoring.record_metric("test_metric", 10.0, labels)
        self.monitoring.record_metric("test_metric", 20.0, labels)
        self.monitoring.record_metric("test_metric", 30.0, labels)
        
        # Compute aggregation
        self.monitoring._compute_aggregation(aggregation, datetime.now())
        
        # Check results
        values = self.monitoring.get_aggregated_values("test_aggregation")
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0][1], 20.0)  # Average of 10, 20, 30

    def test_aggregation_methods(self):
        """Test different aggregation methods."""
        # Register test metric
        metric = MetricDefinition(
            name="test_metric",
            type=MetricType.GAUGE,
            description="Test metric",
            labels=set()
        )
        self.monitoring.register_metric(metric)
        
        # Record test values
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        for value in values:
            self.monitoring.record_metric("test_metric", value, {})
        
        # Test each aggregation method
        methods = {
            AggregationMethod.SUM: sum(values),
            AggregationMethod.AVG: statistics.mean(values),
            AggregationMethod.MIN: min(values),
            AggregationMethod.MAX: max(values),
            AggregationMethod.COUNT: len(values),
            AggregationMethod.P95: np.percentile(values, 95),
            AggregationMethod.P99: np.percentile(values, 99)
        }
        
        for method, expected in methods.items():
            aggregation = MetricAggregation(
                name=f"test_{method.value}",
                source_metric="test_metric",
                method=method,
                interval=timedelta(minutes=5)
            )
            
            self.monitoring.register_aggregation(aggregation)
            self.monitoring._compute_aggregation(aggregation, datetime.now())
            
            values = self.monitoring.get_aggregated_values(f"test_{method.value}")
            self.assertEqual(len(values), 1)
            self.assertAlmostEqual(values[0][1], expected, places=2)

    async def test_health_check_timeout(self):
        """Test health check timeout handling."""
        async def slow_check():
            await asyncio.sleep(2)
            return True

        check = HealthCheck(
            name="slow_check",
            check_function=slow_check,
            interval=timedelta(seconds=1),
            timeout=0.1
        )
        
        self.monitoring.register_health_check(check)
        await self.monitoring._run_single_health_check("slow_check", check)
        
        status = self.monitoring.get_health_status(["slow_check"])
        self.assertFalse(status["slow_check"].status)
        self.assertIn("timed out", status["slow_check"].error_message)

if __name__ == '__main__':
    unittest.main() 