# Metrics and Monitoring Standards

## Purpose
Define standardized metrics collection, monitoring, and alerting patterns across the Datapunk platform to ensure comprehensive observability and proactive issue detection.

## Context
Monitoring is implemented across multiple layers:
1. Infrastructure metrics (system resources)
2. Service metrics (application performance)
3. Business metrics (operational KPIs)
4. Security metrics (threat detection)

## Design/Details

### 1. Metric Types

```yaml
metric_types:
  counters:
    purpose: "Monotonically increasing values"
    use_cases:
      - "Request counts"
      - "Error counts"
      - "Event totals"
    naming_pattern: "{system}_{metric}_total"
    
  gauges:
    purpose: "Point-in-time measurements"
    use_cases:
      - "Memory usage"
      - "Active connections"
      - "Queue depth"
    naming_pattern: "{system}_{metric}_current"
    
  histograms:
    purpose: "Distribution of values"
    use_cases:
      - "Request duration"
      - "Response size"
      - "Queue wait time"
    naming_pattern: "{system}_{metric}_seconds"
    
  summaries:
    purpose: "Calculated aggregations"
    use_cases:
      - "Request rate"
      - "Error percentage"
      - "Success ratio"
    naming_pattern: "{system}_{metric}_ratio"
```

### 2. Standard Metrics

```yaml
standard_metrics:
  service_health:
    - name: "up"
      type: "gauge"
      labels: ["service", "instance"]
      
    - name: "health_status"
      type: "gauge"
      labels: ["service", "check_type"]
      
    - name: "last_check_timestamp"
      type: "gauge"
      labels: ["service", "check_type"]
      
  request_tracking:
    - name: "http_requests_total"
      type: "counter"
      labels: ["service", "method", "path", "status"]
      
    - name: "http_request_duration_seconds"
      type: "histogram"
      labels: ["service", "method", "path"]
      buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
      
    - name: "http_request_size_bytes"
      type: "histogram"
      labels: ["service", "method", "path"]
      
  resource_usage:
    - name: "process_cpu_seconds_total"
      type: "counter"
      labels: ["service", "instance"]
      
    - name: "process_memory_bytes"
      type: "gauge"
      labels: ["service", "instance", "type"]
      
    - name: "process_open_fds"
      type: "gauge"
      labels: ["service", "instance"]
```

### 3. Service-Specific Metrics

```yaml
service_metrics:
  lake:
    - name: "storage_operations_total"
      type: "counter"
      labels: ["operation", "status"]
      
    - name: "vector_search_duration_seconds"
      type: "histogram"
      labels: ["index", "query_type"]
      
  stream:
    - name: "events_processed_total"
      type: "counter"
      labels: ["type", "status"]
      
    - name: "stream_lag_seconds"
      type: "gauge"
      labels: ["topic", "partition"]
      
  cortex:
    - name: "inference_requests_total"
      type: "counter"
      labels: ["model", "version"]
      
    - name: "model_latency_seconds"
      type: "histogram"
      labels: ["model", "operation"]
```

## Implementation Patterns

### 1. Metric Collection

```python
from dataclasses import dataclass, field
from prometheus_client import Counter, Gauge, Histogram
import structlog

logger = structlog.get_logger()

@dataclass
class ServiceMetrics:
    """Standard service metrics collection."""
    
    # Service health
    up: Gauge = field(default_factory=lambda: Gauge(
        'service_up',
        'Service operational status',
        ['service', 'instance']
    ))
    
    # Request metrics
    requests_total: Counter = field(default_factory=lambda: Counter(
        'http_requests_total',
        'Total HTTP requests',
        ['service', 'method', 'path', 'status']
    ))
    
    request_duration: Histogram = field(default_factory=lambda: Histogram(
        'http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['service', 'method', 'path'],
        buckets=[.01, .05, .1, .5, 1, 5]
    ))
    
    def record_request(self,
                      method: str,
                      path: str,
                      status: int,
                      duration: float):
        """Record HTTP request metrics."""
        self.requests_total.labels(
            service=self.service_name,
            method=method,
            path=path,
            status=status
        ).inc()
        
        self.request_duration.labels(
            service=self.service_name,
            method=method,
            path=path
        ).observe(duration)
```

### 2. Monitoring Integration

```python
from typing import Optional, Dict
import aiohttp
import asyncio

class MetricsExporter:
    """Export metrics to monitoring system."""
    
    def __init__(self, push_gateway_url: str):
        self.push_gateway_url = push_gateway_url
        self.logger = logger.bind(component="metrics_exporter")
        
    async def push_metrics(self,
                          job: str,
                          instance: str,
                          metrics: Dict) -> bool:
        """Push metrics to Prometheus Push Gateway."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.push_gateway_url}/metrics/job/{job}/instance/{instance}",
                    json=metrics
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error("metrics_push_failed",
                            job=job,
                            instance=instance,
                            error=str(e))
            return False
```

### 3. Alert Rules

```yaml
alert_rules:
  # Service Health Alerts
  service_health:
    - alert: ServiceDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "Service {{ $labels.service }} is down"
        description: "Service {{ $labels.service }} instance {{ $labels.instance }} has been down for more than 1 minute"
        runbook_url: "https://wiki.datapunk.ai/runbooks/service-down"
        
    - alert: ServiceDegraded
      expr: health_status{check_type="aggregate"} == 0.5
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Service {{ $labels.service }} is degraded"
        description: "Service {{ $labels.service }} is reporting degraded status for 5 minutes"
        
    - alert: HighErrorRate
      expr: |
        rate(http_requests_total{status=~"5.."}[5m])
        / rate(http_requests_total[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High error rate for {{ $labels.service }}"
        description: "Error rate is above 10% for 5 minutes"

  # Resource Usage Alerts
  resource_usage:
    - alert: HighMemoryUsage
      expr: process_memory_bytes > 1e9  # 1GB
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High memory usage on {{ $labels.instance }}"
        description: "Memory usage above 1GB for 5 minutes"
        
    - alert: HighCPUUsage
      expr: rate(process_cpu_seconds_total[5m]) > 0.8
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High CPU usage on {{ $labels.instance }}"
        description: "CPU usage above 80% for 5 minutes"
        
    - alert: DiskSpaceRunningOut
      expr: disk_free_bytes / disk_total_bytes < 0.1
      for: 10m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "Low disk space on {{ $labels.instance }}"
        description: "Less than 10% disk space remaining"

  # Performance Alerts
  performance:
    - alert: SlowRequests
      expr: |
        histogram_quantile(0.95, 
          rate(http_request_duration_seconds_bucket[5m])
        ) > 1.0
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Slow requests detected for {{ $labels.service }}"
        description: "95th percentile latency is above 1s for 5 minutes"
        
    - alert: HighConnectionCount
      expr: process_open_fds > 1000
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High connection count on {{ $labels.instance }}"
        description: "More than 1000 open file descriptors"

  # Cache Alerts
  cache:
    - alert: LowCacheHitRate
      expr: cache_hit_ratio < 0.8
      for: 15m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Low cache hit rate for {{ $labels.cache }}"
        description: "Cache hit rate below 80% for 15 minutes"
        
    - alert: HighEvictionRate
      expr: rate(cache_evictions_total[5m]) > 100
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High cache eviction rate for {{ $labels.cache }}"
        description: "Cache eviction rate above 100/s for 5 minutes"

  # Queue Alerts
  queue:
    - alert: QueueBacklog
      expr: rabbitmq_queue_messages > 1000
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Queue backlog on {{ $labels.queue }}"
        description: "More than 1000 messages in queue for 5 minutes"
        
    - alert: DeadLetterQueueNotEmpty
      expr: rabbitmq_queue_messages{queue=~".*dlq.*"} > 0
      for: 1m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "Messages in DLQ {{ $labels.queue }}"
        description: "Dead letter queue contains messages"

  # Service Mesh Alerts
  service_mesh:
    - alert: HighRetryRate
      expr: rate(retry_attempts_total[5m]) > 10
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High retry rate for {{ $labels.service }}"
        description: "More than 10 retries/s for 5 minutes"
        
    - alert: CircuitBreakerOpen
      expr: circuit_breaker_state == 0  # 0 = open
      for: 1m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "Circuit breaker open for {{ $labels.service }}"
        description: "Circuit breaker has been open for 1 minute"

  # Security Alerts
  security:
    - alert: HighAuthFailureRate
      expr: |
        rate(auth_failures_total[5m])
        / rate(auth_attempts_total[5m]) > 0.1
      for: 5m
      labels:
        severity: critical
        team: security
      annotations:
        summary: "High auth failure rate for {{ $labels.service }}"
        description: "Authentication failure rate above 10% for 5 minutes"
        
    - alert: UnusualTrafficSpike
      expr: |
        rate(http_requests_total[5m])
        > 2 * avg_over_time(rate(http_requests_total[1h])[60m:5m])
      for: 5m
      labels:
        severity: warning
        team: security
      annotations:
        summary: "Traffic spike for {{ $labels.service }}"
        description: "Request rate more than double the hourly average"

  # Data Pipeline Alerts
  data_pipeline:
    - alert: ETLJobFailed
      expr: etl_job_status == 0  # 0 = failed
      for: 1m
      labels:
        severity: critical
        team: data
      annotations:
        summary: "ETL job failed for {{ $labels.job }}"
        description: "ETL job has failed"
        
    - alert: DataLagHigh
      expr: stream_lag_seconds > 300  # 5 minutes
      for: 5m
      labels:
        severity: warning
        team: data
      annotations:
        summary: "High data lag in {{ $labels.stream }}"
        description: "Stream processing lag above 5 minutes"

  # Infrastructure Alerts
  infrastructure:
    - alert: NodeDown
      expr: up{job="node"} == 0
      for: 1m
      labels:
        severity: critical
        team: platform
      annotations:
        summary: "Node {{ $labels.instance }} is down"
        description: "Node has been down for more than 1 minute"
        
    - alert: NetworkErrors
      expr: rate(network_errors_total[5m]) > 10
      for: 5m
      labels:
        severity: warning
        team: platform
      annotations:
        summary: "High network error rate on {{ $labels.instance }}"
        description: "Network error rate above 10/s for 5 minutes"
```

## Integration Points

### 1. Prometheus Integration

```yaml
prometheus_config:
  global:
    scrape_interval: 15s
    evaluation_interval: 15s
    
  scrape_configs:
    - job_name: 'datapunk'
      metrics_path: '/metrics'
      static_configs:
        - targets: ['localhost:9090']
      
  alerting:
    alertmanagers:
      - static_configs:
          - targets: ['localhost:9093']
```

### 2. Grafana Dashboards

```yaml
dashboard_templates:
  service_overview:
    panels:
      - title: "Request Rate"
        type: "graph"
        metrics:
          - "rate(http_requests_total[5m])"
          
      - title: "Error Rate"
        type: "graph"
        metrics:
          - "rate(http_requests_total{status=~'5..'}[5m])"
          
      - title: "Response Time"
        type: "heatmap"
        metrics:
          - "rate(http_request_duration_seconds_bucket[5m])"
```

## Security Considerations

### 1. Metric Protection

```yaml
security_measures:
  metric_access:
    authentication: true
    authorization: true
    encryption: true
    
  data_protection:
    pii_exclusion: true
    sensitive_data_masking: true
    
  audit:
    metric_access_logging: true
    configuration_changes: true
```

### 2. Alert Security

```yaml
alert_security:
  notification_channels:
    encryption: true
    authentication: true
    
  sensitive_data:
    redaction: true
    masking: true
```

## Known Issues and Mitigations

### 1. High Cardinality

```python
class CardinalityLimiter:
    """Limit metric cardinality."""
    
    def __init__(self, max_labels: int = 1000):
        self.max_labels = max_labels
        self.label_counts = {}
        
    def should_record(self, metric_name: str, labels: Dict) -> bool:
        """Check if metric should be recorded."""
        label_key = f"{metric_name}:{sorted(labels.items())}"
        
        if label_key not in self.label_counts:
            if len(self.label_counts) >= self.max_labels:
                return False
            self.label_counts[label_key] = 0
            
        self.label_counts[label_key] += 1
        return True
```

### 2. Storage Optimization

```python
class MetricRetention:
    """Manage metric retention."""
    
    def configure_retention(self, metric_type: str) -> str:
        """Get retention period for metric type."""
        return {
            "high_frequency": "15d",
            "medium_frequency": "30d",
            "low_frequency": "90d",
            "compliance": "365d"
        }.get(metric_type, "15d")
```

## Testing Requirements

```yaml
monitoring_tests:
  functional:
    - metric_collection
    - alert_triggering
    - dashboard_rendering
    
  performance:
    - collection_overhead
    - storage_efficiency
    - query_performance
    
  security:
    - access_control
    - data_protection
    - audit_logging
``` 