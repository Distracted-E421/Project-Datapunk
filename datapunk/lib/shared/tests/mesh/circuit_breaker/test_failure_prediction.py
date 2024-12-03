"""Tests for circuit breaker failure prediction"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import numpy as np
from datapunk_shared.mesh.circuit_breaker.failure_prediction import (
    PredictionMetric,
    PredictionWindow,
    MetricHistory,
    AnomalyDetector,
    TrendAnalyzer,
    FailurePredictor
)

@pytest.fixture
def mock_metrics():
    metrics = AsyncMock()
    metrics.increment = AsyncMock()
    metrics.gauge = AsyncMock()
    return metrics

@pytest.fixture
def prediction_window():
    return PredictionWindow(
        size_seconds=60,  # 1 minute
        resolution_seconds=5  # 5 second buckets
    )

@pytest.fixture
def metric_history(prediction_window):
    return MetricHistory(prediction_window)

@pytest.fixture
def failure_predictor(mock_metrics, prediction_window):
    return FailurePredictor(
        metrics_client=mock_metrics,
        window=prediction_window
    )

class TestPredictionWindow:
    def test_window_configuration(self):
        window = PredictionWindow(
            size_seconds=300,
            resolution_seconds=10
        )
        
        assert window.size_seconds == 300
        assert window.resolution_seconds == 10
        assert window.num_buckets == 30

class TestMetricHistory:
    def test_add_metric(self, metric_history):
        value = 1.0
        timestamp = datetime.utcnow()
        
        metric_history.add(value, timestamp)
        
        assert len(metric_history.values) == 1
        assert len(metric_history.timestamps) == 1
        assert metric_history.values[0] == value
        assert metric_history.timestamps[0] == timestamp
        
    def test_max_size(self, prediction_window):
        history = MetricHistory(prediction_window)
        max_size = prediction_window.num_buckets
        
        # Add more than max size
        for i in range(max_size + 5):
            history.add(float(i))
            
        assert len(history.values) == max_size
        assert list(history.values)[-1] == float(max_size + 4)
        
    def test_get_series(self, metric_history):
        values = [1.0, 2.0, 3.0]
        timestamps = [
            datetime.utcnow() + timedelta(seconds=i)
            for i in range(3)
        ]
        
        for v, t in zip(values, timestamps):
            metric_history.add(v, t)
            
        series_values, series_timestamps = metric_history.get_series()
        
        assert series_values == values
        assert series_timestamps == timestamps
        
    def test_is_ready(self, metric_history):
        assert not metric_history.is_ready()
        
        # Fill up to window size
        for i in range(metric_history.window.num_buckets):
            metric_history.add(float(i))
            
        assert metric_history.is_ready()

class TestAnomalyDetector:
    @pytest.fixture
    def detector(self):
        return AnomalyDetector(
            threshold_sigmas=2.0,
            min_samples=5
        )
        
    def test_not_enough_samples(self, detector):
        values = [1.0, 2.0, 3.0]  # Less than min_samples
        assert not detector.is_anomalous(values)
        
    def test_normal_values(self, detector):
        # Generate normal distribution
        np.random.seed(42)
        values = list(np.random.normal(10, 1, 10))
        assert not detector.is_anomalous(values)
        
    def test_anomalous_value(self, detector):
        # Generate normal values with outlier
        values = list(np.random.normal(10, 1, 10))
        values.append(20.0)  # Add outlier
        assert detector.is_anomalous(values)

class TestTrendAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return TrendAnalyzer(
            forecast_seconds=30,
            trend_threshold=0.1
        )
        
    def test_predict_empty_series(self, analyzer):
        values = []
        timestamps = []
        
        prediction = analyzer.predict_value(values, timestamps)
        assert prediction == 0.0
        
    def test_predict_increasing_trend(self, analyzer):
        timestamps = [
            datetime.utcnow() + timedelta(seconds=i)
            for i in range(10)
        ]
        values = list(range(10))  # Linear increase
        
        prediction = analyzer.predict_value(values, timestamps)
        assert prediction > values[-1]  # Should predict higher value
        
    def test_get_trend_strength(self, analyzer):
        timestamps = [
            datetime.utcnow() + timedelta(seconds=i)
            for i in range(10)
        ]
        
        # Strong upward trend
        values = list(range(10))
        trend = analyzer.get_trend(values, timestamps)
        assert trend > analyzer.trend_threshold
        
        # Flat trend
        values = [5.0] * 10
        trend = analyzer.get_trend(values, timestamps)
        assert abs(trend) < analyzer.trend_threshold

class TestFailurePredictor:
    async def test_record_metric(self, failure_predictor, mock_metrics):
        metric = PredictionMetric.ERROR_RATE
        value = 0.1
        
        await failure_predictor.record_metric(metric, value)
        
        history = failure_predictor.histories[metric]
        assert history.values[-1] == value
        mock_metrics.gauge.assert_awaited_once()
        
    async def test_predict_not_ready(self, failure_predictor):
        will_fail, confidence = await failure_predictor.predict_failure()
        
        assert not will_fail
        assert confidence == 0.0
        
    async def test_predict_threshold_breach(self, failure_predictor):
        # Add error rate above threshold
        metric = PredictionMetric.ERROR_RATE
        threshold = failure_predictor.thresholds[metric]
        
        # Fill history
        for _ in range(failure_predictor.window.num_buckets - 1):
            await failure_predictor.record_metric(metric, 0.0)
            
        # Add value above threshold
        await failure_predictor.record_metric(metric, threshold * 2)
        
        will_fail, confidence = await failure_predictor.predict_failure()
        assert will_fail
        assert confidence > 0.5
        
    async def test_predict_anomaly(self, failure_predictor):
        metric = PredictionMetric.LATENCY
        
        # Fill history with normal values
        for _ in range(failure_predictor.window.num_buckets - 1):
            await failure_predictor.record_metric(metric, 100.0)
            
        # Add anomalous value
        await failure_predictor.record_metric(metric, 5000.0)
        
        will_fail, confidence = await failure_predictor.predict_failure()
        assert will_fail
        assert confidence > 0.5
        
    async def test_update_dynamic_thresholds(self, failure_predictor):
        metric = PredictionMetric.REQUEST_RATE
        
        # Fill history
        values = list(np.random.normal(100, 10, 
                                     failure_predictor.window.num_buckets))
        for value in values:
            await failure_predictor.record_metric(metric, value)
            
        await failure_predictor.update_thresholds()
        
        assert failure_predictor.thresholds[metric] is not None
        assert failure_predictor.thresholds[metric] > np.mean(values)
        
    def test_get_prediction_metrics(self, failure_predictor):
        metric = PredictionMetric.CPU_USAGE
        values = [50.0, 60.0, 70.0]
        
        for value in values:
            failure_predictor.histories[metric].add(value)
            
        metrics = failure_predictor.get_prediction_metrics()
        
        assert f"{metric.value}_current" in metrics
        assert f"{metric.value}_mean" in metrics
        assert f"{metric.value}_std" in metrics
        assert f"{metric.value}_threshold" in metrics 