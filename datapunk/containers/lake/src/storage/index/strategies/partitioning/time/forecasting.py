from typing import List, Dict, Any, Optional, Union
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import xgboost as xgb
from datetime import datetime, timedelta
from .time_analysis import TimeSeriesAnalyzer

class TimeSeriesForecaster:
    """Advanced time series forecasting with multiple models and automatic selection"""
    
    def __init__(self, analyzer: TimeSeriesAnalyzer):
        self.analyzer = analyzer
        self.models = {}
        self.model_performance = {}
        self.best_model = None
        
    def forecast(self, data: pd.Series,
                timestamp_column: str,
                value_column: str,
                horizon: int,
                confidence_interval: float = 0.95) -> Dict[str, Any]:
        """Generate forecasts using the best-suited model"""
        
        # Analyze time series characteristics
        analysis = self.analyzer.analyze_time_series(data, timestamp_column, value_column)
        
        # Select and train best model
        model_type = self._select_best_model(analysis)
        predictions = self._generate_forecast(
            data, timestamp_column, value_column, 
            horizon, model_type, confidence_interval
        )
        
        return {
            'forecast': predictions['forecast'],
            'confidence_intervals': predictions['confidence_intervals'],
            'model_type': model_type,
            'model_metrics': self.model_performance.get(model_type, {}),
            'analysis': analysis
        }
        
    def _select_best_model(self, analysis: Dict[str, Any]) -> str:
        """Select the best model based on time series characteristics"""
        
        # Decision logic for model selection
        if analysis['seasonality']['has_seasonality']:
            if len(analysis['seasonality']['seasonal_periods']) > 1:
                return 'prophet'  # Prophet handles multiple seasonalities well
            else:
                return 'holtwinters'  # Good for single seasonality
                
        if not analysis['trends']['is_stationary']:
            if analysis['basic_stats']['std'] > analysis['basic_stats']['mean'] * 0.5:
                return 'arima'  # ARIMA for non-stationary with high variance
            else:
                return 'xgboost'  # XGBoost for complex non-linear patterns
                
        return 'randomforest'  # Default to RandomForest for other cases
        
    def _generate_forecast(self,
                         data: pd.Series,
                         timestamp_column: str,
                         value_column: str,
                         horizon: int,
                         model_type: str,
                         confidence_interval: float) -> Dict[str, Any]:
        """Generate forecasts using specified model"""
        
        if model_type == 'prophet':
            return self._prophet_forecast(
                data, timestamp_column, value_column, 
                horizon, confidence_interval
            )
        elif model_type == 'holtwinters':
            return self._holtwinters_forecast(
                data, timestamp_column, value_column, 
                horizon, confidence_interval
            )
        elif model_type == 'arima':
            return self._arima_forecast(
                data, timestamp_column, value_column, 
                horizon, confidence_interval
            )
        elif model_type == 'xgboost':
            return self._xgboost_forecast(
                data, timestamp_column, value_column, 
                horizon, confidence_interval
            )
        else:
            return self._randomforest_forecast(
                data, timestamp_column, value_column, 
                horizon, confidence_interval
            )
            
    def _prophet_forecast(self, data: pd.Series, 
                         timestamp_column: str,
                         value_column: str,
                         horizon: int,
                         confidence_interval: float) -> Dict[str, Any]:
        """Generate forecast using Facebook Prophet"""
        
        # Prepare data for Prophet
        df = pd.DataFrame({
            'ds': pd.to_datetime(data[timestamp_column]),
            'y': data[value_column]
        })
        
        # Initialize and train model
        model = Prophet(interval_width=confidence_interval)
        model.fit(df)
        
        # Generate future dates
        future = model.make_future_dataframe(periods=horizon)
        forecast = model.predict(future)
        
        return {
            'forecast': forecast['yhat'].tail(horizon).values,
            'confidence_intervals': {
                'lower': forecast['yhat_lower'].tail(horizon).values,
                'upper': forecast['yhat_upper'].tail(horizon).values
            }
        }
        
    def _holtwinters_forecast(self, data: pd.Series,
                            timestamp_column: str,
                            value_column: str,
                            horizon: int,
                            confidence_interval: float) -> Dict[str, Any]:
        """Generate forecast using Holt-Winters"""
        
        # Fit model
        model = ExponentialSmoothing(
            data[value_column],
            seasonal_periods=self._get_seasonal_period(data[timestamp_column]),
            trend='add',
            seasonal='add'
        ).fit()
        
        # Generate forecast
        forecast = model.forecast(horizon)
        conf_int = model.get_prediction(start=len(data), end=len(data)+horizon-1).conf_int(
            alpha=1-confidence_interval
        )
        
        return {
            'forecast': forecast.values,
            'confidence_intervals': {
                'lower': conf_int.iloc[:, 0].values,
                'upper': conf_int.iloc[:, 1].values
            }
        }
        
    def _arima_forecast(self, data: pd.Series,
                       timestamp_column: str,
                       value_column: str,
                       horizon: int,
                       confidence_interval: float) -> Dict[str, Any]:
        """Generate forecast using ARIMA"""
        
        # Fit model
        model = ARIMA(data[value_column], order=(1,1,1)).fit()
        
        # Generate forecast
        forecast = model.forecast(horizon)
        conf_int = model.get_forecast(horizon).conf_int(alpha=1-confidence_interval)
        
        return {
            'forecast': forecast.values,
            'confidence_intervals': {
                'lower': conf_int.iloc[:, 0].values,
                'upper': conf_int.iloc[:, 1].values
            }
        }
        
    def _xgboost_forecast(self, data: pd.Series,
                         timestamp_column: str,
                         value_column: str,
                         horizon: int,
                         confidence_interval: float) -> Dict[str, Any]:
        """Generate forecast using XGBoost"""
        
        # Prepare features
        X, y = self._create_features(data[timestamp_column], data[value_column])
        
        # Train model
        model = xgb.XGBRegressor(objective='reg:squarederror')
        model.fit(X, y)
        
        # Generate future features and forecast
        future_features = self._create_future_features(
            data[timestamp_column].iloc[-1], horizon
        )
        forecast = model.predict(future_features)
        
        # Calculate confidence intervals using quantile regression
        lower_model = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=(1-confidence_interval)/2)
        upper_model = xgb.XGBRegressor(objective='reg:quantileerror', quantile_alpha=(1+confidence_interval)/2)
        
        lower_model.fit(X, y)
        upper_model.fit(X, y)
        
        return {
            'forecast': forecast,
            'confidence_intervals': {
                'lower': lower_model.predict(future_features),
                'upper': upper_model.predict(future_features)
            }
        }
        
    def _randomforest_forecast(self, data: pd.Series,
                             timestamp_column: str,
                             value_column: str,
                             horizon: int,
                             confidence_interval: float) -> Dict[str, Any]:
        """Generate forecast using Random Forest"""
        
        # Prepare features
        X, y = self._create_features(data[timestamp_column], data[value_column])
        
        # Train model
        model = RandomForestRegressor(n_estimators=100)
        model.fit(X, y)
        
        # Generate future features and forecast
        future_features = self._create_future_features(
            data[timestamp_column].iloc[-1], horizon
        )
        forecast = model.predict(future_features)
        
        # Calculate confidence intervals using quantiles of tree predictions
        predictions = []
        for estimator in model.estimators_:
            predictions.append(estimator.predict(future_features))
        predictions = np.array(predictions)
        
        lower = np.percentile(predictions, ((1-confidence_interval)/2)*100, axis=0)
        upper = np.percentile(predictions, (1-(1-confidence_interval)/2)*100, axis=0)
        
        return {
            'forecast': forecast,
            'confidence_intervals': {
                'lower': lower,
                'upper': upper
            }
        }
        
    def _create_features(self, timestamps: pd.Series, 
                        values: pd.Series,
                        lookback: int = 30) -> tuple:
        """Create feature matrix for ML models"""
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        
        # Create lagged features
        for i in range(1, lookback + 1):
            df[f'lag_{i}'] = df['value'].shift(i)
            
        # Add time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day'] = df['timestamp'].dt.day
        df['month'] = df['timestamp'].dt.month
        df['dayofweek'] = df['timestamp'].dt.dayofweek
        
        # Drop rows with NaN (due to lagging)
        df = df.dropna()
        
        # Prepare X and y
        feature_cols = [col for col in df.columns if col not in ['timestamp', 'value']]
        X = df[feature_cols].values
        y = df['value'].values
        
        return X, y
        
    def _create_future_features(self, last_timestamp: datetime,
                              horizon: int) -> np.ndarray:
        """Create feature matrix for future predictions"""
        
        future_dates = pd.date_range(
            start=last_timestamp,
            periods=horizon + 1,
            freq='D'
        )[1:]  # Exclude start date
        
        df = pd.DataFrame({
            'timestamp': future_dates,
            'hour': future_dates.hour,
            'day': future_dates.day,
            'month': future_dates.month,
            'dayofweek': future_dates.dayofweek
        })
        
        # Add dummy lagged features (will be updated during prediction)
        for i in range(1, 31):
            df[f'lag_{i}'] = 0
            
        feature_cols = [col for col in df.columns if col != 'timestamp']
        return df[feature_cols].values
        
    def _get_seasonal_period(self, timestamps: pd.Series) -> int:
        """Determine seasonal period from timestamp frequency"""
        
        freq = pd.infer_freq(timestamps)
        if freq in ['D', 'B']:
            return 7  # Weekly seasonality
        elif freq in ['H']:
            return 24  # Daily seasonality
        elif freq in ['M', 'MS']:
            return 12  # Yearly seasonality
        return 1  # No seasonality 