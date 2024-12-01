from typing import Any, Dict, List, Optional, Union
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .monitoring import QueryMetrics
from .profiling import OperationProfile

class MetricsVisualizer:
    """Visualizes query metrics and performance data."""
    
    def create_execution_timeline(
        self,
        metrics: List[QueryMetrics]
    ) -> go.Figure:
        """Create timeline of query executions."""
        df = pd.DataFrame([
            {
                'query_id': m.query_id,
                'start_time': m.start_time,
                'end_time': m.end_time,
                'duration_ms': m.execution_time_ms,
                'memory_mb': m.memory_usage_mb
            }
            for m in metrics
        ])
        
        fig = px.timeline(
            df,
            x_start='start_time',
            x_end='end_time',
            y='query_id',
            color='memory_mb',
            title='Query Execution Timeline',
            labels={
                'memory_mb': 'Memory Usage (MB)',
                'query_id': 'Query ID'
            }
        )
        
        return fig
        
    def create_resource_usage_chart(
        self,
        metrics: List[QueryMetrics]
    ) -> go.Figure:
        """Create resource usage chart."""
        df = pd.DataFrame([
            {
                'query_id': m.query_id,
                'cpu_percent': m.cpu_usage_percent,
                'memory_mb': m.memory_usage_mb,
                'execution_time_ms': m.execution_time_ms
            }
            for m in metrics
        ])
        
        fig = go.Figure()
        
        # Add CPU usage
        fig.add_trace(go.Bar(
            name='CPU Usage (%)',
            x=df['query_id'],
            y=df['cpu_percent'],
            marker_color='blue'
        ))
        
        # Add memory usage
        fig.add_trace(go.Bar(
            name='Memory Usage (MB)',
            x=df['query_id'],
            y=df['memory_mb'],
            marker_color='red'
        ))
        
        fig.update_layout(
            title='Resource Usage by Query',
            barmode='group',
            xaxis_title='Query ID',
            yaxis_title='Usage'
        )
        
        return fig
        
    def create_error_distribution(
        self,
        metrics: List[QueryMetrics]
    ) -> go.Figure:
        """Create error distribution chart."""
        error_counts = {}
        for metric in metrics:
            if metric.errors:
                for error in metric.errors:
                    error_type = error.split(':')[0]
                    error_counts[error_type] = error_counts.get(error_type, 0) + 1
                    
        fig = go.Figure(data=[
            go.Pie(
                labels=list(error_counts.keys()),
                values=list(error_counts.values()),
                title='Error Distribution'
            )
        ])
        
        return fig

class ProfileVisualizer:
    """Visualizes profiling data."""
    
    def create_operation_flamegraph(
        self,
        profiles: List[OperationProfile]
    ) -> go.Figure:
        """Create flame graph of operations."""
        def process_profile(profile: OperationProfile, level: int = 0) -> List[Dict]:
            result = [{
                'operation': profile.operation_type,
                'start': profile.start_time.timestamp(),
                'end': profile.end_time.timestamp() if profile.end_time else datetime.now().timestamp(),
                'level': level,
                'cpu_ms': profile.cpu_time_ms,
                'memory_mb': profile.memory_usage_mb
            }]
            
            if profile.children:
                for child in profile.children:
                    result.extend(process_profile(child, level + 1))
                    
            return result
            
        data = []
        for profile in profiles:
            data.extend(process_profile(profile))
            
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        for level in df['level'].unique():
            level_data = df[df['level'] == level]
            fig.add_trace(go.Bar(
                name=f'Level {level}',
                x=level_data['end'] - level_data['start'],
                y=level_data['operation'],
                orientation='h',
                base=level_data['start'],
                marker=dict(
                    color=level_data['cpu_ms'],
                    colorscale='Viridis'
                )
            ))
            
        fig.update_layout(
            title='Operation Flame Graph',
            barmode='stack',
            xaxis_title='Time',
            yaxis_title='Operation',
            showlegend=True
        )
        
        return fig
        
    def create_bottleneck_analysis(
        self,
        profiles: List[OperationProfile]
    ) -> go.Figure:
        """Create bottleneck analysis visualization."""
        operations = {}
        
        for profile in profiles:
            if profile.operation_type not in operations:
                operations[profile.operation_type] = {
                    'count': 0,
                    'total_cpu': 0,
                    'total_memory': 0,
                    'total_io': 0
                }
                
            op_stats = operations[profile.operation_type]
            op_stats['count'] += 1
            op_stats['total_cpu'] += profile.cpu_time_ms
            op_stats['total_memory'] += profile.memory_usage_mb
            op_stats['total_io'] += profile.io_operations
            
        df = pd.DataFrame([
            {
                'operation': op,
                'avg_cpu': stats['total_cpu'] / stats['count'],
                'avg_memory': stats['total_memory'] / stats['count'],
                'avg_io': stats['total_io'] / stats['count']
            }
            for op, stats in operations.items()
        ])
        
        fig = go.Figure()
        
        # Add traces for each metric
        fig.add_trace(go.Bar(
            name='Avg CPU Time (ms)',
            x=df['operation'],
            y=df['avg_cpu']
        ))
        
        fig.add_trace(go.Bar(
            name='Avg Memory (MB)',
            x=df['operation'],
            y=df['avg_memory']
        ))
        
        fig.add_trace(go.Bar(
            name='Avg IO Operations',
            x=df['operation'],
            y=df['avg_io']
        ))
        
        fig.update_layout(
            title='Operation Resource Usage Analysis',
            barmode='group',
            xaxis_title='Operation Type',
            yaxis_title='Average Usage'
        )
        
        return fig
        
    def create_performance_trend(
        self,
        profiles: List[OperationProfile]
    ) -> go.Figure:
        """Create performance trend visualization."""
        df = pd.DataFrame([
            {
                'operation': p.operation_type,
                'timestamp': p.start_time,
                'duration_ms': (p.end_time - p.start_time).total_seconds() * 1000 if p.end_time else 0,
                'cpu_ms': p.cpu_time_ms,
                'memory_mb': p.memory_usage_mb
            }
            for p in profiles
        ])
        
        fig = go.Figure()
        
        # Add traces for each metric
        fig.add_trace(go.Scatter(
            name='Duration (ms)',
            x=df['timestamp'],
            y=df['duration_ms'],
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            name='CPU Time (ms)',
            x=df['timestamp'],
            y=df['cpu_ms'],
            mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            name='Memory (MB)',
            x=df['timestamp'],
            y=df['memory_mb'],
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Performance Trends Over Time',
            xaxis_title='Time',
            yaxis_title='Metrics',
            hovermode='x unified'
        )
        
        return fig

class DashboardGenerator:
    """Generates comprehensive performance dashboards."""
    
    def __init__(self):
        self.metrics_viz = MetricsVisualizer()
        self.profile_viz = ProfileVisualizer()
        
    def create_performance_dashboard(
        self,
        metrics: List[QueryMetrics],
        profiles: List[OperationProfile]
    ) -> Dict[str, go.Figure]:
        """Create a complete performance dashboard."""
        return {
            'execution_timeline': self.metrics_viz.create_execution_timeline(metrics),
            'resource_usage': self.metrics_viz.create_resource_usage_chart(metrics),
            'error_distribution': self.metrics_viz.create_error_distribution(metrics),
            'flamegraph': self.profile_viz.create_operation_flamegraph(profiles),
            'bottlenecks': self.profile_viz.create_bottleneck_analysis(profiles),
            'performance_trend': self.profile_viz.create_performance_trend(profiles)
        }
        
    def save_dashboard(
        self,
        dashboard: Dict[str, go.Figure],
        output_dir: str
    ) -> None:
        """Save dashboard figures to files."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        for name, fig in dashboard.items():
            fig.write_html(os.path.join(output_dir, f"{name}.html"))
            fig.write_image(os.path.join(output_dir, f"{name}.png"))
            
    def create_html_report(
        self,
        dashboard: Dict[str, go.Figure],
        output_file: str
    ) -> None:
        """Create an HTML report with all visualizations."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Dashboard</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                .dashboard-container {
                    display: grid;
                    grid-template-columns: repeat(2, 1fr);
                    gap: 20px;
                    padding: 20px;
                }
                .chart-container {
                    border: 1px solid #ddd;
                    padding: 10px;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <h1>Performance Dashboard</h1>
            <div class="dashboard-container">
        """
        
        for name, fig in dashboard.items():
            html_content += f"""
                <div class="chart-container">
                    <h2>{name.replace('_', ' ').title()}</h2>
                    <div id="{name}"></div>
                    <script>
                        var data = {fig.to_json()};
                        Plotly.newPlot('{name}', data.data, data.layout);
                    </script>
                </div>
            """
            
        html_content += """
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content) 