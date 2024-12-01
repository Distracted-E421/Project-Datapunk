from typing import Dict, Any, List, Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

class PerformanceVisualizer:
    """Visualizes and analyzes system performance metrics"""
    
    def __init__(self):
        self.performance_data: Dict[str, pd.DataFrame] = {}
        self.anomaly_thresholds: Dict[str, float] = {}
        self.baseline_stats: Dict[str, Dict[str, float]] = {}
        
    def add_performance_data(self, operation: str,
                           metrics: Dict[str, Any],
                           timestamp: Optional[datetime] = None):
        """Add performance data point"""
        if timestamp is None:
            timestamp = datetime.now()
            
        if operation not in self.performance_data:
            self.performance_data[operation] = pd.DataFrame()
            
        metrics_point = metrics.copy()
        metrics_point['timestamp'] = timestamp
        
        df = pd.DataFrame([metrics_point])
        df.set_index('timestamp', inplace=True)
        self.performance_data[operation] = pd.concat([
            self.performance_data[operation],
            df
        ])
        
    def plot_latency_distribution(self, output_path: str,
                                operations: Optional[List[str]] = None):
        """Plot latency distribution for operations"""
        if operations is None:
            operations = list(self.performance_data.keys())
            
        fig = go.Figure()
        
        for operation in operations:
            if operation in self.performance_data:
                df = self.performance_data[operation]
                if 'latency' in df.columns:
                    fig.add_trace(go.Box(
                        y=df['latency'],
                        name=operation,
                        boxpoints='outliers'
                    ))
                    
        fig.update_layout(
            title="Operation Latency Distribution",
            yaxis_title="Latency (ms)",
            showlegend=True,
            height=600
        )
        
        fig.write_html(output_path)
        
    def plot_throughput_trends(self, output_path: str,
                             time_range: Optional[timedelta] = None,
                             window: str = '1min'):
        """Plot throughput trends over time"""
        fig = go.Figure()
        
        for operation, df in self.performance_data.items():
            if time_range:
                cutoff = datetime.now() - time_range
                df = df[df.index >= cutoff]
                
            if 'throughput' in df.columns:
                # Resample and calculate rolling average
                throughput = df['throughput'].resample(window).mean()
                
                fig.add_trace(go.Scatter(
                    x=throughput.index,
                    y=throughput.values,
                    name=operation,
                    mode='lines'
                ))
                
        fig.update_layout(
            title="Operation Throughput Trends",
            xaxis_title="Time",
            yaxis_title="Throughput (ops/sec)",
            showlegend=True,
            height=600
        )
        
        fig.write_html(output_path)
        
    def plot_resource_correlation(self, output_path: str,
                                operation: str):
        """Plot correlation between resources and performance"""
        if operation not in self.performance_data:
            return
            
        df = self.performance_data[operation]
        resource_cols = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_io']
        perf_cols = ['latency', 'throughput']
        
        # Calculate correlation matrix
        corr_matrix = df[resource_cols + perf_cols].corr()
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.columns,
            colorscale='RdBu'
        ))
        
        fig.update_layout(
            title=f"Resource-Performance Correlation: {operation}",
            height=600
        )
        
        fig.write_html(output_path)
        
    def analyze_performance_anomalies(self,
                                    operation: str,
                                    metric: str = 'latency',
                                    threshold: float = 2.0) -> List[datetime]:
        """Detect performance anomalies using statistical analysis"""
        if operation not in self.performance_data:
            return []
            
        df = self.performance_data[operation]
        if metric not in df.columns:
            return []
            
        # Calculate z-scores
        z_scores = np.abs(stats.zscore(df[metric]))
        
        # Find anomalies
        anomalies = df.index[z_scores > threshold].tolist()
        return anomalies
        
    def establish_performance_baseline(self, operation: str,
                                    window: timedelta = timedelta(hours=24)):
        """Establish performance baseline for anomaly detection"""
        if operation not in self.performance_data:
            return
            
        df = self.performance_data[operation]
        cutoff = datetime.now() - window
        baseline_df = df[df.index >= cutoff]
        
        metrics = ['latency', 'throughput']
        stats_dict = {}
        
        for metric in metrics:
            if metric in baseline_df.columns:
                stats_dict[metric] = {
                    'mean': baseline_df[metric].mean(),
                    'std': baseline_df[metric].std(),
                    'p95': baseline_df[metric].quantile(0.95),
                    'p99': baseline_df[metric].quantile(0.99)
                }
                
        self.baseline_stats[operation] = stats_dict
        
    def plot_performance_trends(self, output_path: str,
                              operation: str,
                              metrics: Optional[List[str]] = None):
        """Plot detailed performance trends"""
        if operation not in self.performance_data:
            return
            
        df = self.performance_data[operation]
        if metrics is None:
            metrics = ['latency', 'throughput']
            
        # Create subplots
        fig = make_subplots(
            rows=len(metrics),
            cols=1,
            subplot_titles=[m.capitalize() for m in metrics],
            vertical_spacing=0.1
        )
        
        for i, metric in enumerate(metrics, 1):
            if metric in df.columns:
                # Plot actual values
                fig.add_trace(
                    go.Scatter(
                        x=df.index,
                        y=df[metric],
                        name=f"Actual {metric}",
                        line=dict(color='#2ecc71')
                    ),
                    row=i, col=1
                )
                
                # Plot baseline if available
                if operation in self.baseline_stats and metric in self.baseline_stats[operation]:
                    baseline = self.baseline_stats[operation][metric]
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=[baseline['mean']] * len(df),
                            name=f"Baseline {metric}",
                            line=dict(color='#3498db', dash='dash')
                        ),
                        row=i, col=1
                    )
                    
                    # Plot confidence intervals
                    upper = baseline['mean'] + 2 * baseline['std']
                    lower = baseline['mean'] - 2 * baseline['std']
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=[upper] * len(df),
                            name='Upper bound',
                            line=dict(color='#e74c3c', dash='dot')
                        ),
                        row=i, col=1
                    )
                    
                    fig.add_trace(
                        go.Scatter(
                            x=df.index,
                            y=[lower] * len(df),
                            name='Lower bound',
                            line=dict(color='#e74c3c', dash='dot'),
                            showlegend=False
                        ),
                        row=i, col=1
                    )
                    
        fig.update_layout(
            height=200 * len(metrics),
            title=f"Performance Trends: {operation}",
            showlegend=True
        )
        
        fig.write_html(output_path)
        
    def analyze_performance_patterns(self, operation: str) -> Dict[str, Any]:
        """Analyze performance patterns and trends"""
        if operation not in self.performance_data:
            return {}
            
        df = self.performance_data[operation]
        metrics = ['latency', 'throughput']
        patterns = {}
        
        for metric in metrics:
            if metric in df.columns:
                # Basic statistics
                patterns[f"{metric}_stats"] = {
                    'mean': df[metric].mean(),
                    'std': df[metric].std(),
                    'min': df[metric].min(),
                    'max': df[metric].max(),
                    'p95': df[metric].quantile(0.95),
                    'p99': df[metric].quantile(0.99)
                }
                
                # Trend analysis
                trend = self._analyze_trend(df[metric])
                patterns[f"{metric}_trend"] = trend
                
                # Seasonality detection
                seasonality = self._detect_seasonality(df[metric])
                patterns[f"{metric}_seasonality"] = seasonality
                
        return patterns
        
    def _analyze_trend(self, series: pd.Series) -> str:
        """Analyze trend direction"""
        z = np.polyfit(range(len(series)), series, 1)
        slope = z[0]
        
        if abs(slope) < 0.001:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
            
    def _detect_seasonality(self, series: pd.Series) -> Dict[str, Any]:
        """Detect seasonality patterns"""
        # Simple seasonality detection using autocorrelation
        acf = pd.Series(series).autocorr()
        
        return {
            'autocorrelation': acf,
            'has_seasonality': abs(acf) > 0.7
        }
        
    def get_performance_summary(self, operation: str) -> Dict[str, Any]:
        """Get summary of performance metrics"""
        if operation not in self.performance_data:
            return {}
            
        df = self.performance_data[operation]
        summary = {}
        
        for metric in ['latency', 'throughput']:
            if metric in df.columns:
                recent = df[metric].iloc[-100:]  # Last 100 points
                summary[f"recent_{metric}"] = {
                    'mean': recent.mean(),
                    'std': recent.std(),
                    'trend': self._analyze_trend(recent)
                }
                
                if operation in self.baseline_stats and metric in self.baseline_stats[operation]:
                    baseline = self.baseline_stats[operation][metric]
                    deviation = (recent.mean() - baseline['mean']) / baseline['std']
                    summary[f"{metric}_baseline_deviation"] = deviation
                    
        return summary 