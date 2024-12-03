import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
from tensorflow.keras.optimizers import Adam

@dataclass
class ResourceMetrics:
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_bandwidth: float
    request_count: int

@dataclass
class ResourcePrediction:
    resource_type: str
    predicted_value: float
    confidence: float
    timestamp: datetime
    metadata: Optional[Dict] = None

class ResourcePredictor:
    def __init__(
        self,
        history_window: int = 24,  # Hours of history to consider
        forecast_window: int = 12,  # Hours to forecast
        confidence_threshold: float = 0.8,
        update_interval: int = 1  # Hours between model updates
    ):
        self.history_window = history_window
        self.forecast_window = forecast_window
        self.confidence_threshold = confidence_threshold
        self.update_interval = update_interval
        self.metrics_history: List[ResourceMetrics] = []
        self.models: Dict[str, Sequential] = {}
        self.scalers: Dict[str, MinMaxScaler] = {}
        self.last_update: Optional[datetime] = None
        self.logger = logging.getLogger(__name__)

    def add_metrics(self, metrics: ResourceMetrics) -> None:
        """Add new metrics and update models if needed."""
        self.metrics_history.append(metrics)
        self._cleanup_old_metrics()
        
        if self._should_update_models():
            self._update_models()

    def _cleanup_old_metrics(self) -> None:
        """Remove metrics older than the history window."""
        cutoff_time = datetime.now() - timedelta(hours=self.history_window)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]

    def _should_update_models(self) -> bool:
        """Check if models should be updated based on the update interval."""
        if not self.last_update:
            return True
        
        hours_since_update = (datetime.now() - self.last_update).total_seconds() / 3600
        return hours_since_update >= self.update_interval

    def _update_models(self) -> None:
        """Update prediction models with latest data."""
        if len(self.metrics_history) < self.history_window:
            self.logger.warning("Insufficient history for model update")
            return

        resource_types = ['cpu', 'memory', 'disk', 'network', 'requests']
        
        for resource_type in resource_types:
            self._train_model(resource_type)
        
        self.last_update = datetime.now()
        self.logger.info("Models updated successfully")

    def _prepare_data(self, resource_type: str) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for model training."""
        # Extract values for the resource type
        values = []
        if resource_type == 'cpu':
            values = [m.cpu_usage for m in self.metrics_history]
        elif resource_type == 'memory':
            values = [m.memory_usage for m in self.metrics_history]
        elif resource_type == 'disk':
            values = [m.disk_usage for m in self.metrics_history]
        elif resource_type == 'network':
            values = [m.network_bandwidth for m in self.metrics_history]
        elif resource_type == 'requests':
            values = [float(m.request_count) for m in self.metrics_history]

        # Scale the data
        if resource_type not in self.scalers:
            self.scalers[resource_type] = MinMaxScaler()
        
        values = np.array(values).reshape(-1, 1)
        scaled_values = self.scalers[resource_type].fit_transform(values)

        # Create sequences for LSTM
        X, y = [], []
        for i in range(len(scaled_values) - self.forecast_window):
            X.append(scaled_values[i:i + self.forecast_window])
            y.append(scaled_values[i + self.forecast_window])
        
        return np.array(X), np.array(y)

    def _train_model(self, resource_type: str) -> None:
        """Train LSTM model for a specific resource type."""
        X, y = self._prepare_data(resource_type)
        
        if len(X) < 2:  # Need at least 2 samples for train/test split
            return

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Create and compile model
        model = Sequential([
            LSTM(50, activation='relu', input_shape=(self.forecast_window, 1)),
            Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

        # Train model
        model.fit(
            X_train, y_train,
            epochs=50,
            batch_size=32,
            validation_data=(X_test, y_test),
            verbose=0
        )

        self.models[resource_type] = model

    def predict_resource_usage(
        self,
        resource_type: str,
        hours_ahead: int
    ) -> List[ResourcePrediction]:
        """Predict resource usage for specified hours ahead."""
        if resource_type not in self.models:
            raise ValueError(f"No model available for {resource_type}")

        if len(self.metrics_history) < self.forecast_window:
            raise ValueError("Insufficient history for prediction")

        # Prepare input data
        recent_values = []
        if resource_type == 'cpu':
            recent_values = [m.cpu_usage for m in self.metrics_history[-self.forecast_window:]]
        elif resource_type == 'memory':
            recent_values = [m.memory_usage for m in self.metrics_history[-self.forecast_window:]]
        elif resource_type == 'disk':
            recent_values = [m.disk_usage for m in self.metrics_history[-self.forecast_window:]]
        elif resource_type == 'network':
            recent_values = [m.network_bandwidth for m in self.metrics_history[-self.forecast_window:]]
        elif resource_type == 'requests':
            recent_values = [float(m.request_count) for m in self.metrics_history[-self.forecast_window:]]

        # Scale input
        scaled_input = self.scalers[resource_type].transform(
            np.array(recent_values).reshape(-1, 1)
        )
        
        # Make predictions
        predictions = []
        current_input = scaled_input.reshape(1, self.forecast_window, 1)
        
        for hour in range(hours_ahead):
            # Predict next value
            scaled_pred = self.models[resource_type].predict(current_input, verbose=0)
            
            # Inverse transform prediction
            pred_value = self.scalers[resource_type].inverse_transform(
                scaled_pred.reshape(-1, 1)
            )[0][0]
            
            # Calculate confidence based on historical accuracy
            confidence = self._calculate_confidence(resource_type, pred_value)
            
            # Create prediction object
            prediction = ResourcePrediction(
                resource_type=resource_type,
                predicted_value=float(pred_value),
                confidence=confidence,
                timestamp=datetime.now() + timedelta(hours=hour+1)
            )
            predictions.append(prediction)
            
            # Update input for next prediction
            current_input = np.roll(current_input, -1)
            current_input[0, -1, 0] = scaled_pred

        return predictions

    def _calculate_confidence(self, resource_type: str, predicted_value: float) -> float:
        """Calculate confidence score for prediction."""
        if len(self.metrics_history) < 2:
            return 0.5

        # Get recent actual values
        recent_values = []
        if resource_type == 'cpu':
            recent_values = [m.cpu_usage for m in self.metrics_history[-10:]]
        elif resource_type == 'memory':
            recent_values = [m.memory_usage for m in self.metrics_history[-10:]]
        elif resource_type == 'disk':
            recent_values = [m.disk_usage for m in self.metrics_history[-10:]]
        elif resource_type == 'network':
            recent_values = [m.network_bandwidth for m in self.metrics_history[-10:]]
        elif resource_type == 'requests':
            recent_values = [float(m.request_count) for m in self.metrics_history[-10:]]

        # Calculate confidence based on prediction's deviation from recent trends
        mean_val = np.mean(recent_values)
        std_val = np.std(recent_values)
        
        if std_val == 0:
            return 1.0 if abs(predicted_value - mean_val) < 0.1 else 0.5
            
        z_score = abs(predicted_value - mean_val) / std_val
        confidence = 1.0 / (1.0 + z_score)
        
        return max(min(confidence, 1.0), 0.0)

    def get_capacity_plan(self) -> Dict[str, Dict]:
        """Generate capacity planning recommendations."""
        plan = {}
        resource_types = ['cpu', 'memory', 'disk', 'network', 'requests']
        
        for resource_type in resource_types:
            try:
                predictions = self.predict_resource_usage(resource_type, 24)  # 24-hour forecast
                max_predicted = max(p.predicted_value for p in predictions)
                avg_predicted = np.mean([p.predicted_value for p in predictions])
                min_confidence = min(p.confidence for p in predictions)
                
                # Calculate recommended capacity
                buffer_factor = 1.0 + (1.0 - min_confidence)  # More buffer for less confident predictions
                recommended_capacity = max_predicted * buffer_factor
                
                plan[resource_type] = {
                    'current_usage': self.metrics_history[-1].__dict__[f"{resource_type}_usage"]
                    if resource_type != 'requests' else float(self.metrics_history[-1].request_count),
                    'max_predicted': max_predicted,
                    'avg_predicted': avg_predicted,
                    'confidence': min_confidence,
                    'recommended_capacity': recommended_capacity
                }
            except (ValueError, KeyError) as e:
                self.logger.warning(f"Could not generate capacity plan for {resource_type}: {str(e)}")
                continue
        
        return plan 