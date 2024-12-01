from typing import Dict, Any, List, Optional
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MetricsVisualizer:
    """Visualizes cluster metrics and performance data"""
    
    def __init__(self):
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        self.node_metrics: Dict[str, pd.DataFrame] = {}
        self.cluster_metrics: pd.DataFrame = pd.DataFrame()
        
    def add_metrics(self, node_id: str,
                   metrics: Dict[str, Any],
                   timestamp: Optional[datetime] = None):
        """Add metrics data point"""
        if timestamp is None:
            timestamp = datetime.now()
            
        if node_id not in self.metrics_history:
            self.metrics_history[node_id] = []
            
        metrics_point = metrics.copy()
        metrics_point['timestamp'] = timestamp
        self.metrics_history[node_id].append(metrics_point)
        
        # Update DataFrames
        self._update_dataframes()
        
    def plot_node_metrics(self, output_path: str,
                         node_id: str,
                         time_range: Optional[timedelta] = None):
        """Generate node metrics visualization"""
        if node_id not in self.node_metrics:
            return
            
        df = self.node_metrics[node_id]
        if time_range:
            cutoff = datetime.now() - time_range
            df = df[df.index >= cutoff]
            
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Resource Usage', 'IO Metrics', 'Partition Count'),
            vertical_spacing=0.1
        )
        
        # Resource usage
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['cpu_usage'],
                name='CPU Usage',
                line=dict(color='#2ecc71')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['memory_usage'],
                name='Memory Usage',
                line=dict(color='#3498db')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['disk_usage'],
                name='Disk Usage',
                line=dict(color='#e74c3c')
            ),
            row=1, col=1
        )
        
        # IO metrics
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['network_io'],
                name='Network IO',
                line=dict(color='#9b59b6')
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['iops'],
                name='IOPS',
                line=dict(color='#f1c40f')
            ),
            row=2, col=1
        )
        
        # Partition count
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['partition_count'],
                name='Partitions',
                line=dict(color='#1abc9c')
            ),
            row=3, col=1
        )
        
        # Update layout
        fig.update_layout(
            height=900,
            title=f"Node Metrics: {node_id}",
            showlegend=True,
            hovermode='x unified'
        )
        
        # Update y-axes
        fig.update_yaxes(title_text="Percentage", row=1, col=1)
        fig.update_yaxes(title_text="Operations/s", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=3, col=1)
        
        # Save plot
        fig.write_html(output_path)
        
    def plot_cluster_overview(self, output_path: str,
                            time_range: Optional[timedelta] = None):
        """Generate cluster overview visualization"""
        df = self.cluster_metrics
        if time_range:
            cutoff = datetime.now() - time_range
            df = df[df.index >= cutoff]
            
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Average Resource Usage',
                'Node Status Distribution',
                'Partition Distribution',
                'Network Traffic'
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.1
        )
        
        # Average resource usage
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['avg_cpu_usage'],
                name='Avg CPU',
                line=dict(color='#2ecc71')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['avg_memory_usage'],
                name='Avg Memory',
                line=dict(color='#3498db')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['avg_disk_usage'],
                name='Avg Disk',
                line=dict(color='#e74c3c')
            ),
            row=1, col=1
        )
        
        # Node status distribution
        latest = df.iloc[-1]
        fig.add_trace(
            go.Pie(
                labels=['Active', 'Degraded', 'Unhealthy'],
                values=[
                    latest['active_nodes'],
                    latest['degraded_nodes'],
                    latest['unhealthy_nodes']
                ],
                marker=dict(colors=['#2ecc71', '#f1c40f', '#e74c3c'])
            ),
            row=1, col=2
        )
        
        # Partition distribution
        fig.add_trace(
            go.Box(
                y=df['partitions_per_node'],
                name='Partitions per Node',
                marker=dict(color='#1abc9c')
            ),
            row=2, col=1
        )
        
        # Network traffic
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df['total_network_io'],
                name='Network Traffic',
                line=dict(color='#9b59b6')
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=800,
            title="Cluster Overview",
            showlegend=True,
            hovermode='x unified'
        )
        
        # Save plot
        fig.write_html(output_path)
        
    def plot_heatmap(self, output_path: str):
        """Generate node load heatmap"""
        # Prepare data
        nodes = list(self.node_metrics.keys())
        metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']
        
        data = []
        for metric in metrics:
            row = []
            for node_id in nodes:
                df = self.node_metrics[node_id]
                row.append(df[metric].mean())
            data.append(row)
            
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=nodes,
            y=metrics,
            colorscale='RdYlGn_r'
        ))
        
        fig.update_layout(
            title="Node Load Heatmap",
            xaxis_title="Node ID",
            yaxis_title="Metric",
            height=400
        )
        
        # Save plot
        fig.write_html(output_path)
        
    def export_metrics(self, output_path: str):
        """Export metrics data as CSV"""
        # Prepare data
        data = []
        for node_id, metrics_list in self.metrics_history.items():
            for metrics in metrics_list:
                row = {
                    'node_id': node_id,
                    'timestamp': metrics['timestamp']
                }
                row.update(metrics)
                data.append(row)
                
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        
    def _update_dataframes(self):
        """Update metrics DataFrames"""
        # Update node metrics
        for node_id, metrics_list in self.metrics_history.items():
            df = pd.DataFrame(metrics_list)
            df.set_index('timestamp', inplace=True)
            self.node_metrics[node_id] = df
            
        # Update cluster metrics
        cluster_data = []
        timestamps = set()
        
        for metrics_list in self.metrics_history.values():
            for metrics in metrics_list:
                timestamps.add(metrics['timestamp'])
                
        for timestamp in sorted(timestamps):
            metrics_at_time = []
            for metrics_list in self.metrics_history.values():
                for metrics in metrics_list:
                    if metrics['timestamp'] == timestamp:
                        metrics_at_time.append(metrics)
                        
            if metrics_at_time:
                cluster_metrics = {
                    'timestamp': timestamp,
                    'avg_cpu_usage': np.mean([m['cpu_usage'] for m in metrics_at_time]),
                    'avg_memory_usage': np.mean([m['memory_usage'] for m in metrics_at_time]),
                    'avg_disk_usage': np.mean([m['disk_usage'] for m in metrics_at_time]),
                    'total_network_io': sum(m['network_io'] for m in metrics_at_time),
                    'active_nodes': sum(1 for m in metrics_at_time if m.get('status') == 'active'),
                    'degraded_nodes': sum(1 for m in metrics_at_time if m.get('status') == 'degraded'),
                    'unhealthy_nodes': sum(1 for m in metrics_at_time if m.get('status') == 'unhealthy'),
                    'partitions_per_node': [len(m.get('partitions', [])) for m in metrics_at_time]
                }
                cluster_data.append(cluster_metrics)
                
        if cluster_data:
            df = pd.DataFrame(cluster_data)
            df.set_index('timestamp', inplace=True)
            self.cluster_metrics = df
            
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        if self.cluster_metrics.empty:
            return {}
            
        latest = self.cluster_metrics.iloc[-1]
        return {
            'avg_cpu_usage': latest['avg_cpu_usage'],
            'avg_memory_usage': latest['avg_memory_usage'],
            'avg_disk_usage': latest['avg_disk_usage'],
            'total_network_io': latest['total_network_io'],
            'active_nodes': latest['active_nodes'],
            'degraded_nodes': latest['degraded_nodes'],
            'unhealthy_nodes': latest['unhealthy_nodes'],
            'total_nodes': latest['active_nodes'] + latest['degraded_nodes'] + latest['unhealthy_nodes'],
            'avg_partitions_per_node': np.mean(latest['partitions_per_node'])
        } 