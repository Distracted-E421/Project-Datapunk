import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.health import (
    HealthTrendAnalyzer,
    TrendConfig,
    HealthStatus,
    TrendPattern,
    TrendResult,
    AnomalyDetection
)

@pytest.fixture
def trend_config():
    return TrendConfig(
        window_size=60,  # 1 minute
        sample_interval=1,  # 1 second
        min_samples=10,
        anomaly_threshold=2.0,  # standard deviations
        trend_sensitivity=0.8
    )

@pytest.fixture
def trend_analyzer(trend_config):
    return HealthTrendAnalyzer(config=trend_config)

@pytest.fixture
def sample_metrics():
    base_time = datetime.utcnow()
    return [
        {
            "timestamp": base_time + timedelta(seconds=i),
            "value": 100 + i,  # Increasing trend
            "status": HealthStatus.HEALTHY
        }
        for i in range(30)
    ]

@pytest.mark.asyncio
async def test_analyzer_initialization(trend_analyzer, trend_config):
    assert trend_analyzer.config == trend_config
    assert trend_analyzer.is_initialized
    assert len(trend_analyzer.patterns) == 0

@pytest.mark.asyncio
async def test_metric_ingestion(trend_analyzer, sample_metrics):
    for metric in sample_metrics:
        await trend_analyzer.ingest_metric(
            name="response_time",
            value=metric["value"],
            timestamp=metric["timestamp"],
            status=metric["status"]
        )
    
    metrics = await trend_analyzer.get_metrics("response_time")
    assert len(metrics) == len(sample_metrics)

@pytest.mark.asyncio
async def test_trend_detection(trend_analyzer):
    # Simulate increasing trend
    base_time = datetime.utcnow()
    for i in range(20):
        await trend_analyzer.ingest_metric(
            name="cpu_usage",
            value=50 + i * 2,  # Linear increase
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    trend = await trend_analyzer.analyze_trend("cpu_usage")
    assert trend.pattern == TrendPattern.INCREASING
    assert trend.slope > 0

@pytest.mark.asyncio
async def test_pattern_recognition(trend_analyzer):
    # Simulate cyclic pattern
    base_time = datetime.utcnow()
    for i in range(60):
        value = 50 + 30 * math.sin(i * math.pi / 30)  # Sinusoidal pattern
        await trend_analyzer.ingest_metric(
            name="memory_usage",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    pattern = await trend_analyzer.detect_pattern("memory_usage")
    assert pattern.type == TrendPattern.CYCLIC
    assert pattern.period is not None

@pytest.mark.asyncio
async def test_anomaly_detection(trend_analyzer):
    # Normal values followed by anomaly
    base_time = datetime.utcnow()
    normal_values = [100 + random.normalvariate(0, 5) for _ in range(20)]
    anomaly_value = 200  # Significant deviation
    
    # Ingest normal values
    for i, value in enumerate(normal_values):
        await trend_analyzer.ingest_metric(
            name="request_count",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    # Ingest anomaly
    await trend_analyzer.ingest_metric(
        name="request_count",
        value=anomaly_value,
        timestamp=base_time + timedelta(seconds=len(normal_values)),
        status=HealthStatus.HEALTHY
    )
    
    anomalies = await trend_analyzer.detect_anomalies("request_count")
    assert len(anomalies) == 1
    assert abs(anomalies[0].value - anomaly_value) < 0.01

@pytest.mark.asyncio
async def test_trend_forecasting(trend_analyzer):
    # Simulate linear trend
    base_time = datetime.utcnow()
    for i in range(30):
        await trend_analyzer.ingest_metric(
            name="latency",
            value=100 + i * 2,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    forecast = await trend_analyzer.forecast_trend(
        metric_name="latency",
        horizon=5  # 5 seconds ahead
    )
    
    assert len(forecast.values) == 5
    assert all(140 <= v <= 150 for v in forecast.values)  # Expected range

@pytest.mark.asyncio
async def test_seasonal_decomposition(trend_analyzer):
    # Simulate seasonal pattern
    base_time = datetime.utcnow()
    for i in range(100):
        # Trend + Seasonal + Random
        value = (
            i * 0.5 +  # Trend
            10 * math.sin(i * 2 * math.pi / 24) +  # 24-point seasonality
            random.normalvariate(0, 1)  # Random noise
        )
        await trend_analyzer.ingest_metric(
            name="traffic",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    decomposition = await trend_analyzer.decompose_series("traffic")
    assert "trend" in decomposition
    assert "seasonal" in decomposition
    assert "residual" in decomposition

@pytest.mark.asyncio
async def test_correlation_analysis(trend_analyzer):
    base_time = datetime.utcnow()
    # Simulate correlated metrics
    for i in range(50):
        base_value = i * 2
        await trend_analyzer.ingest_metric(
            name="metric1",
            value=base_value + random.normalvariate(0, 1),
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
        await trend_analyzer.ingest_metric(
            name="metric2",
            value=base_value * 2 + random.normalvariate(0, 2),
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    correlation = await trend_analyzer.analyze_correlation(
        metric1="metric1",
        metric2="metric2"
    )
    assert correlation.coefficient > 0.9  # Strong positive correlation

@pytest.mark.asyncio
async def test_threshold_violation_detection(trend_analyzer):
    base_time = datetime.utcnow()
    threshold = 150
    
    # Simulate metrics with threshold violations
    for i in range(30):
        value = 100 + i * 2
        await trend_analyzer.ingest_metric(
            name="cpu_temp",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY if value < threshold else HealthStatus.UNHEALTHY
        )
    
    violations = await trend_analyzer.detect_threshold_violations(
        metric_name="cpu_temp",
        threshold=threshold
    )
    
    assert len(violations) > 0
    assert all(v.value >= threshold for v in violations)

@pytest.mark.asyncio
async def test_trend_change_detection(trend_analyzer):
    base_time = datetime.utcnow()
    
    # First trend: linear increase
    for i in range(20):
        await trend_analyzer.ingest_metric(
            name="response_time",
            value=100 + i * 2,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    # Second trend: sudden plateau
    for i in range(20, 40):
        await trend_analyzer.ingest_metric(
            name="response_time",
            value=140 + random.normalvariate(0, 1),
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    changes = await trend_analyzer.detect_trend_changes("response_time")
    assert len(changes) == 1
    assert abs(changes[0].timestamp - (base_time + timedelta(seconds=20))) < timedelta(seconds=2)

@pytest.mark.asyncio
async def test_outlier_detection(trend_analyzer):
    base_time = datetime.utcnow()
    
    # Normal distribution with outliers
    values = [100 + random.normalvariate(0, 5) for _ in range(30)]
    values[10] = 200  # Add outlier
    values[20] = 50   # Add outlier
    
    for i, value in enumerate(values):
        await trend_analyzer.ingest_metric(
            name="metric",
            value=value,
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    outliers = await trend_analyzer.detect_outliers("metric")
    assert len(outliers) == 2
    assert any(abs(o.value - 200) < 1 for o in outliers)
    assert any(abs(o.value - 50) < 1 for o in outliers)

@pytest.mark.asyncio
async def test_trend_persistence(trend_analyzer):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Add some test data
        await trend_analyzer.ingest_metric(
            name="test_metric",
            value=100,
            timestamp=datetime.utcnow(),
            status=HealthStatus.HEALTHY
        )
        
        await trend_analyzer.save_state()
        mock_file.write.assert_called_once()
        
        await trend_analyzer.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_metric_aggregation(trend_analyzer):
    base_time = datetime.utcnow()
    
    # Ingest multiple metrics
    for i in range(60):
        await trend_analyzer.ingest_metric(
            name="test_metric",
            value=100 + random.normalvariate(0, 5),
            timestamp=base_time + timedelta(seconds=i),
            status=HealthStatus.HEALTHY
        )
    
    # Test different aggregation windows
    windows = [5, 15, 30]  # seconds
    for window in windows:
        aggregated = await trend_analyzer.aggregate_metrics(
            metric_name="test_metric",
            window_size=window
        )
        assert len(aggregated) == 60 // window

@pytest.mark.asyncio
async def test_trend_classification(trend_analyzer):
    base_time = datetime.utcnow()
    patterns = [
        (range(30), lambda x: 100 + x),           # Linear
        (range(30), lambda x: 100 + x**2),        # Quadratic
        (range(30), lambda x: 100 * math.exp(x/10))  # Exponential
    ]
    
    for i, (range_vals, pattern_func) in enumerate(patterns):
        metric_name = f"pattern_{i}"
        for x in range_vals:
            await trend_analyzer.ingest_metric(
                name=metric_name,
                value=pattern_func(x),
                timestamp=base_time + timedelta(seconds=x),
                status=HealthStatus.HEALTHY
            )
        
        classification = await trend_analyzer.classify_trend(metric_name)
        assert classification.pattern in [
            TrendPattern.LINEAR,
            TrendPattern.QUADRATIC,
            TrendPattern.EXPONENTIAL
        ] 