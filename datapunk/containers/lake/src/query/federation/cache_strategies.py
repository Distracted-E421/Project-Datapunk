from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import asyncio
import logging
from .core import QueryPlan

@dataclass
class CacheEntry:
    """Represents a cached query result."""
    result: Any
    query_hash: str
    creation_time: datetime
    last_access: datetime
    access_count: int
    size_bytes: int
    source_id: str
    metadata: Dict[str, Any]

class MLBasedStrategy:
    """Machine learning based caching strategy."""
    
    def __init__(self, max_cache_size_mb: int = 1024):
        self.max_cache_bytes = max_cache_size_mb * 1024 * 1024
        self.access_history: List[Dict[str, Any]] = []
        self.model = DBSCAN(eps=0.3, min_samples=2)
        self.scaler = StandardScaler()
        self.logger = logging.getLogger(__name__)
    
    async def should_cache(self, query: QueryPlan, metadata: Dict[str, Any]) -> bool:
        """Determine if query result should be cached using ML."""
        try:
            features = self._extract_features(query, metadata)
            if not features:
                return False
            
            # Normalize features
            X = self.scaler.fit_transform([features])
            
            # Predict using clustering
            labels = self.model.fit_predict(X)
            
            # Items in clusters are more likely to be accessed again
            return labels[0] != -1
        except Exception as e:
            self.logger.error(f"Error in cache prediction: {e}")
            return False
    
    def _extract_features(self,
                         query: QueryPlan,
                         metadata: Dict[str, Any]) -> Optional[List[float]]:
        """Extract features for ML prediction."""
        try:
            # Query complexity features
            complexity = self._calculate_query_complexity(query)
            
            # Time-based features
            now = datetime.utcnow()
            hour = float(now.hour)
            day = float(now.weekday())
            
            # Resource features
            result_size = metadata.get('estimated_size', 0)
            cpu_cost = metadata.get('cpu_cost', 0)
            
            # Usage features
            access_count = metadata.get('access_count', 0)
            last_access_gap = metadata.get('last_access_gap', 0)
            
            return [
                complexity,
                hour / 24.0,  # Normalize to [0,1]
                day / 7.0,    # Normalize to [0,1]
                np.log1p(result_size) / 20.0,  # Normalize large values
                cpu_cost / 1000.0,  # Normalize to reasonable range
                np.log1p(access_count) / 10.0,
                np.log1p(last_access_gap) / 15.0
            ]
        except Exception as e:
            self.logger.error(f"Error extracting features: {e}")
            return None
    
    def _calculate_query_complexity(self, query: QueryPlan) -> float:
        """Calculate query complexity score."""
        complexity = 0.0
        
        def analyze_node(node: Any) -> None:
            nonlocal complexity
            if hasattr(node, 'operation_type'):
                # Weight different operations
                weights = {
                    'scan': 1.0,
                    'filter': 1.2,
                    'join': 2.0,
                    'aggregate': 1.5,
                    'sort': 1.3,
                    'window': 1.8
                }
                complexity += weights.get(
                    node.operation_type.lower(),
                    1.0
                )
            
            if hasattr(node, 'children'):
                for child in node.children:
                    analyze_node(child)
        
        analyze_node(query.root)
        return complexity

class SemanticStrategy:
    """Semantic-based caching strategy."""
    
    def __init__(self,
                 similarity_threshold: float = 0.8,
                 max_semantic_cache_entries: int = 1000):
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_semantic_cache_entries
        self.semantic_cache: Dict[str, CacheEntry] = {}
        self.query_embeddings: Dict[str, np.ndarray] = {}
    
    async def should_cache(self, query: QueryPlan, metadata: Dict[str, Any]) -> bool:
        """Determine if query should be cached based on semantics."""
        try:
            # Get query embedding
            embedding = await self._get_query_embedding(query)
            if embedding is None:
                return False
            
            # Check for similar queries
            similar_queries = self._find_similar_queries(embedding)
            
            # Cache if no similar queries exist
            return len(similar_queries) == 0
        except Exception as e:
            logging.error(f"Error in semantic cache check: {e}")
            return False
    
    async def _get_query_embedding(self, query: QueryPlan) -> Optional[np.ndarray]:
        """Get semantic embedding for query."""
        try:
            # Convert query to string representation
            query_str = self._query_to_string(query)
            
            # Use query hash as cache key
            query_hash = hash(query_str)
            
            # Return cached embedding if available
            if query_hash in self.query_embeddings:
                return self.query_embeddings[query_hash]
            
            # Generate new embedding
            embedding = await self._generate_embedding(query_str)
            
            # Cache embedding
            self.query_embeddings[query_hash] = embedding
            
            return embedding
        except Exception as e:
            logging.error(f"Error generating query embedding: {e}")
            return None
    
    def _find_similar_queries(self, embedding: np.ndarray) -> List[str]:
        """Find semantically similar queries in cache."""
        similar_queries = []
        
        for query_hash, cached_embedding in self.query_embeddings.items():
            similarity = self._calculate_similarity(embedding, cached_embedding)
            if similarity >= self.similarity_threshold:
                similar_queries.append(query_hash)
        
        return similar_queries
    
    def _calculate_similarity(self,
                            embedding1: np.ndarray,
                            embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between embeddings."""
        return float(np.dot(embedding1, embedding2) / 
                    (np.linalg.norm(embedding1) * np.linalg.norm(embedding2)))
    
    def _query_to_string(self, query: QueryPlan) -> str:
        """Convert query plan to string representation."""
        # Implementation depends on query plan structure
        pass
    
    async def _generate_embedding(self, query_str: str) -> np.ndarray:
        """Generate semantic embedding for query string."""
        # Implementation depends on embedding model
        pass

class HybridStrategy:
    """Hybrid caching strategy combining multiple approaches."""
    
    def __init__(self):
        self.ml_strategy = MLBasedStrategy()
        self.semantic_strategy = SemanticStrategy()
        self.weights = {
            'ml': 0.5,
            'semantic': 0.3,
            'heuristic': 0.2
        }
    
    async def should_cache(self, query: QueryPlan, metadata: Dict[str, Any]) -> bool:
        """Determine if query should be cached using hybrid approach."""
        try:
            # Get scores from different strategies
            ml_score = float(await self.ml_strategy.should_cache(query, metadata))
            semantic_score = float(await self.semantic_strategy.should_cache(query, metadata))
            heuristic_score = float(self._apply_heuristics(query, metadata))
            
            # Calculate weighted score
            total_score = (
                self.weights['ml'] * ml_score +
                self.weights['semantic'] * semantic_score +
                self.weights['heuristic'] * heuristic_score
            )
            
            return total_score >= 0.5
        except Exception as e:
            logging.error(f"Error in hybrid cache decision: {e}")
            return False
    
    def _apply_heuristics(self,
                         query: QueryPlan,
                         metadata: Dict[str, Any]) -> bool:
        """Apply heuristic rules for caching decision."""
        try:
            # Check result size
            if metadata.get('estimated_size', 0) > 100 * 1024 * 1024:  # 100MB
                return False
            
            # Check query complexity
            if self._is_complex_query(query):
                return True
            
            # Check access patterns
            if metadata.get('access_count', 0) > 5:
                return True
            
            # Check temporal locality
            last_access = metadata.get('last_access_time')
            if last_access:
                time_gap = (datetime.utcnow() - last_access).total_seconds()
                if time_gap < 3600:  # 1 hour
                    return True
            
            return False
        except Exception as e:
            logging.error(f"Error applying heuristics: {e}")
            return False
    
    def _is_complex_query(self, query: QueryPlan) -> bool:
        """Check if query is complex enough to warrant caching."""
        try:
            # Count operations
            operation_count = 0
            join_count = 0
            
            def count_operations(node: Any) -> None:
                nonlocal operation_count, join_count
                if hasattr(node, 'operation_type'):
                    operation_count += 1
                    if node.operation_type.lower() == 'join':
                        join_count += 1
                
                if hasattr(node, 'children'):
                    for child in node.children:
                        count_operations(child)
            
            count_operations(query.root)
            
            # Consider query complex if:
            # 1. Has many operations
            # 2. Has multiple joins
            # 3. Has specific expensive operations
            return (
                operation_count > 5 or
                join_count > 1 or
                self._has_expensive_operations(query)
            )
        except Exception as e:
            logging.error(f"Error checking query complexity: {e}")
            return False
    
    def _has_expensive_operations(self, query: QueryPlan) -> bool:
        """Check if query has expensive operations."""
        expensive_ops = {'window', 'recursive', 'outer_join'}
        
        def check_node(node: Any) -> bool:
            if hasattr(node, 'operation_type'):
                if node.operation_type.lower() in expensive_ops:
                    return True
            
            if hasattr(node, 'children'):
                return any(check_node(child) for child in node.children)
            
            return False
        
        return check_node(query.root)
    
    async def update_weights(self, performance_metrics: Dict[str, float]) -> None:
        """Update strategy weights based on performance."""
        try:
            total_benefit = sum(performance_metrics.values())
            if total_benefit > 0:
                self.weights = {
                    strategy: benefit / total_benefit
                    for strategy, benefit in performance_metrics.items()
                }
        except Exception as e:
            logging.error(f"Error updating weights: {e}")

class AdaptiveStrategy:
    """Adaptive caching strategy that learns from query patterns."""
    
    def __init__(self):
        self.hybrid_strategy = HybridStrategy()
        self.performance_history: List[Dict[str, Any]] = []
        self.adaptation_interval = timedelta(hours=1)
        self.last_adaptation = datetime.utcnow()
    
    async def should_cache(self, query: QueryPlan, metadata: Dict[str, Any]) -> bool:
        """Determine if query should be cached using adaptive strategy."""
        try:
            # Check if adaptation is needed
            await self._maybe_adapt()
            
            # Use hybrid strategy with current weights
            return await self.hybrid_strategy.should_cache(query, metadata)
        except Exception as e:
            logging.error(f"Error in adaptive cache decision: {e}")
            return False
    
    async def record_performance(self,
                               query: QueryPlan,
                               cache_decision: bool,
                               performance_metrics: Dict[str, float]) -> None:
        """Record cache decision performance."""
        try:
            self.performance_history.append({
                'timestamp': datetime.utcnow(),
                'query_hash': hash(str(query)),
                'cache_decision': cache_decision,
                'metrics': performance_metrics
            })
            
            # Trim old history
            self._trim_history()
        except Exception as e:
            logging.error(f"Error recording performance: {e}")
    
    async def _maybe_adapt(self) -> None:
        """Adapt strategy if enough time has passed."""
        try:
            now = datetime.utcnow()
            if now - self.last_adaptation >= self.adaptation_interval:
                # Calculate strategy benefits
                benefits = self._calculate_strategy_benefits()
                
                # Update weights
                await self.hybrid_strategy.update_weights(benefits)
                
                self.last_adaptation = now
        except Exception as e:
            logging.error(f"Error in strategy adaptation: {e}")
    
    def _calculate_strategy_benefits(self) -> Dict[str, float]:
        """Calculate benefits of different strategies."""
        try:
            benefits = {
                'ml': 0.0,
                'semantic': 0.0,
                'heuristic': 0.0
            }
            
            for record in self.performance_history:
                metrics = record['metrics']
                if record['cache_decision']:
                    # Calculate benefit based on hit rate and latency improvement
                    benefit = (
                        metrics.get('hit_rate', 0.0) *
                        metrics.get('latency_improvement', 0.0)
                    )
                    
                    # Distribute benefit among strategies
                    benefits['ml'] += benefit * 0.4
                    benefits['semantic'] += benefit * 0.4
                    benefits['heuristic'] += benefit * 0.2
            
            return benefits
        except Exception as e:
            logging.error(f"Error calculating benefits: {e}")
            return {'ml': 1.0, 'semantic': 1.0, 'heuristic': 1.0}
    
    def _trim_history(self) -> None:
        """Trim performance history to recent entries."""
        try:
            cutoff = datetime.utcnow() - timedelta(days=7)
            self.performance_history = [
                record for record in self.performance_history
                if record['timestamp'] >= cutoff
            ]
        except Exception as e:
            logging.error(f"Error trimming history: {e}") 