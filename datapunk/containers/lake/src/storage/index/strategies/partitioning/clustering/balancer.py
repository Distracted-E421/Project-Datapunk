from typing import List, Tuple, Dict
import numpy as np
from collections import defaultdict
from datetime import datetime, timedelta

class LoadBalancer:
    """Manages partition load balancing"""
    
    def __init__(self, grid_manager):
        self.grid_manager = grid_manager
        self.load_history = defaultdict(list)
        self.max_history_size = 100
        self.last_rebalance = datetime.now()
        self.min_rebalance_interval = timedelta(minutes=5)
        
    def calculate_load_metrics(self, partitions: Dict[str, List[Tuple[float, float]]],
                             weights: Dict[str, float] = None) -> Dict[str, float]:
        """Calculate weighted load metrics for each partition"""
        if weights is None:
            weights = {
                'point_count': 0.4,
                'historical_load': 0.3,
                'density': 0.3
            }
            
        metrics = {}
        total_points = sum(len(points) for points in partitions.values())
        
        for cell_id, points in partitions.items():
            # Calculate current point load
            current_load = len(points) / max(total_points, 1)
            
            # Get historical load
            historical_load = np.mean(self.load_history[cell_id]) if self.load_history[cell_id] else 0
            
            # Calculate density
            cell_poly = self.grid_manager.get_cell_polygon(cell_id)
            density = len(points) / cell_poly.area if cell_poly.area > 0 else 0
            
            # Normalize density across all partitions
            max_density = max((len(p) / self.grid_manager.get_cell_polygon(c).area 
                             for c, p in partitions.items()), default=1)
            normalized_density = density / max_density if max_density > 0 else 0
            
            # Calculate weighted metric
            metrics[cell_id] = (
                weights['point_count'] * current_load +
                weights['historical_load'] * historical_load +
                weights['density'] * normalized_density
            )
            
            # Update history
            self.load_history[cell_id].append(current_load)
            if len(self.load_history[cell_id]) > self.max_history_size:
                self.load_history[cell_id].pop(0)
                
        return metrics
    
    def suggest_rebalancing(self, partitions: Dict[str, List[Tuple[float, float]]],
                           threshold: float = 0.2,
                           min_partition_size: int = 10) -> List[Tuple[str, str, int]]:
        """Suggest partition splits or merges"""
        # Check if enough time has passed since last rebalance
        now = datetime.now()
        if now - self.last_rebalance < self.min_rebalance_interval:
            return []
            
        load_metrics = self.calculate_load_metrics(partitions)
        suggestions = []
        
        # Calculate thresholds
        avg_load = np.mean(list(load_metrics.values()))
        high_threshold = avg_load * (1 + threshold)
        low_threshold = avg_load * (1 - threshold)
        
        # Find overloaded and underloaded partitions
        overloaded = {cell_id for cell_id, load in load_metrics.items() 
                     if load > high_threshold}
        underloaded = {cell_id for cell_id, load in load_metrics.items() 
                      if load < low_threshold and 
                      len(partitions[cell_id]) >= min_partition_size}
        
        # Suggest splits for overloaded partitions
        for cell_id in overloaded:
            suggestions.append((cell_id, None, 1))  # 1 indicates split
            
        # Find mergeable pairs of underloaded partitions
        underloaded_list = list(underloaded)
        for i in range(0, len(underloaded_list) - 1, 2):
            cell1 = underloaded_list[i]
            cell2 = underloaded_list[i + 1]
            
            # Check if partitions are neighbors
            if cell2 in self.grid_manager.grid.get_neighbors(cell1):
                suggestions.append((cell1, cell2, 2))  # 2 indicates merge
                
        self.last_rebalance = now
        return suggestions
    
    def estimate_optimal_partition_count(self, points: List[Tuple[float, float]],
                                       target_points_per_partition: int = 1000) -> int:
        """Estimate optimal number of partitions"""
        total_points = len(points)
        return max(1, total_points // target_points_per_partition)
    
    def get_load_distribution(self) -> Dict[str, Dict[str, float]]:
        """Get load distribution statistics"""
        stats = {}
        
        for cell_id, history in self.load_history.items():
            if history:
                stats[cell_id] = {
                    'current_load': history[-1],
                    'mean_load': float(np.mean(history)),
                    'std_load': float(np.std(history)),
                    'min_load': float(np.min(history)),
                    'max_load': float(np.max(history)),
                    'trend': float(np.polyfit(range(len(history)), history, 1)[0])
                }
                
        return stats
    
    def predict_future_load(self, cell_id: str, 
                          time_steps: int = 5) -> List[float]:
        """Predict future load using simple linear regression"""
        history = self.load_history[cell_id]
        if len(history) < 2:
            return [history[-1]] * time_steps if history else [0.0] * time_steps
            
        # Fit linear regression
        x = np.arange(len(history))
        y = np.array(history)
        coeffs = np.polyfit(x, y, 1)
        
        # Predict future values
        future_x = np.arange(len(history), len(history) + time_steps)
        predictions = np.polyval(coeffs, future_x)
        
        # Ensure predictions are non-negative
        return [max(0.0, float(p)) for p in predictions] 