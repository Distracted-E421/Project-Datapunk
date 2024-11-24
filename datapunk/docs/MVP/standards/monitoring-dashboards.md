# Monitoring Dashboard Standards

## Purpose
Define standardized Grafana dashboards and alert correlation patterns for comprehensive system monitoring and troubleshooting.

## Context
Dashboards are organized by:
1. Service-level metrics
2. Infrastructure metrics
3. Business metrics
4. Cross-service correlations

## Design/Details

### 1. Service Overview Dashboard

```yaml
dashboard:
  title: "Service Overview"
  refresh: "30s"
  time_options: ["5m", "15m", "30m", "1h", "3h", "6h", "12h", "24h", "7d"]
  
  rows:
    - title: "Service Health"
      panels:
        - title: "Service Status"
          type: "stat"
          targets:
            - expr: "up{job=~'$service'}"
              legendFormat: "{{instance}}"
          
        - title: "Health Score"
          type: "gauge"
          targets:
            - expr: "health_status{service=~'$service'}"
              thresholds:
                - value: 0
                  color: "red"
                - value: 0.5
                  color: "yellow"
                - value: 0.8
                  color: "green"
    
    - title: "Request Metrics"
      panels:
        - title: "Request Rate"
          type: "graph"
          targets:
            - expr: "rate(http_requests_total{service=~'$service'}[5m])"
              legendFormat: "{{method}} {{path}}"
          
        - title: "Error Rate"
          type: "graph"
          targets:
            - expr: |
                sum(rate(http_requests_total{status=~"5..", service=~"$service"}[5m]))
                /
                sum(rate(http_requests_total{service=~"$service"}[5m]))
              legendFormat: "Error %"
          
        - title: "Response Time"
          type: "heatmap"
          targets:
            - expr: "rate(http_request_duration_seconds_bucket{service=~'$service'}[5m])"
```

### 2. Service Mesh Dashboard

```yaml
dashboard:
  title: "Service Mesh Overview"
  
  rows:
    - title: "Circuit Breakers"
      panels:
        - title: "Circuit Breaker Status"
          type: "stat"
          targets:
            - expr: "circuit_breaker_state"
              legendFormat: "{{service}}"
          
        - title: "Circuit Breaker Trips"
          type: "graph"
          targets:
            - expr: "rate(circuit_breaker_trips_total[5m])"
              legendFormat: "{{service}}"
    
    - title: "Retry Metrics"
      panels:
        - title: "Retry Rate"
          type: "graph"
          targets:
            - expr: "rate(retry_attempts_total[5m])"
              legendFormat: "{{service}} {{operation}}"
          
        - title: "Retry Success Rate"
          type: "graph"
          targets:
            - expr: |
                sum(rate(retry_success_total[5m]))
                /
                sum(rate(retry_attempts_total[5m]))
```

### 3. Resource Usage Dashboard

```yaml
dashboard:
  title: "Resource Usage"
  
  rows:
    - title: "CPU Usage"
      panels:
        - title: "CPU Usage by Service"
          type: "graph"
          targets:
            - expr: "rate(process_cpu_seconds_total[5m])"
              legendFormat: "{{service}}"
          
        - title: "System CPU Usage"
          type: "graph"
          targets:
            - expr: "1 - avg(rate(node_cpu_seconds_total{mode='idle'}[5m]))"
    
    - title: "Memory Usage"
      panels:
        - title: "Memory Usage by Service"
          type: "graph"
          targets:
            - expr: "process_resident_memory_bytes"
              legendFormat: "{{service}}"
          
        - title: "System Memory Usage"
          type: "graph"
          targets:
            - expr: "1 - node_memory_MemAvailable_bytes/node_memory_MemTotal_bytes"
```

## Alert Correlation Rules

### 1. Service Degradation Pattern

```yaml
alert_correlation:
  pattern_name: "service_degradation"
  conditions:
    - alert: "HighErrorRate"
      threshold: 0.1
      duration: "5m"
      
    - alert: "SlowRequests"
      threshold: 1.0
      duration: "5m"
      
    - alert: "HighCPUUsage"
      threshold: 0.8
      duration: "5m"
  
  correlation_rules:
    - name: "Resource Exhaustion"
      condition: "HighCPUUsage && SlowRequests"
      severity: "critical"
      
    - name: "Service Failure"
      condition: "HighErrorRate && !HighCPUUsage"
      severity: "critical"
```

### 2. Infrastructure Issues Pattern

```yaml
alert_correlation:
  pattern_name: "infrastructure_issues"
  conditions:
    - alert: "DiskSpaceRunningOut"
      threshold: 0.1
      duration: "10m"
      
    - alert: "HighMemoryUsage"
      threshold: 0.9
      duration: "5m"
      
    - alert: "NetworkErrors"
      threshold: 10
      duration: "5m"
  
  correlation_rules:
    - name: "Storage Crisis"
      condition: "DiskSpaceRunningOut && HighMemoryUsage"
      severity: "critical"
      
    - name: "Network Degradation"
      condition: "NetworkErrors && !DiskSpaceRunningOut"
      severity: "warning"
```

### 3. Data Pipeline Issues Pattern

```yaml
alert_correlation:
  pattern_name: "data_pipeline_issues"
  conditions:
    - alert: "ETLJobFailed"
      threshold: 1
      duration: "1m"
      
    - alert: "DataLagHigh"
      threshold: 300
      duration: "5m"
      
    - alert: "QueueBacklog"
      threshold: 1000
      duration: "5m"
  
  correlation_rules:
    - name: "Pipeline Stall"
      condition: "DataLagHigh && QueueBacklog"
      severity: "critical"
      
    - name: "Processing Failure"
      condition: "ETLJobFailed && !QueueBacklog"
      severity: "warning"
```

## Dashboard Organization

### 1. Folder Structure

```yaml
grafana_folders:
  - name: "Service Dashboards"
    dashboards:
      - "Service Overview"
      - "Service Mesh"
      - "API Gateway"
      
  - name: "Infrastructure Dashboards"
    dashboards:
      - "Resource Usage"
      - "Network Overview"
      - "Storage Overview"
      
  - name: "Business Dashboards"
    dashboards:
      - "Data Pipeline"
      - "Processing Metrics"
      - "Business KPIs"
```

### 2. Variables

```yaml
dashboard_variables:
  - name: "service"
    type: "query"
    query: "label_values(up, service)"
    
  - name: "instance"
    type: "query"
    query: "label_values(up{service='$service'}, instance)"
    
  - name: "interval"
    type: "interval"
    values: ["30s", "1m", "5m", "10m", "30m", "1h"]
```

### 3. Annotations

```yaml
dashboard_annotations:
  - name: "Deployments"
    datasource: "Loki"
    expr: '{app="deployment-service"} |= "deployed"'
    
  - name: "Incidents"
    datasource: "Loki"
    expr: '{severity="critical"}'
```

## Integration Points

### 1. Alert Manager Integration

```yaml
alertmanager_config:
  route:
    group_by: ['alertname', 'cluster', 'service']
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
    receiver: 'default'
    routes:
      - match:
          severity: critical
        receiver: 'pagerduty'
      - match:
          severity: warning
        receiver: 'slack'
```

### 2. Loki Integration

```yaml
loki_config:
  datasources:
    - name: "Loki"
      type: "loki"
      access: "proxy"
      url: "http://loki:3100"
      jsonData:
        maxLines: 1000
``` 