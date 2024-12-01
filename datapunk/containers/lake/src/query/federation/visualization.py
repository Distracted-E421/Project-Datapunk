from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import logging
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from .monitoring import FederationMonitor, QueryMetrics
from .alerting import AlertManager, AlertSeverity, AlertType

class FederationVisualizer:
    """Visualizes federation monitoring and profiling data."""
    
    def __init__(self,
                 monitor: FederationMonitor,
                 alert_manager: AlertManager):
        self.monitor = monitor
        self.alert_manager = alert_manager
        self.logger = logging.getLogger(__name__)
    
    def create_performance_dashboard(self,
                                  hours: int = 24) -> Dict[str, Any]:
        """Create performance monitoring dashboard."""
        try:
            # Get data
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            metrics = self.monitor.get_historical_metrics(
                start_time=start_time,
                end_time=end_time
            )
            
            if not metrics:
                return {
                    'error': 'No data available for the specified time range'
                }
            
            # Create figures
            figures = {}
            
            # Query execution time trend
            fig_exec_time = go.Figure()
            times = [m.execution_time_ms for m in metrics if m.execution_time_ms]
            timestamps = [m.start_time for m in metrics if m.execution_time_ms]
            
            fig_exec_time.add_trace(go.Scatter(
                x=timestamps,
                y=times,
                mode='lines+markers',
                name='Execution Time (ms)'
            ))
            fig_exec_time.update_layout(
                title='Query Execution Time Trend',
                xaxis_title='Time',
                yaxis_title='Execution Time (ms)'
            )
            figures['execution_time'] = fig_exec_time
            
            # Resource usage
            fig_resources = make_subplots(
                rows=2,
                cols=1,
                subplot_titles=('CPU Usage', 'Memory Usage')
            )
            
            fig_resources.add_trace(
                go.Scatter(
                    x=[m.start_time for m in metrics],
                    y=[m.cpu_usage_percent for m in metrics],
                    mode='lines',
                    name='CPU %'
                ),
                row=1,
                col=1
            )
            
            fig_resources.add_trace(
                go.Scatter(
                    x=[m.start_time for m in metrics],
                    y=[m.memory_usage_mb for m in metrics],
                    mode='lines',
                    name='Memory (MB)'
                ),
                row=2,
                col=1
            )
            
            fig_resources.update_layout(
                height=600,
                title='Resource Usage'
            )
            figures['resources'] = fig_resources
            
            # Cache performance
            fig_cache = go.Figure()
            for m in metrics:
                total = m.cache_hits + m.cache_misses
                ratio = m.cache_hits / total if total > 0 else 0
                fig_cache.add_trace(go.Scatter(
                    x=[m.start_time],
                    y=[ratio],
                    mode='markers',
                    name='Cache Hit Ratio'
                ))
            
            fig_cache.update_layout(
                title='Cache Performance',
                yaxis_title='Cache Hit Ratio'
            )
            figures['cache'] = fig_cache
            
            # Error distribution
            error_counts = {}
            for m in metrics:
                if m.error_count > 0:
                    date = m.start_time.date()
                    error_counts[date] = error_counts.get(date, 0) + m.error_count
            
            if error_counts:
                fig_errors = go.Figure(data=[
                    go.Bar(
                        x=list(error_counts.keys()),
                        y=list(error_counts.values())
                    )
                ])
                fig_errors.update_layout(
                    title='Daily Error Distribution',
                    xaxis_title='Date',
                    yaxis_title='Error Count'
                )
                figures['errors'] = fig_errors
            
            return {
                'figures': figures,
                'summary': self._create_summary(metrics)
            }
        except Exception as e:
            self.logger.error(f"Error creating performance dashboard: {e}")
            return {'error': str(e)}
    
    def create_source_dashboard(self) -> Dict[str, Any]:
        """Create data source monitoring dashboard."""
        try:
            source_metrics = self.monitor.source_metrics
            if not source_metrics:
                return {
                    'error': 'No source metrics available'
                }
            
            figures = {}
            
            # Response time comparison
            fig_response = go.Figure(data=[
                go.Bar(
                    x=list(source_metrics.keys()),
                    y=[m.avg_response_time_ms for m in source_metrics.values()],
                    name='Avg Response Time (ms)'
                )
            ])
            fig_response.update_layout(
                title='Source Response Times',
                xaxis_title='Source',
                yaxis_title='Response Time (ms)'
            )
            figures['response_times'] = fig_response
            
            # Error rates
            fig_errors = go.Figure(data=[
                go.Bar(
                    x=list(source_metrics.keys()),
                    y=[m.error_rate for m in source_metrics.values()],
                    name='Error Rate'
                )
            ])
            fig_errors.update_layout(
                title='Source Error Rates',
                xaxis_title='Source',
                yaxis_title='Error Rate'
            )
            figures['error_rates'] = fig_errors
            
            # Throughput
            fig_throughput = go.Figure(data=[
                go.Bar(
                    x=list(source_metrics.keys()),
                    y=[m.throughput_qps for m in source_metrics.values()],
                    name='Throughput (QPS)'
                )
            ])
            fig_throughput.update_layout(
                title='Source Throughput',
                xaxis_title='Source',
                yaxis_title='Queries per Second'
            )
            figures['throughput'] = fig_throughput
            
            # Health status
            health = self.monitor.get_source_health()
            status_colors = {
                'healthy': 'green',
                'degraded': 'yellow',
                'unhealthy': 'red'
            }
            
            fig_health = go.Figure(data=[
                go.Indicator(
                    mode="color",
                    value=1,
                    title={"text": source},
                    number={"prefix": status},
                    delta={"position": "top"},
                    domain={"row": i, "column": 0}
                )
                for i, (source, status) in enumerate(health.items())
            ])
            
            fig_health.update_layout(
                title='Source Health Status',
                grid={"rows": len(health), "columns": 1}
            )
            figures['health'] = fig_health
            
            return {
                'figures': figures,
                'summary': self._create_source_summary(source_metrics)
            }
        except Exception as e:
            self.logger.error(f"Error creating source dashboard: {e}")
            return {'error': str(e)}
    
    def create_alert_dashboard(self,
                             hours: int = 24) -> Dict[str, Any]:
        """Create alert monitoring dashboard."""
        try:
            # Get alert stats
            stats = self.alert_manager.get_alert_stats(hours=hours)
            if not stats:
                return {
                    'error': 'No alert data available'
                }
            
            figures = {}
            
            # Alert severity distribution
            severity_data = stats['alerts_by_severity']
            fig_severity = go.Figure(data=[
                go.Pie(
                    labels=list(severity_data.keys()),
                    values=list(severity_data.values()),
                    hole=.3
                )
            ])
            fig_severity.update_layout(title='Alert Severity Distribution')
            figures['severity'] = fig_severity
            
            # Alert type distribution
            type_data = stats['alerts_by_type']
            fig_type = go.Figure(data=[
                go.Pie(
                    labels=list(type_data.keys()),
                    values=list(type_data.values()),
                    hole=.3
                )
            ])
            fig_type.update_layout(title='Alert Type Distribution')
            figures['type'] = fig_type
            
            # Active alerts timeline
            active_alerts = self.alert_manager.get_active_alerts()
            if active_alerts:
                fig_timeline = go.Figure(data=[
                    go.Scatter(
                        x=[a.timestamp for a in active_alerts],
                        y=[a.severity.value for a in active_alerts],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color=['red' if a.severity == AlertSeverity.CRITICAL
                                  else 'orange' if a.severity == AlertSeverity.ERROR
                                  else 'yellow' if a.severity == AlertSeverity.WARNING
                                  else 'blue'
                                  for a in active_alerts]
                        ),
                        text=[a.message for a in active_alerts]
                    )
                ])
                fig_timeline.update_layout(
                    title='Active Alerts Timeline',
                    xaxis_title='Time',
                    yaxis_title='Severity'
                )
                figures['timeline'] = fig_timeline
            
            return {
                'figures': figures,
                'summary': stats
            }
        except Exception as e:
            self.logger.error(f"Error creating alert dashboard: {e}")
            return {'error': str(e)}
    
    def _create_summary(self,
                       metrics: List[QueryMetrics]) -> Dict[str, Any]:
        """Create performance summary statistics."""
        try:
            if not metrics:
                return {}
            
            exec_times = [m.execution_time_ms for m in metrics if m.execution_time_ms]
            return {
                'total_queries': len(metrics),
                'avg_execution_time_ms': np.mean(exec_times) if exec_times else 0,
                'p95_execution_time_ms': np.percentile(exec_times, 95) if exec_times else 0,
                'total_errors': sum(m.error_count for m in metrics),
                'avg_cpu_usage': np.mean([m.cpu_usage_percent for m in metrics]),
                'avg_memory_usage_mb': np.mean([m.memory_usage_mb for m in metrics]),
                'total_cache_hits': sum(m.cache_hits for m in metrics),
                'total_cache_misses': sum(m.cache_misses for m in metrics)
            }
        except Exception as e:
            self.logger.error(f"Error creating summary: {e}")
            return {}
    
    def _create_source_summary(self,
                             source_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Create source performance summary."""
        try:
            if not source_metrics:
                return {}
            
            return {
                'total_sources': len(source_metrics),
                'avg_response_time_ms': np.mean([
                    m.avg_response_time_ms
                    for m in source_metrics.values()
                ]),
                'total_throughput_qps': sum(
                    m.throughput_qps for m in source_metrics.values()
                ),
                'avg_error_rate': np.mean([
                    m.error_rate
                    for m in source_metrics.values()
                ]),
                'total_active_connections': sum(
                    m.active_connections
                    for m in source_metrics.values()
                )
            }
        except Exception as e:
            self.logger.error(f"Error creating source summary: {e}")
            return {} 