from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from datetime import datetime, timedelta

class TimeSeriesAnalyzer:
    def __init__(self):
        self.decomposition_cache = {}
        self.seasonality_cache = {}
        
    def analyze_time_series(self, data: pd.Series, 
                          timestamp_column: str,
                          value_column: str) -> Dict[str, Any]:
        """Perform comprehensive time series analysis"""
        df = self._prepare_time_series(data, timestamp_column, value_column)
        
        return {
            'basic_stats': self._calculate_basic_stats(df),
            'seasonality': self._detect_seasonality(df),
            'trends': self._analyze_trends(df),
            'anomalies': self._detect_anomalies(df),
            'patterns': self._identify_patterns(df)
        }
        
    def _prepare_time_series(self, data: pd.Series,
                           timestamp_column: str,
                           value_column: str) -> pd.DataFrame:
        """Prepare time series data for analysis"""
        df = pd.DataFrame(data)
        df[timestamp_column] = pd.to_datetime(df[timestamp_column])
        df = df.set_index(timestamp_column)
        df = df.sort_index()
        
        # Handle missing values
        df = df.interpolate(method='time')
        return df
        
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate basic time series statistics"""
        return {
            'mean': float(df.mean()),
            'std': float(df.std()),
            'min': float(df.min()),
            'max': float(df.max()),
            'skewness': float(stats.skew(df.values)),
            'kurtosis': float(stats.kurtosis(df.values))
        }
        
    def _detect_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect and analyze seasonality patterns"""
        # Check cache
        series_hash = hash(str(df.values.tobytes()))
        if series_hash in self.seasonality_cache:
            return self.seasonality_cache[series_hash]
            
        try:
            # Perform seasonal decomposition
            decomposition = seasonal_decompose(df, period=self._estimate_period(df))
            
            seasonality_strength = np.std(decomposition.seasonal) / np.std(df)
            
            result = {
                'has_seasonality': seasonality_strength > 0.1,
                'seasonality_strength': float(seasonality_strength),
                'seasonal_periods': self._find_seasonal_periods(decomposition.seasonal)
            }
            
            # Cache result
            self.seasonality_cache[series_hash] = result
            return result
        except:
            return {
                'has_seasonality': False,
                'seasonality_strength': 0.0,
                'seasonal_periods': []
            }
            
    def _analyze_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in the time series"""
        # Perform trend analysis using various methods
        linear_trend = np.polyfit(range(len(df)), df.values.flatten(), 1)
        
        # Check for stationarity
        adf_result = adfuller(df.values.flatten())
        
        return {
            'is_stationary': adf_result[1] < 0.05,
            'trend_direction': 'increasing' if linear_trend[0] > 0 else 'decreasing',
            'trend_strength': float(abs(linear_trend[0])),
            'confidence': float(1 - adf_result[1])
        }
        
    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect anomalies in the time series"""
        # Calculate rolling statistics
        rolling_mean = df.rolling(window=7).mean()
        rolling_std = df.rolling(window=7).std()
        
        # Z-score based anomaly detection
        z_scores = (df - rolling_mean) / rolling_std
        anomalies = []
        
        for timestamp, z_score in z_scores.items():
            if abs(z_score) > 3:  # 3 sigma rule
                anomalies.append({
                    'timestamp': timestamp.isoformat(),
                    'value': float(df.loc[timestamp]),
                    'z_score': float(z_score),
                    'severity': 'high' if abs(z_score) > 5 else 'medium'
                })
                
        return anomalies
        
    def _identify_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify common patterns in the time series"""
        patterns = []
        
        # Detect level shifts
        rolling_mean = df.rolling(window=30).mean()
        shifts = (rolling_mean - rolling_mean.shift(1)).abs()
        significant_shifts = shifts[shifts > shifts.std() * 2]
        
        for timestamp, shift in significant_shifts.items():
            patterns.append({
                'type': 'level_shift',
                'timestamp': timestamp.isoformat(),
                'magnitude': float(shift)
            })
            
        # Detect cyclic patterns
        if len(df) >= 60:  # Need sufficient data for cycle detection
            autocorr = pd.Series(df.values.flatten()).autocorr(lag=30)
            if abs(autocorr) > 0.7:
                patterns.append({
                    'type': 'cyclic',
                    'period': 30,
                    'strength': float(abs(autocorr))
                })
                
        return patterns
        
    def _estimate_period(self, df: pd.DataFrame) -> int:
        """Estimate the seasonal period of the time series"""
        # Use autocorrelation to estimate period
        n = len(df)
        if n < 4:
            return 1
            
        max_period = min(n // 2, 365)  # Maximum period to check
        autocorr = [pd.Series(df.values.flatten()).autocorr(lag=i) 
                   for i in range(1, max_period + 1)]
        
        # Find peaks in autocorrelation
        peaks = []
        for i in range(1, len(autocorr) - 1):
            if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                peaks.append((i + 1, autocorr[i]))
                
        if not peaks:
            return 1
            
        # Return the period with highest autocorrelation
        return max(peaks, key=lambda x: x[1])[0]
        
    def _find_seasonal_periods(self, seasonal: pd.Series) -> List[int]:
        """Find multiple seasonal periods in the decomposed seasonal component"""
        n = len(seasonal)
        if n < 4:
            return []
            
        # Calculate autocorrelation for different lags
        max_lag = min(n // 2, 365)
        autocorr = [pd.Series(seasonal).autocorr(lag=i) 
                   for i in range(1, max_lag + 1)]
        
        # Find significant peaks
        peaks = []
        threshold = 0.3  # Correlation threshold
        
        for i in range(1, len(autocorr) - 1):
            if (autocorr[i] > threshold and 
                autocorr[i] > autocorr[i-1] and 
                autocorr[i] > autocorr[i+1]):
                peaks.append(i + 1)
                
        return sorted(peaks) 