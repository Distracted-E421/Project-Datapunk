import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from datapunk_shared.mesh.auth import (
    ThreatDetector,
    ThreatConfig,
    ThreatPattern,
    ThreatLevel,
    ThreatAlert
)

@pytest.fixture
def threat_config():
    return ThreatConfig(
        scan_interval=5,
        pattern_refresh_interval=300,
        alert_threshold=3,
        retention_days=7
    )

@pytest.fixture
def threat_detector(threat_config):
    return ThreatDetector(config=threat_config)

@pytest.fixture
def sample_patterns():
    return [
        ThreatPattern(
            id="sql_injection",
            pattern=r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b.*\b(FROM|INTO|WHERE)\b)",
            level=ThreatLevel.HIGH,
            description="SQL Injection attempt"
        ),
        ThreatPattern(
            id="xss_basic",
            pattern=r"(<script>|<img.*onerror=|javascript:)",
            level=ThreatLevel.MEDIUM,
            description="Cross-site scripting attempt"
        )
    ]

@pytest.mark.asyncio
async def test_detector_initialization(threat_detector, threat_config):
    assert threat_detector.config == threat_config
    assert not threat_detector.is_running
    assert len(threat_detector.patterns) == 0

@pytest.mark.asyncio
async def test_pattern_registration(threat_detector, sample_patterns):
    for pattern in sample_patterns:
        await threat_detector.register_pattern(pattern)
    
    assert len(threat_detector.patterns) == len(sample_patterns)
    assert all(p.id in threat_detector.patterns for p in sample_patterns)

@pytest.mark.asyncio
async def test_threat_detection(threat_detector, sample_patterns):
    await threat_detector.register_pattern(sample_patterns[0])  # SQL injection pattern
    
    request = {
        "query": "SELECT * FROM users WHERE password = '1234'",
        "source_ip": "192.168.1.100",
        "timestamp": datetime.utcnow()
    }
    
    threats = await threat_detector.analyze_request(request)
    assert len(threats) == 1
    assert threats[0].pattern_id == "sql_injection"
    assert threats[0].level == ThreatLevel.HIGH

@pytest.mark.asyncio
async def test_anomaly_detection(threat_detector):
    # Simulate normal traffic pattern
    baseline = {
        "requests_per_minute": 100,
        "error_rate": 0.02,
        "avg_response_time": 0.2
    }
    
    await threat_detector.update_baseline(baseline)
    
    # Test anomalous traffic
    metrics = {
        "requests_per_minute": 500,  # Sudden spike
        "error_rate": 0.15,  # High error rate
        "avg_response_time": 1.5  # Slow responses
    }
    
    anomalies = await threat_detector.detect_anomalies(metrics)
    assert len(anomalies) > 0
    assert any(a.metric == "requests_per_minute" for a in anomalies)

@pytest.mark.asyncio
async def test_alert_generation(threat_detector):
    alerts = []
    
    def alert_handler(alert: ThreatAlert):
        alerts.append(alert)
    
    threat_detector.on_threat_detected(alert_handler)
    
    # Simulate malicious request
    request = {
        "query": "DROP TABLE users;--",
        "source_ip": "192.168.1.100",
        "timestamp": datetime.utcnow()
    }
    
    await threat_detector.register_pattern(sample_patterns[0])
    await threat_detector.analyze_request(request)
    
    assert len(alerts) == 1
    assert alerts[0].level == ThreatLevel.HIGH

@pytest.mark.asyncio
async def test_ip_based_detection(threat_detector):
    # Simulate multiple failed login attempts
    source_ip = "192.168.1.100"
    
    for _ in range(5):
        await threat_detector.record_failed_auth(source_ip)
    
    is_suspicious = await threat_detector.is_ip_suspicious(source_ip)
    assert is_suspicious

@pytest.mark.asyncio
async def test_pattern_matching_performance(threat_detector, sample_patterns):
    for pattern in sample_patterns:
        await threat_detector.register_pattern(pattern)
    
    # Generate test requests
    requests = [
        {"query": f"test query {i}", "source_ip": "192.168.1.100"}
        for i in range(1000)
    ]
    
    start_time = datetime.utcnow()
    
    # Analyze requests concurrently
    results = await asyncio.gather(*[
        threat_detector.analyze_request(req)
        for req in requests
    ])
    
    duration = (datetime.utcnow() - start_time).total_seconds()
    assert duration < 2.0  # Should process 1000 requests within 2 seconds

@pytest.mark.asyncio
async def test_threat_metrics_collection(threat_detector):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        request = {
            "query": "DROP TABLE users;--",
            "source_ip": "192.168.1.100",
            "timestamp": datetime.utcnow()
        }
        
        await threat_detector.register_pattern(sample_patterns[0])
        await threat_detector.analyze_request(request)
        
        mock_collector.return_value.record_counter.assert_called()
        mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_pattern_refresh(threat_detector):
    with patch.object(threat_detector, '_load_patterns') as mock_load:
        mock_load.return_value = sample_patterns
        
        await threat_detector.refresh_patterns()
        assert len(threat_detector.patterns) == len(sample_patterns)
        mock_load.assert_called_once()

@pytest.mark.asyncio
async def test_threat_correlation(threat_detector):
    # Record related security events
    events = [
        {
            "type": "failed_login",
            "source_ip": "192.168.1.100",
            "timestamp": datetime.utcnow()
        },
        {
            "type": "sql_injection",
            "source_ip": "192.168.1.100",
            "timestamp": datetime.utcnow()
        }
    ]
    
    for event in events:
        await threat_detector.record_security_event(event)
    
    correlations = await threat_detector.analyze_correlations("192.168.1.100")
    assert len(correlations) > 0
    assert correlations[0].threat_level >= ThreatLevel.HIGH

@pytest.mark.asyncio
async def test_threat_persistence(threat_detector):
    with patch('aiofiles.open', create=True) as mock_open:
        mock_file = AsyncMock()
        mock_open.return_value.__aenter__.return_value = mock_file
        
        # Save threat data
        await threat_detector.save_state()
        mock_file.write.assert_called_once()
        
        # Load threat data
        await threat_detector.load_state()
        mock_file.read.assert_called_once()

@pytest.mark.asyncio
async def test_cleanup(threat_detector):
    # Add old threat data
    old_event = {
        "type": "failed_login",
        "source_ip": "192.168.1.100",
        "timestamp": datetime.utcnow() - timedelta(days=10)
    }
    await threat_detector.record_security_event(old_event)
    
    # Clean up old data
    await threat_detector.cleanup()
    
    # Verify old data is removed
    events = await threat_detector.get_security_events("192.168.1.100")
    assert len(events) == 0 