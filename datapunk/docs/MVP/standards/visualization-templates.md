# Visualization Templates

## Purpose

Define standardized visualization templates for tracing, logging, and metrics data to ensure consistent monitoring and troubleshooting capabilities across services.

## Context

These templates provide a unified view of system behavior, performance, and health across all services.

## Design/Details

### 1. Service Mesh Overview Dashboard

```yaml
dashboard:
  title: "Service Mesh Overview"
  refresh: "30s"
  time_range: "last 24 hours"
  
  layout:
    rows:
      - height: 4
        panels:
          - title: "Service Health Status"
            type: "stat"
            width: 6
            targets:
              - expr: "up{job=~'$service'}"
                legendFormat: "{{instance}}"
            
          - title: "Active Instances"
            type: "gauge"
            width: 6
            targets:
              - expr: "count(up{job=~'$service'}) by (service)"
                legendFormat: "{{service}}"
      
      - height: 8
        panels:
          - title: "Request Flow"
            type: "nodeGraph"
            width: 24
            targets:
              - expr: "rate(service_requests_total[5m])"
                legendFormat: "{{source}} -> {{destination}}"

### 2. Distributed Tracing Dashboard

```yaml
dashboard:
  title: "Distributed Tracing Analysis"
  
  layout:
    rows:
      - height: 8
        panels:
          - title: "Trace Duration Distribution"
            type: "heatmap"
            width: 12
            targets:
              - expr: "rate(trace_duration_seconds_bucket[5m])"
            options:
              tooltip:
                show: true
                showHistogram: true
          
          - title: "Service Dependencies"
            type: "nodeGraph"
            width: 12
            targets:
              - expr: "sum(rate(span_count[5m])) by (service, remote_service)"
      
      - height: 8
        panels:
          - title: "Error Traces"
            type: "table"
            width: 24
            targets:
              - expr: |
                  traces_total{status="error"}
                  * on(trace_id) group_left(error)
                  last_over_time(error_details[1h])
            transform:
              - type: "organize"
                options:
                  excludeByName:
                    trace_id: false
                    service: false
                    error: false
                    timestamp: false
```

### 3. Error Analysis Dashboard

```yaml
dashboard:
  title: "Error Analysis"
  
  layout:
    rows:
      - height: 6
        panels:
          - title: "Error Rate by Service"
            type: "timeseries"
            width: 12
            targets:
              - expr: |
                  sum(rate(error_total[5m])) by (service)
                  / sum(rate(requests_total[5m])) by (service)
            options:
              legend:
                showLegend: true
                placement: "right"
          
          - title: "Error Types Distribution"
            type: "piechart"
            width: 12
            targets:
              - expr: "sum(error_total) by (type)"
      
      - height: 8
        panels:
          - title: "Error Timeline"
            type: "timeline"
            width: 24
            targets:
              - expr: "error_total"
                legendFormat: "{{error_type}}"
```

### 4. Performance Analysis Dashboard

```yaml
dashboard:
  title: "Performance Analysis"
  
  layout:
    rows:
      - height: 8
        panels:
          - title: "Service Latency Distribution"
            type: "heatmap"
            width: 12
            targets:
              - expr: "rate(request_duration_seconds_bucket[5m])"
            options:
              tooltip:
                show: true
                showHistogram: true
          
          - title: "Resource Usage"
            type: "timeseries"
            width: 12
            targets:
              - expr: "rate(process_cpu_seconds_total[5m])"
                legendFormat: "CPU - {{instance}}"
              - expr: "process_resident_memory_bytes"
                legendFormat: "Memory - {{instance}}"
      
      - height: 8
        panels:
          - title: "Circuit Breaker Status"
            type: "status-history"
            width: 12
            targets:
              - expr: "circuit_breaker_state"
                legendFormat: "{{service}}"
          
          - title: "Retry Patterns"
            type: "timeseries"
            width: 12
            targets:
              - expr: "rate(retry_attempts_total[5m])"
                legendFormat: "{{service}}"
```

### 5. Log Analysis Dashboard

```yaml
dashboard:
  title: "Log Analysis"
  
  layout:
    rows:
      - height: 4
        panels:
          - title: "Log Volume"
            type: "stat"
            width: 6
            targets:
              - expr: 'sum(rate(log_messages_total[5m])) by (level)'
          
          - title: "Error Rate"
            type: "gauge"
            width: 6
            targets:
              - expr: |
                  sum(rate(log_messages_total{level="error"}[5m]))
                  / sum(rate(log_messages_total[5m]))
      
      - height: 12
        panels:
          - title: "Log Explorer"
            type: "logs"
            width: 24
            targets:
              - expr: '{job=~"$application"}'
                refId: "A"
            options:
              showTime: true
              showLabels: false
              showCommonLabels: true
              wrapLogMessage: true
              prettifyLogMessage: true
              enableLogDetails: true
```

## Integration Points

### 1. Data Sources

```yaml
datasources:
  prometheus:
    type: "prometheus"
    url: "http://prometheus:9090"
    access: "proxy"
    
  loki:
    type: "loki"
    url: "http://loki:3100"
    access: "proxy"
    
  jaeger:
    type: "jaeger"
    url: "http://jaeger:16686"
    access: "proxy"
```

### 2. Alert Integration

```yaml
alert_rules:
  - name: "High Error Rate"
    expr: |
      sum(rate(error_total[5m])) by (service)
      / sum(rate(requests_total[5m])) by (service)
      > 0.1
    for: "5m"
    labels:
      severity: warning
    annotations:
      summary: "High error rate for {{ $labels.service }}"
      
  - name: "Slow Service Response"
    expr: |
      histogram_quantile(0.95,
        sum(rate(request_duration_seconds_bucket[5m])) by (le, service)
      ) > 1.0
    for: "5m"
    labels:
      severity: warning
    annotations:
      summary: "Slow response time for {{ $labels.service }}"
```

## Usage Notes

1. **Dashboard Variables**
   - `$service`: Multi-select for services
   - `$instance`: Instance selector
   - `$environment`: Environment selector
   - `$time_range`: Time range selector

2. **Refresh Rates**
   - Real-time views: 30s
   - Historical views: 5m
   - Long-term analysis: 15m

3. **Performance Considerations**
   - Use appropriate time ranges
   - Limit high-cardinality metrics
   - Enable caching where appropriate
