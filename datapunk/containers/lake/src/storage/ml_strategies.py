from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, IsolationForest
import logging
from datetime import datetime, timedelta
from .cache_strategies import WarmingStrategy

logger = logging.getLogger(__name__)

class LSTMPredictor(nn.Module):
    """LSTM model for sequence prediction"""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        num_layers: int,
        output_size: int
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True
        )
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        batch_size = x.size(0)
        
        if hidden is None:
            h0 = torch.zeros(
                self.num_layers,
                batch_size,
                self.hidden_size
            ).to(x.device)
            c0 = torch.zeros(
                self.num_layers,
                batch_size,
                self.hidden_size
            ).to(x.device)
            hidden = (h0, c0)
            
        out, hidden = self.lstm(x, hidden)
        out = self.fc(out[:, -1, :])
        return out, hidden

class SequenceWarming(WarmingStrategy):
    """LSTM-based sequence prediction for cache warming"""
    
    def __init__(
        self,
        redis: Any,
        access_pattern: Any,
        sequence_length: int = 10,
        hidden_size: int = 64,
        num_layers: int = 2
    ):
        super().__init__()
        self.redis = redis
        self.access_pattern = access_pattern
        self.sequence_length = sequence_length
        self.model = LSTMPredictor(
            input_size=5,  # Features per timestep
            hidden_size=hidden_size,
            num_layers=num_layers,
            output_size=1
        )
        self.scaler = StandardScaler()
        self.last_update = 0
        self.update_interval = 3600
        self.min_sequences = 10
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming based on sequence prediction"""
        if time.time() - self.last_update > self.update_interval:
            await self._update_model()
            
        candidates = []
        keys = await self.redis.keys(pattern)
        
        for key in keys:
            if not await self.redis.exists(key):
                sequences = self._prepare_sequences(key)
                if len(sequences) >= self.sequence_length:
                    prediction = self._predict_next_access(sequences[-1])
                    if prediction >= config.get('sequence_threshold', 0.7):
                        candidates.append(key)
                        
        return candidates[:config.get('batch_size', 100)]
        
    async def _update_model(self):
        """Update LSTM model with recent data"""
        sequences = []
        labels = []
        
        for key, times in self.access_pattern.access_times.items():
            if len(times) < self.sequence_length + 1:
                continue
                
            key_sequences = self._prepare_sequences(key)
            for i in range(len(key_sequences) - 1):
                sequences.append(key_sequences[i])
                labels.append(1.0 if times[i+self.sequence_length] - 
                            times[i+self.sequence_length-1] < 3600 else 0.0)
                
        if len(sequences) < self.min_sequences:
            return
            
        # Convert to tensors
        X = torch.FloatTensor(sequences)
        y = torch.FloatTensor(labels)
        
        # Train model
        optimizer = torch.optim.Adam(self.model.parameters())
        criterion = nn.BCEWithLogitsLoss()
        
        self.model.train()
        for epoch in range(10):
            optimizer.zero_grad()
            output, _ = self.model(X)
            loss = criterion(output.squeeze(), y)
            loss.backward()
            optimizer.step()
            
        self.last_update = time.time()
        
    def _prepare_sequences(self, key: str) -> List[np.ndarray]:
        """Prepare sequences for LSTM"""
        times = self.access_pattern.access_times.get(key, [])
        if len(times) < self.sequence_length:
            return []
            
        sequences = []
        for i in range(len(times) - self.sequence_length + 1):
            sequence = []
            for j in range(self.sequence_length):
                t = times[i+j]
                dt = datetime.fromtimestamp(t)
                features = [
                    dt.hour / 24.0,
                    dt.weekday() / 7.0,
                    len(times[:i+j]) / 100.0,  # Normalized count
                    (t - times[i+j-1]) / 3600.0 if j > 0 else 0,
                    np.mean(np.diff(times[:i+j])) / 3600.0 if j > 0 else 0
                ]
                sequence.append(features)
            sequences.append(sequence)
            
        return sequences
        
    def _predict_next_access(self, sequence: np.ndarray) -> float:
        """Predict probability of next access"""
        self.model.eval()
        with torch.no_grad():
            X = torch.FloatTensor([sequence])
            output, _ = self.model(X)
            return torch.sigmoid(output).item()

class AnomalyDetector:
    """Anomaly detection for cache access patterns"""
    
    def __init__(self, contamination: float = 0.1):
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42
        )
        self.scaler = StandardScaler()
        
    def fit(self, data: pd.DataFrame):
        """Train anomaly detection model"""
        X = self.scaler.fit_transform(data)
        self.model.fit(X)
        
    def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Predict anomalies"""
        X = self.scaler.transform(data)
        return self.model.predict(X)

class AdaptiveWarming(WarmingStrategy):
    """Adaptive warming strategy with anomaly detection"""
    
    def __init__(
        self,
        redis: Any,
        access_pattern: Any,
        window_size: int = 3600
    ):
        super().__init__()
        self.redis = redis
        self.access_pattern = access_pattern
        self.window_size = window_size
        self.anomaly_detector = AnomalyDetector()
        self.last_update = 0
        self.update_interval = 3600
        
    async def get_warming_candidates(
        self,
        pattern: str,
        config: Dict[str, Any]
    ) -> List[str]:
        """Get keys that need warming based on adaptive analysis"""
        if time.time() - self.last_update > self.update_interval:
            await self._update_model()
            
        candidates = []
        keys = await self.redis.keys(pattern)
        
        # Prepare current features
        features = self._prepare_features(keys)
        if features.empty:
            return []
            
        # Detect anomalies
        predictions = self.anomaly_detector.predict(features)
        
        # Select keys with anomalous patterns
        for key, pred in zip(features.index, predictions):
            if pred == -1 and not await self.redis.exists(key):
                candidates.append(key)
                
        return candidates[:config.get('batch_size', 100)]
        
    async def _update_model(self):
        """Update anomaly detection model"""
        data = []
        now = time.time()
        cutoff = now - self.window_size
        
        for key, times in self.access_pattern.access_times.items():
            recent_times = [t for t in times if t > cutoff]
            if len(recent_times) < 2:
                continue
                
            row = {
                'key': key,
                'access_count': len(recent_times),
                'mean_interval': np.mean(np.diff(recent_times)),
                'std_interval': np.std(np.diff(recent_times)),
                'last_access': now - recent_times[-1],
                'burst_ratio': self._calculate_burst_ratio(recent_times)
            }
            data.append(row)
            
        if not data:
            return
            
        df = pd.DataFrame(data).set_index('key')
        self.anomaly_detector.fit(df)
        self.last_update = time.time()
        
    def _prepare_features(self, keys: List[str]) -> pd.DataFrame:
        """Prepare features for anomaly detection"""
        data = []
        now = time.time()
        cutoff = now - self.window_size
        
        for key in keys:
            times = self.access_pattern.access_times.get(key, [])
            recent_times = [t for t in times if t > cutoff]
            if len(recent_times) < 2:
                continue
                
            row = {
                'key': key,
                'access_count': len(recent_times),
                'mean_interval': np.mean(np.diff(recent_times)),
                'std_interval': np.std(np.diff(recent_times)),
                'last_access': now - recent_times[-1],
                'burst_ratio': self._calculate_burst_ratio(recent_times)
            }
            data.append(row)
            
        return pd.DataFrame(data).set_index('key')
        
    def _calculate_burst_ratio(self, times: List[float]) -> float:
        """Calculate ratio of burst vs normal access"""
        if len(times) < 2:
            return 0.0
            
        intervals = np.diff(times)
        mean_interval = np.mean(intervals)
        burst_count = sum(1 for i in intervals if i < mean_interval * 0.5)
        return burst_count / len(intervals)