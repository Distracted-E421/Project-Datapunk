from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import pandas as pd
from enum import Enum

from .stats import (
    IndexStats,
    StatisticsStore,
    StatisticsManager
)

class TrendType(Enum):
    """Types of trends that can be analyzed."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    FLUCTUATING = "fluctuating"
    CYCLIC = "cyclic"
    ANOMALOUS = "anomalous"

@dataclass
class Seasonality:
    """Detected seasonality in data."""
    period: int  # Period length in hours
    strength: float  # Strength of seasonality (0-1)
    peaks: List[datetime]  # Peak times
    troughs: List[datetime]  # Trough times

@dataclass
class Anomaly:
    """Detected anomaly in data."""
    timestamp: datetime
    value: float
    expected_value: float
    deviation: float  # Number of standard deviations
    metric: str

@dataclass
class Forecast:
    """Forecasted values."""
    timestamps: List[datetime]
    values: List[float]
    confidence_lower: List[float]
    confidence_upper: List[float]
    model_type: str

@dataclass
class TrendAnalysis:
    """Complete trend analysis results."""
    trend_type: TrendType
    slope: float  # Rate of change
    r_squared: float  # Goodness of fit
    seasonality: Optional[Seasonality]
    anomalies: List[Anomaly]
    forecast: Optional[Forecast]
    change_points: List[datetime]  # Points where trend changes significantly
    correlation_matrix: Dict[str, Dict[str, float]]

class TrendAnalyzer:
    """Advanced trend analysis for index statistics."""
    
    def __init__(self, store: StatisticsStore):
        self.store = store
        
    def analyze_performance_trends(
        self,
        index_name: str,
        days: int = 30
    ) -> TrendAnalysis:
        """Analyze performance-related trends."""
        history = self._get_history(index_name, days)
        if not history:
            return None
            
        # Extract time series
        timestamps = [stats.created_at for stats in history]
        read_times = [stats.usage.avg_read_time_ms for stats in history]
        write_times = [stats.usage.avg_write_time_ms for stats in history]
        
        # Create DataFrame for analysis
        df = pd.DataFrame({
            'timestamp': timestamps,
            'read_time': read_times,
            'write_time': write_times
        })
        
        # Analyze main trend
        trend_type = self._determine_trend_type(df['read_time'])
        slope, r_squared = self._calculate_trend_metrics(df['read_time'])
        
        # Detect seasonality
        seasonality = self._detect_seasonality(df)
        
        # Detect anomalies
        anomalies = self._detect_anomalies(df)
        
        # Generate forecast
        forecast = self._generate_forecast(df)
        
        # Find change points
        change_points = self._detect_change_points(df)
        
        # Calculate correlations
        correlation_matrix = df.corr().to_dict()
        
        return TrendAnalysis(
            trend_type=trend_type,
            slope=slope,
            r_squared=r_squared,
            seasonality=seasonality,
            anomalies=anomalies,
            forecast=forecast,
            change_points=change_points,
            correlation_matrix=correlation_matrix
        )
        
    def analyze_growth_patterns(
        self,
        index_name: str,
        days: int = 30
    ) -> TrendAnalysis:
        """Analyze index growth patterns."""
        history = self._get_history(index_name, days)
        if not history:
            return None
            
        # Extract size metrics
        df = pd.DataFrame({
            'timestamp': [stats.created_at for stats in history],
            'entries': [stats.size.total_entries for stats in history],
            'size_bytes': [stats.size.size_bytes for stats in history],
            'fragmentation': [stats.size.fragmentation_ratio for stats in history]
        })
        
        # Analyze growth trend
        trend_type = self._determine_trend_type(df['entries'])
        slope, r_squared = self._calculate_trend_metrics(df['entries'])
        
        # Look for growth patterns
        seasonality = self._detect_seasonality(df)
        anomalies = self._detect_anomalies(df)
        forecast = self._generate_forecast(df)
        change_points = self._detect_change_points(df)
        
        return TrendAnalysis(
            trend_type=trend_type,
            slope=slope,
            r_squared=r_squared,
            seasonality=seasonality,
            anomalies=anomalies,
            forecast=forecast,
            change_points=change_points,
            correlation_matrix=df.corr().to_dict()
        )
        
    def analyze_condition_effectiveness(
        self,
        index_name: str,
        days: int = 30
    ) -> TrendAnalysis:
        """Analyze condition effectiveness trends."""
        history = self._get_history(index_name, days)
        if not history or not all(h.condition for h in history):
            return None
            
        # Extract condition metrics
        df = pd.DataFrame({
            'timestamp': [stats.created_at for stats in history],
            'selectivity': [stats.condition.selectivity for stats in history],
            'false_positives': [
                stats.condition.false_positive_rate for stats in history
            ],
            'eval_time': [
                stats.condition.evaluation_time_ms for stats in history
            ]
        })
        
        trend_type = self._determine_trend_type(df['false_positives'])
        slope, r_squared = self._calculate_trend_metrics(df['false_positives'])
        
        return TrendAnalysis(
            trend_type=trend_type,
            slope=slope,
            r_squared=r_squared,
            seasonality=self._detect_seasonality(df),
            anomalies=self._detect_anomalies(df),
            forecast=self._generate_forecast(df),
            change_points=self._detect_change_points(df),
            correlation_matrix=df.corr().to_dict()
        )
        
    def _get_history(
        self,
        index_name: str,
        days: int
    ) -> List[IndexStats]:
        """Get historical statistics."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        return self.store.get_stats_history(index_name, start_time, end_time)
        
    def _determine_trend_type(self, series: pd.Series) -> TrendType:
        """Determine the type of trend in a time series."""
        # Calculate basic statistics
        mean = series.mean()
        std = series.std()
        
        # Check for cyclical pattern
        acf = pd.Series(series).autocorr()
        if abs(acf) > 0.7:
            return TrendType.CYCLIC
            
        # Check for trend
        slope, _ = self._calculate_trend_metrics(series)
        if abs(slope) < 0.01:
            return TrendType.STABLE
            
        # Check for fluctuations
        cv = std / mean if mean != 0 else float('inf')
        if cv > 0.5:
            return TrendType.FLUCTUATING
            
        return TrendType.INCREASING if slope > 0 else TrendType.DECREASING
        
    def _calculate_trend_metrics(
        self,
        series: pd.Series
    ) -> Tuple[float, float]:
        """Calculate trend slope and R-squared."""
        X = np.arange(len(series)).reshape(-1, 1)
        y = series.values.reshape(-1, 1)
        
        model = LinearRegression()
        model.fit(X, y)
        
        return model.coef_[0][0], model.score(X, y)
        
    def _detect_seasonality(self, df: pd.DataFrame) -> Optional[Seasonality]:
        """Detect seasonal patterns in the data."""
        # Requires at least 2 full cycles to detect seasonality
        if len(df) < 48:  # 2 days of hourly data
            return None
            
        # Calculate hourly averages
        df['hour'] = df['timestamp'].dt.hour
        hourly_avg = df.groupby('hour').mean()
        
        # Find peaks and troughs
        peaks = []
        troughs = []
        for col in hourly_avg.columns:
            if col != 'hour':
                peak_hours = hourly_avg[col].nlargest(3).index
                trough_hours = hourly_avg[col].nsmallest(3).index
                
                peaks.extend([
                    df['timestamp'].iloc[0].replace(hour=h)
                    for h in peak_hours
                ])
                troughs.extend([
                    df['timestamp'].iloc[0].replace(hour=h)
                    for h in trough_hours
                ])
                
        # Calculate seasonality strength
        strength = hourly_avg.std().mean() / df.std().mean()
        
        return Seasonality(
            period=24,  # Assuming daily patterns
            strength=strength,
            peaks=sorted(peaks),
            troughs=sorted(troughs)
        )
        
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        for column in df.columns:
            if column != 'timestamp':
                series = df[column]
                mean = series.mean()
                std = series.std()
                z_scores = np.abs((series - mean) / std)
                
                # Find points beyond 3 standard deviations
                anomaly_points = z_scores > 3
                
                for idx in anomaly_points[anomaly_points].index:
                    anomalies.append(Anomaly(
                        timestamp=df['timestamp'].iloc[idx],
                        value=series.iloc[idx],
                        expected_value=mean,
                        deviation=z_scores.iloc[idx],
                        metric=column
                    ))
                    
        return anomalies
        
    def _generate_forecast(self, df: pd.DataFrame) -> Optional[Forecast]:
        """Generate forecasts using time series models."""
        if len(df) < 10:  # Need sufficient data
            return None
            
        forecasts = {}
        confidence_lower = {}
        confidence_upper = {}
        
        for column in df.columns:
            if column != 'timestamp':
                # Use simple exponential smoothing
                series = df[column]
                model = stats.ExponentialSmoothing(
                    series,
                    seasonal_periods=24,
                    trend='add',
                    seasonal='add'
                ).fit()
                
                # Generate forecast
                forecast = model.forecast(steps=24)  # 24 hours ahead
                conf_int = model.get_prediction(
                    start=len(series),
                    end=len(series) + 23
                ).conf_int()
                
                forecasts[column] = forecast.values
                confidence_lower[column] = conf_int[:, 0]
                confidence_upper[column] = conf_int[:, 1]
                
        # Generate future timestamps
        last_time = df['timestamp'].iloc[-1]
        future_times = [
            last_time + timedelta(hours=i)
            for i in range(1, 25)
        ]
        
        return Forecast(
            timestamps=future_times,
            values=list(forecasts.values())[0],  # Use first metric
            confidence_lower=list(confidence_lower.values())[0],
            confidence_upper=list(confidence_upper.values())[0],
            model_type="exponential_smoothing"
        )
        
    def _detect_change_points(self, df: pd.DataFrame) -> List[datetime]:
        """Detect points where trend changes significantly."""
        change_points = []
        
        for column in df.columns:
            if column != 'timestamp':
                series = df[column]
                
                # Use rolling statistics
                rolling_mean = series.rolling(window=5).mean()
                rolling_std = series.rolling(window=5).std()
                
                # Detect significant changes
                for i in range(5, len(series)):
                    if abs(series.iloc[i] - rolling_mean.iloc[i-1]) > 2 * rolling_std.iloc[i-1]:
                        change_points.append(df['timestamp'].iloc[i])
                        
        return sorted(list(set(change_points))) 