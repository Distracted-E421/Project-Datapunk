from typing import Dict, Any, List, Optional
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
from .topology import TopologyVisualizer
from .metrics import MetricsVisualizer
from ..distributed.coordinator import ClusterState

class DashboardManager:
    """Manages real-time monitoring dashboard"""
    
    def __init__(self, topology_viz: TopologyVisualizer,
                 metrics_viz: MetricsVisualizer,
                 update_interval: int = 5):
        self.topology_viz = topology_viz
        self.metrics_viz = metrics_viz
        self.update_interval = update_interval
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()
        self._stop = False
        self._update_thread = None
        
    def start(self, host: str = 'localhost',
              port: int = 8050,
              debug: bool = False):
        """Start dashboard server"""
        self._stop = False
        self._update_thread = threading.Thread(
            target=self._update_loop,
            daemon=True
        )
        self._update_thread.start()
        
        self.app.run_server(
            host=host,
            port=port,
            debug=debug
        )
        
    def stop(self):
        """Stop dashboard server"""
        self._stop = True
        if self._update_thread:
            self._update_thread.join()
            
    def _setup_layout(self):
        """Setup dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.H1("Cluster Monitoring Dashboard",
                   style={'textAlign': 'center'}),
                   
            # Time range selector
            html.Div([
                html.Label("Time Range:"),
                dcc.Dropdown(
                    id='time-range',
                    options=[
                        {'label': '1 Hour', 'value': '1H'},
                        {'label': '6 Hours', 'value': '6H'},
                        {'label': '24 Hours', 'value': '24H'},
                        {'label': '7 Days', 'value': '7D'}
                    ],
                    value='1H'
                )
            ], style={'width': '200px', 'margin': '10px'}),
            
            # Cluster overview
            html.Div([
                html.H2("Cluster Overview"),
                dcc.Graph(id='cluster-overview')
            ]),
            
            # Node metrics
            html.Div([
                html.H2("Node Metrics"),
                html.Div([
                    html.Label("Select Node:"),
                    dcc.Dropdown(id='node-selector')
                ], style={'width': '200px', 'margin': '10px'}),
                dcc.Graph(id='node-metrics')
            ]),
            
            # Topology view
            html.Div([
                html.H2("Cluster Topology"),
                dcc.Graph(id='topology-view')
            ]),
            
            # Heatmap
            html.Div([
                html.H2("Node Load Heatmap"),
                dcc.Graph(id='load-heatmap')
            ]),
            
            # Metrics summary
            html.Div([
                html.H2("Current Metrics"),
                html.Div(id='metrics-summary')
            ]),
            
            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=self.update_interval * 1000,  # milliseconds
                n_intervals=0
            )
        ])
        
    def _setup_callbacks(self):
        """Setup dashboard callbacks"""
        @self.app.callback(
            Output('cluster-overview', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('time-range', 'value')]
        )
        def update_cluster_overview(n, time_range):
            return self._create_cluster_overview(self._get_time_range(time_range))
            
        @self.app.callback(
            Output('node-selector', 'options'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_node_options(n):
            return [{'label': node_id, 'value': node_id}
                   for node_id in self.metrics_viz.node_metrics.keys()]
                   
        @self.app.callback(
            Output('node-metrics', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value'),
             Input('time-range', 'value')]
        )
        def update_node_metrics(n, node_id, time_range):
            if not node_id:
                return go.Figure()
            return self._create_node_metrics(
                node_id,
                self._get_time_range(time_range)
            )
            
        @self.app.callback(
            Output('topology-view', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_topology(n):
            return self._create_topology_view()
            
        @self.app.callback(
            Output('load-heatmap', 'figure'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_heatmap(n):
            return self._create_heatmap()
            
        @self.app.callback(
            Output('metrics-summary', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_metrics_summary(n):
            return self._create_metrics_summary()
            
    def _update_loop(self):
        """Background loop for data updates"""
        while not self._stop:
            try:
                self._update_data()
            except Exception as e:
                print(f"Update error: {str(e)}")
                
            time.sleep(self.update_interval)
            
    def _update_data(self):
        """Update visualization data"""
        # This would integrate with your cluster state
        pass
        
    def _get_time_range(self, range_str: str) -> timedelta:
        """Convert time range string to timedelta"""
        if range_str == '1H':
            return timedelta(hours=1)
        elif range_str == '6H':
            return timedelta(hours=6)
        elif range_str == '24H':
            return timedelta(hours=24)
        elif range_str == '7D':
            return timedelta(days=7)
        return timedelta(hours=1)
        
    def _create_cluster_overview(self,
                               time_range: timedelta) -> go.Figure:
        """Create cluster overview figure"""
        return self.metrics_viz.plot_cluster_overview(time_range)
        
    def _create_node_metrics(self, node_id: str,
                           time_range: timedelta) -> go.Figure:
        """Create node metrics figure"""
        return self.metrics_viz.plot_node_metrics(node_id, time_range)
        
    def _create_topology_view(self) -> go.Figure:
        """Create topology view figure"""
        return self.topology_viz.plot_topology()
        
    def _create_heatmap(self) -> go.Figure:
        """Create load heatmap figure"""
        return self.metrics_viz.plot_heatmap()
        
    def _create_metrics_summary(self) -> List[html.Div]:
        """Create metrics summary"""
        summary = self.metrics_viz.get_metrics_summary()
        
        return [
            html.Div([
                html.Strong(f"{key}: "),
                html.Span(f"{value:.2f}" if isinstance(value, float) else str(value))
            ]) for key, value in summary.items()
        ]
        
class DashboardConfig:
    """Configuration for dashboard"""
    
    def __init__(self):
        self.update_interval = 5  # seconds
        self.retention_period = timedelta(days=7)
        self.max_points = 1000
        self.default_time_range = '1H'
        self.plot_height = 400
        self.plot_width = 800
        self.color_scheme = {
            'background': '#ffffff',
            'text': '#2c3e50',
            'primary': '#2ecc71',
            'secondary': '#3498db',
            'warning': '#f1c40f',
            'danger': '#e74c3c'
        }
        
class DashboardMetrics:
    """Metrics tracking for dashboard"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.update_count = 0
        self.error_count = 0
        self.last_update = None
        self.update_times: List[float] = []
        
    def record_update(self, duration: float):
        """Record metrics for an update"""
        self.update_count += 1
        self.last_update = datetime.now()
        self.update_times.append(duration)
        
        # Keep last 1000 update times
        if len(self.update_times) > 1000:
            self.update_times = self.update_times[-1000:]
            
    def record_error(self):
        """Record an error"""
        self.error_count += 1
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics"""
        return {
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'update_count': self.update_count,
            'error_count': self.error_count,
            'last_update': self.last_update,
            'avg_update_time': sum(self.update_times) / len(self.update_times) if self.update_times else 0,
            'max_update_time': max(self.update_times) if self.update_times else 0
        } 