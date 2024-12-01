from typing import List, Tuple, Dict, Set
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from shapely.geometry import Polygon

class DensityAnalyzer:
    """Analyzes spatial density patterns"""
    
    def __init__(self, grid_manager):
        self.grid_manager = grid_manager
        
    def calculate_density_metrics(self, points: List[Tuple[float, float]], 
                                precision: int) -> Dict[str, float]:
        """Calculate density metrics for each partition"""
        partitions = self.grid_manager.partition_points(points, precision)
        metrics = {}
        
        for cell_id, cell_points in partitions.items():
            cell_poly = self.grid_manager.get_cell_polygon(cell_id)
            density = len(cell_points) / cell_poly.area
            metrics[cell_id] = density
            
        return metrics
    
    def find_hotspots(self, points: List[Tuple[float, float]], 
                     precision: int, 
                     threshold: float = 0.75) -> Set[str]:
        """Identify high-density areas"""
        densities = self.calculate_density_metrics(points, precision)
        if not densities:
            return set()
            
        density_threshold = np.percentile(list(densities.values()), 
                                        threshold * 100)
        return {cell_id for cell_id, density in densities.items() 
                if density >= density_threshold}
    
    def cluster_analysis(self, points: List[Tuple[float, float]], 
                        eps: float = 0.1, 
                        min_samples: int = 5) -> Dict[str, List[Tuple[float, float]]]:
        """Perform DBSCAN clustering on points"""
        if not points:
            return {}
            
        # Normalize points for clustering
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples)
        clusters = dbscan.fit_predict(points_normalized)
        
        # Group points by cluster
        cluster_points = {}
        for point, cluster_id in zip(points, clusters):
            if cluster_id not in cluster_points:
                cluster_points[str(cluster_id)] = []
            cluster_points[str(cluster_id)].append(point)
            
        return cluster_points
    
    def get_density_distribution(self, points: List[Tuple[float, float]], 
                               precision: int) -> Dict[str, Dict[str, float]]:
        """Get density distribution statistics"""
        densities = self.calculate_density_metrics(points, precision)
        if not densities:
            return {}
            
        density_values = list(densities.values())
        return {
            'statistics': {
                'mean': float(np.mean(density_values)),
                'median': float(np.median(density_values)),
                'std': float(np.std(density_values)),
                'min': float(np.min(density_values)),
                'max': float(np.max(density_values)),
                'quartiles': [
                    float(np.percentile(density_values, 25)),
                    float(np.percentile(density_values, 50)),
                    float(np.percentile(density_values, 75))
                ]
            },
            'cell_densities': densities
        }
    
    def find_density_anomalies(self, points: List[Tuple[float, float]], 
                             precision: int,
                             std_threshold: float = 2.0) -> Dict[str, List[str]]:
        """Find cells with anomalous densities"""
        densities = self.calculate_density_metrics(points, precision)
        if not densities:
            return {'high': [], 'low': []}
            
        density_values = np.array(list(densities.values()))
        mean_density = np.mean(density_values)
        std_density = np.std(density_values)
        
        high_threshold = mean_density + std_threshold * std_density
        low_threshold = mean_density - std_threshold * std_density
        
        return {
            'high': [cell_id for cell_id, density in densities.items() 
                    if density > high_threshold],
            'low': [cell_id for cell_id, density in densities.items() 
                   if density < low_threshold]
        } 