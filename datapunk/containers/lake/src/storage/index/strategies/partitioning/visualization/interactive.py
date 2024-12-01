from typing import Dict, Any, List, Optional, Set
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import threading
import time
import json
from .topology import TopologyVisualizer
from .metrics import MetricsVisualizer
from .performance import PerformanceVisualizer
from ..distributed.coordinator import ClusterState

class InteractiveVisualizer:
    """Interactive visualization component with real-time updates"""
    
    def __init__(self, topology_viz: TopologyVisualizer,
                 metrics_viz: MetricsVisualizer,
                 performance_viz: PerformanceVisualizer,
                 update_interval: int = 5):
        self.topology_viz = topology_viz
        self.metrics_viz = metrics_viz
        self.performance_viz = performance_viz
        self.update_interval = update_interval
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()
        self._stop = False
        self._update_thread = None
        self.selected_nodes: Set[str] = set()
        self.selected_metrics: Set[str] = set()
        self.time_window = '1H'
        
    def start(self, host: str = 'localhost',
              port: int = 8050,
              debug: bool = False):
        """Start interactive visualization server"""
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
        """Stop visualization server"""
        self._stop = True
        if self._update_thread:
            self._update_thread.join()
            
    def _setup_layout(self):
        """Setup interactive dashboard layout"""
        self.app.layout = html.Div([
            # Header
            html.H1("Interactive Cluster Visualization",
                   style={'textAlign': 'center'}),
                   
            # Control Panel
            html.Div([
                # Time Range Selector
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
                
                # Node Selector
                html.Div([
                    html.Label("Select Nodes:"),
                    dcc.Dropdown(
                        id='node-selector',
                        multi=True
                    )
                ], style={'width': '400px', 'margin': '10px'}),
                
                # Metric Selector
                html.Div([
                    html.Label("Select Metrics:"),
                    dcc.Dropdown(
                        id='metric-selector',
                        options=[
                            {'label': 'CPU Usage', 'value': 'cpu_usage'},
                            {'label': 'Memory Usage', 'value': 'memory_usage'},
                            {'label': 'Disk Usage', 'value': 'disk_usage'},
                            {'label': 'Network IO', 'value': 'network_io'},
                            {'label': 'IOPS', 'value': 'iops'},
                            {'label': 'Latency', 'value': 'latency'},
                            {'label': 'Throughput', 'value': 'throughput'}
                        ],
                        value=['cpu_usage', 'memory_usage'],
                        multi=True
                    )
                ], style={'width': '400px', 'margin': '10px'})
            ], style={'display': 'flex', 'justifyContent': 'space-around'}),
            
            # Main Content
            html.Div([
                # Topology View
                html.Div([
                    html.H2("Cluster Topology"),
                    dcc.Graph(id='topology-view')
                ], style={'width': '50%'}),
                
                # Metrics View
                html.Div([
                    html.H2("Node Metrics"),
                    dcc.Graph(id='metrics-view')
                ], style={'width': '50%'})
            ], style={'display': 'flex'}),
            
            # Performance Analysis
            html.Div([
                html.H2("Performance Analysis"),
                
                # Tabs for different analyses
                dcc.Tabs([
                    dcc.Tab(label="Latency Distribution", children=[
                        dcc.Graph(id='latency-distribution')
                    ]),
                    dcc.Tab(label="Resource Correlation", children=[
                        dcc.Graph(id='resource-correlation')
                    ]),
                    dcc.Tab(label="Performance Trends", children=[
                        dcc.Graph(id='performance-trends')
                    ])
                ])
            ]),
            
            # Alerts and Anomalies
            html.Div([
                html.H2("Alerts and Anomalies"),
                html.Div(id='anomaly-alerts')
            ]),
            
            # Auto-refresh
            dcc.Interval(
                id='interval-component',
                interval=self.update_interval * 1000,
                n_intervals=0
            )
        ])
        
    def _setup_callbacks(self):
        """Setup interactive callbacks"""
        @self.app.callback(
            Output('topology-view', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value')]
        )
        def update_topology(n, selected_nodes):
            self.selected_nodes = set(selected_nodes or [])
            return self._create_topology_view()
            
        @self.app.callback(
            Output('metrics-view', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value'),
             Input('metric-selector', 'value'),
             Input('time-range', 'value')]
        )
        def update_metrics(n, nodes, metrics, time_range):
            self.selected_nodes = set(nodes or [])
            self.selected_metrics = set(metrics or [])
            self.time_window = time_range
            return self._create_metrics_view()
            
        @self.app.callback(
            Output('latency-distribution', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value')]
        )
        def update_latency_distribution(n, nodes):
            return self._create_latency_distribution()
            
        @self.app.callback(
            Output('resource-correlation', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value')]
        )
        def update_resource_correlation(n, nodes):
            return self._create_resource_correlation()
            
        @self.app.callback(
            Output('performance-trends', 'figure'),
            [Input('interval-component', 'n_intervals'),
             Input('node-selector', 'value'),
             Input('time-range', 'value')]
        )
        def update_performance_trends(n, nodes, time_range):
            return self._create_performance_trends()
            
        @self.app.callback(
            Output('anomaly-alerts', 'children'),
            [Input('interval-component', 'n_intervals')]
        )
        def update_anomaly_alerts(n):
            return self._create_anomaly_alerts()
            
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
        
    def _create_topology_view(self) -> go.Figure:
        """Create interactive topology view"""
        fig = self.topology_viz.plot_topology(
            highlight_cells=self.selected_nodes
        )
        
        # Add click events
        fig.update_traces(
            hoverinfo='text',
            hovertemplate='%{text}<extra></extra>'
        )
        
        return fig
        
    def _create_metrics_view(self) -> go.Figure:
        """Create interactive metrics view"""
        if not self.selected_nodes or not self.selected_metrics:
            return go.Figure()
            
        fig = make_subplots(
            rows=len(self.selected_metrics),
            cols=1,
            subplot_titles=[m.replace('_', ' ').title() 
                          for m in self.selected_metrics]
        )
        
        for i, metric in enumerate(self.selected_metrics, 1):
            for node_id in self.selected_nodes:
                if node_id in self.metrics_viz.node_metrics:
                    df = self.metrics_viz.node_metrics[node_id]
                    if metric in df.columns:
                        fig.add_trace(
                            go.Scatter(
                                x=df.index,
                                y=df[metric],
                                name=f"{node_id} - {metric}",
                                mode='lines+markers'
                            ),
                            row=i, col=1
                        )
                        
        fig.update_layout(
            height=300 * len(self.selected_metrics),
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
        
    def _create_latency_distribution(self) -> go.Figure:
        """Create latency distribution visualization"""
        return self.performance_viz.plot_latency_distribution(
            operations=list(self.selected_nodes)
        )
        
    def _create_resource_correlation(self) -> go.Figure:
        """Create resource correlation visualization"""
        if not self.selected_nodes:
            return go.Figure()
            
        fig = make_subplots(
            rows=len(self.selected_nodes),
            cols=1,
            subplot_titles=[f"Resource Correlation - {node}" 
                          for node in self.selected_nodes]
        )
        
        for i, node_id in enumerate(self.selected_nodes, 1):
            self.performance_viz.plot_resource_correlation(
                node_id,
                fig=fig,
                row=i,
                col=1
            )
            
        fig.update_layout(
            height=400 * len(self.selected_nodes),
            showlegend=True
        )
        
        return fig
        
    def _create_performance_trends(self) -> go.Figure:
        """Create performance trends visualization"""
        if not self.selected_nodes:
            return go.Figure()
            
        time_range = self._parse_time_range(self.time_window)
        
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=["Latency Trends", "Throughput Trends"]
        )
        
        for node_id in self.selected_nodes:
            self.performance_viz.plot_performance_trends(
                node_id,
                time_range=time_range,
                fig=fig
            )
            
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
        
    def _create_anomaly_alerts(self) -> List[html.Div]:
        """Create anomaly alerts"""
        alerts = []
        
        for node_id in self.selected_nodes:
            anomalies = self.performance_viz.analyze_performance_anomalies(
                node_id,
                threshold=2.0
            )
            
            if anomalies:
                alerts.append(html.Div([
                    html.Strong(f"Anomalies detected for {node_id}:"),
                    html.Ul([
                        html.Li(f"Anomaly at {anomaly.strftime('%Y-%m-%d %H:%M:%S')}")
                        for anomaly in anomalies
                    ])
                ]))
                
        return alerts
        
    def _parse_time_range(self, range_str: str) -> timedelta:
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
        
    def export_visualization_state(self, output_path: str):
        """Export current visualization state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'selected_nodes': list(self.selected_nodes),
            'selected_metrics': list(self.selected_metrics),
            'time_window': self.time_window,
            'topology': self.topology_viz.get_topology_metrics(),
            'performance': {
                node: self.performance_viz.get_performance_summary(node)
                for node in self.selected_nodes
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(state, f, indent=2)
            
    def import_visualization_state(self, input_path: str):
        """Import visualization state"""
        with open(input_path, 'r') as f:
            state = json.load(f)
            
        self.selected_nodes = set(state['selected_nodes'])
        self.selected_metrics = set(state['selected_metrics'])
        self.time_window = state['time_window'] 