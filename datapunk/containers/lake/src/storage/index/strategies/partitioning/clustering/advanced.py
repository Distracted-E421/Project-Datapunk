from typing import List, Tuple, Dict
import numpy as np
from sklearn.cluster import OPTICS
from sklearn.preprocessing import StandardScaler
import hdbscan
from datetime import datetime, timedelta
import pytz

class AdvancedClusterAnalyzer:
    """Advanced clustering analysis with HDBSCAN and OPTICS"""
    
    def __init__(self, grid_manager):
        self.grid_manager = grid_manager
        
    def hdbscan_clustering(self, points: List[Tuple[float, float]], 
                          min_cluster_size: int = 5,
                          min_samples: int = None,
                          cluster_selection_epsilon: float = 0.0) -> Dict[str, List[Tuple[float, float]]]:
        """Perform HDBSCAN clustering"""
        if not points:
            return {}
            
        # Normalize points
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Configure HDBSCAN
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            min_samples=min_samples,
            cluster_selection_epsilon=cluster_selection_epsilon,
            prediction_data=True
        )
        
        # Perform clustering
        cluster_labels = clusterer.fit_predict(points_normalized)
        
        # Get probabilities and outlier scores
        probabilities = clusterer.probabilities_
        outlier_scores = clusterer.outlier_scores_
        
        # Group points by cluster with metadata
        clusters = {}
        for i, (point, label, prob, score) in enumerate(zip(points, cluster_labels, 
                                                          probabilities, outlier_scores)):
            cluster_id = str(label)
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'points': [],
                    'probabilities': [],
                    'outlier_scores': []
                }
            clusters[cluster_id]['points'].append(point)
            clusters[cluster_id]['probabilities'].append(float(prob))
            clusters[cluster_id]['outlier_scores'].append(float(score))
            
        return clusters
    
    def optics_clustering(self, points: List[Tuple[float, float]], 
                         min_samples: int = 5,
                         max_eps: float = np.inf,
                         cluster_method: str = 'xi') -> Dict[str, List[Tuple[float, float]]]:
        """Perform OPTICS clustering"""
        if not points:
            return {}
            
        # Normalize points
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Configure OPTICS
        clusterer = OPTICS(
            min_samples=min_samples,
            max_eps=max_eps,
            cluster_method=cluster_method
        )
        
        # Perform clustering
        cluster_labels = clusterer.fit_predict(points_normalized)
        
        # Get reachability and ordering
        reachability = clusterer.reachability_
        ordering = clusterer.ordering_
        
        # Group points by cluster with metadata
        clusters = {}
        for i, (point, label) in enumerate(zip(points, cluster_labels)):
            cluster_id = str(label)
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    'points': [],
                    'reachability': [],
                    'ordering': []
                }
            clusters[cluster_id]['points'].append(point)
            clusters[cluster_id]['reachability'].append(float(reachability[i]))
            clusters[cluster_id]['ordering'].append(int(ordering[i]))
            
        return clusters
    
    def analyze_cluster_stability(self, points: List[Tuple[float, float]], 
                                time_window: timedelta = timedelta(hours=1),
                                sample_interval: timedelta = timedelta(minutes=10)) -> Dict[str, Dict]:
        """Analyze cluster stability over time"""
        now = datetime.now(pytz.UTC)
        window_start = now - time_window
        
        # Get historical clusters
        historical_clusters = []
        current_time = window_start
        
        while current_time <= now:
            # Get clusters at this time point
            clusters = self.hdbscan_clustering(points)
            historical_clusters.append({
                'timestamp': current_time,
                'clusters': clusters
            })
            current_time += sample_interval
        
        # Calculate stability metrics
        stability_metrics = {}
        
        # Track cluster persistence
        for cluster_snapshot in historical_clusters:
            for cluster_id, cluster_data in cluster_snapshot['clusters'].items():
                if cluster_id not in stability_metrics:
                    stability_metrics[cluster_id] = {
                        'appearances': 0,
                        'total_points': [],
                        'mean_probability': [],
                        'mean_outlier_score': []
                    }
                
                stability_metrics[cluster_id]['appearances'] += 1
                stability_metrics[cluster_id]['total_points'].append(
                    len(cluster_data['points'])
                )
                stability_metrics[cluster_id]['mean_probability'].append(
                    np.mean(cluster_data['probabilities'])
                )
                stability_metrics[cluster_id]['mean_outlier_score'].append(
                    np.mean(cluster_data['outlier_scores'])
                )
        
        # Calculate final metrics
        total_snapshots = len(historical_clusters)
        for cluster_id in stability_metrics:
            metrics = stability_metrics[cluster_id]
            metrics['persistence'] = metrics['appearances'] / total_snapshots
            metrics['point_stability'] = float(np.std(metrics['total_points']))
            metrics['probability_stability'] = float(np.mean(metrics['mean_probability']))
            metrics['outlier_stability'] = float(np.mean(metrics['mean_outlier_score']))
            
            # Clean up raw data
            del metrics['total_points']
            del metrics['mean_probability']
            del metrics['mean_outlier_score']
        
        return stability_metrics
    
    def get_cluster_hierarchy(self, points: List[Tuple[float, float]], 
                            min_cluster_size: int = 5) -> Dict:
        """Get hierarchical clustering structure"""
        if not points:
            return {}
            
        # Normalize points
        scaler = StandardScaler()
        points_array = np.array(points)
        points_normalized = scaler.fit_transform(points_array)
        
        # Perform hierarchical clustering
        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size,
            prediction_data=True
        )
        clusterer.fit(points_normalized)
        
        # Extract hierarchy
        hierarchy = {
            'condensed_tree': {
                'parent': clusterer.condensed_tree_.parent.tolist(),
                'child': clusterer.condensed_tree_.child.tolist(),
                'lambda_val': clusterer.condensed_tree_.lambda_val.tolist()
            },
            'single_linkage_tree': {
                'parent': clusterer.single_linkage_tree_.parent.tolist(),
                'children': clusterer.single_linkage_tree_.children.tolist(),
                'distances': clusterer.single_linkage_tree_.distances.tolist()
            },
            'cluster_persistence': dict(enumerate(clusterer.cluster_persistence_))
        }
        
        return hierarchy 