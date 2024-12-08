from typing import Dict, List, Any, Optional
import json
import numpy as np
from datetime import datetime, date
import pandas as pd
from .formatter_core import ResultFormatter

class TimeSeriesFormatter(ResultFormatter):
    """Formats time series data with specialized visualizations."""
    
    def format_table(self,
                    data: List[Dict[str, Any]],
                    headers: Optional[List[str]] = None,
                    format_type: str = "text") -> str:
        """Format time series data."""
        try:
            if not data:
                return "No results"
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(data)
            
            if format_type == "text":
                return self._format_text_timeseries(df)
            elif format_type == "json":
                return self._format_json_timeseries(df)
            elif format_type == "summary":
                return self._format_summary_timeseries(df)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
        except Exception as e:
            self.logger.error(f"Error formatting time series: {e}")
            return str(e)
    
    def _format_text_timeseries(self, df: pd.DataFrame) -> str:
        """Format time series as text table with trends."""
        try:
            # Calculate basic statistics
            stats = df.describe()
            
            # Calculate trends
            trends = self._calculate_trends(df)
            
            # Format output
            lines = [
                "Time Series Analysis",
                "=" * 50,
                "",
                "Statistics:",
                "-" * 20
            ]
            
            # Add statistics
            for col in stats.columns:
                lines.extend([
                    f"{col}:",
                    f"  Count: {stats[col]['count']}",
                    f"  Mean:  {stats[col]['mean']:.2f}",
                    f"  Std:   {stats[col]['std']:.2f}",
                    f"  Min:   {stats[col]['min']:.2f}",
                    f"  Max:   {stats[col]['max']:.2f}",
                    ""
                ])
            
            # Add trends
            lines.extend([
                "Trends:",
                "-" * 20
            ])
            
            for col, trend in trends.items():
                lines.extend([
                    f"{col}:",
                    f"  Direction: {trend['direction']}",
                    f"  Strength:  {trend['strength']:.2f}",
                    ""
                ])
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting text time series: {e}")
            return str(e)
    
    def _format_json_timeseries(self, df: pd.DataFrame) -> str:
        """Format time series as JSON with additional metadata."""
        try:
            # Calculate statistics and trends
            stats = df.describe().to_dict()
            trends = self._calculate_trends(df)
            
            # Create result structure
            result = {
                'data': df.to_dict(orient='records'),
                'metadata': {
                    'statistics': stats,
                    'trends': trends,
                    'timespan': {
                        'start': str(df.index.min()),
                        'end': str(df.index.max()),
                        'periods': len(df)
                    }
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            self.logger.error(f"Error formatting JSON time series: {e}")
            return str(e)
    
    def _format_summary_timeseries(self, df: pd.DataFrame) -> str:
        """Format time series summary with key insights."""
        try:
            # Calculate key metrics
            metrics = self._calculate_metrics(df)
            
            # Format output
            lines = [
                "Time Series Summary",
                "=" * 50,
                "",
                "Key Metrics:",
                "-" * 20
            ]
            
            for metric, value in metrics.items():
                lines.append(f"{metric}: {value}")
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting time series summary: {e}")
            return str(e)
    
    def _calculate_trends(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Calculate trends for each column."""
        trends = {}
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                # Calculate trend direction and strength
                values = df[col].dropna()
                if len(values) > 1:
                    slope = np.polyfit(range(len(values)), values, 1)[0]
                    correlation = np.corrcoef(range(len(values)), values)[0, 1]
                    
                    trends[col] = {
                        'direction': 'up' if slope > 0 else 'down',
                        'strength': abs(correlation)
                    }
        
        return trends
    
    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate key metrics for time series."""
        metrics = {}
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                values = df[col].dropna()
                if len(values) > 0:
                    metrics[f"{col}_volatility"] = values.std() / values.mean()
                    metrics[f"{col}_trend"] = (
                        values.iloc[-1] - values.iloc[0]
                    ) / values.iloc[0]
        
        return metrics

class VectorFormatter(ResultFormatter):
    """Formats vector and embedding data."""
    
    def format_table(self,
                    data: List[Dict[str, Any]],
                    headers: Optional[List[str]] = None,
                    format_type: str = "text") -> str:
        """Format vector data."""
        try:
            if not data:
                return "No results"
            
            if format_type == "text":
                return self._format_text_vectors(data)
            elif format_type == "json":
                return self._format_json_vectors(data)
            elif format_type == "summary":
                return self._format_summary_vectors(data)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
        except Exception as e:
            self.logger.error(f"Error formatting vectors: {e}")
            return str(e)
    
    def _format_text_vectors(self, data: List[Dict[str, Any]]) -> str:
        """Format vectors as text with statistics."""
        try:
            lines = [
                "Vector Analysis",
                "=" * 50,
                ""
            ]
            
            # Format each vector
            for i, item in enumerate(data):
                vector = self._extract_vector(item)
                if vector is not None:
                    stats = self._calculate_vector_stats(vector)
                    lines.extend([
                        f"Vector {i + 1}:",
                        f"  Dimension: {len(vector)}",
                        f"  Magnitude: {stats['magnitude']:.4f}",
                        f"  Mean:      {stats['mean']:.4f}",
                        f"  Std:       {stats['std']:.4f}",
                        f"  Min:       {stats['min']:.4f}",
                        f"  Max:       {stats['max']:.4f}",
                        ""
                    ])
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting text vectors: {e}")
            return str(e)
    
    def _format_json_vectors(self, data: List[Dict[str, Any]]) -> str:
        """Format vectors as JSON with metadata."""
        try:
            result = []
            
            for item in data:
                vector = self._extract_vector(item)
                if vector is not None:
                    stats = self._calculate_vector_stats(vector)
                    result.append({
                        'vector': vector.tolist(),
                        'metadata': {
                            'dimension': len(vector),
                            'statistics': stats
                        }
                    })
            
            return json.dumps(result, indent=2)
        except Exception as e:
            self.logger.error(f"Error formatting JSON vectors: {e}")
            return str(e)
    
    def _format_summary_vectors(self, data: List[Dict[str, Any]]) -> str:
        """Format vector summary with key insights."""
        try:
            vectors = []
            for item in data:
                vector = self._extract_vector(item)
                if vector is not None:
                    vectors.append(vector)
            
            if not vectors:
                return "No valid vectors found"
            
            # Calculate summary statistics
            summary = self._calculate_vectors_summary(vectors)
            
            lines = [
                "Vector Summary",
                "=" * 50,
                "",
                f"Number of Vectors: {len(vectors)}",
                f"Vector Dimension:  {len(vectors[0])}",
                "",
                "Statistics:",
                "-" * 20,
                f"Average Magnitude: {summary['avg_magnitude']:.4f}",
                f"Average Distance:  {summary['avg_distance']:.4f}",
                f"Dimension Range:   {summary['dim_range']}"
            ]
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting vector summary: {e}")
            return str(e)
    
    def _extract_vector(self, item: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract vector from data item."""
        try:
            # Try common vector field names
            for field in ['vector', 'embedding', 'features']:
                if field in item:
                    value = item[field]
                    if isinstance(value, (list, np.ndarray)):
                        return np.array(value)
            return None
        except Exception as e:
            self.logger.error(f"Error extracting vector: {e}")
            return None
    
    def _calculate_vector_stats(self, vector: np.ndarray) -> Dict[str, float]:
        """Calculate statistics for a vector."""
        return {
            'magnitude': np.linalg.norm(vector),
            'mean': np.mean(vector),
            'std': np.std(vector),
            'min': np.min(vector),
            'max': np.max(vector)
        }
    
    def _calculate_vectors_summary(self,
                                vectors: List[np.ndarray]) -> Dict[str, Any]:
        """Calculate summary statistics for multiple vectors."""
        magnitudes = [np.linalg.norm(v) for v in vectors]
        distances = []
        
        # Calculate pairwise distances
        for i in range(len(vectors)):
            for j in range(i + 1, len(vectors)):
                distance = np.linalg.norm(vectors[i] - vectors[j])
                distances.append(distance)
        
        return {
            'avg_magnitude': np.mean(magnitudes),
            'avg_distance': np.mean(distances) if distances else 0,
            'dim_range': f"{np.min(vectors[0]):.4f} to {np.max(vectors[0]):.4f}"
        }

class GraphFormatter(ResultFormatter):
    """Formats graph and network data."""
    
    def format_table(self,
                    data: List[Dict[str, Any]],
                    headers: Optional[List[str]] = None,
                    format_type: str = "text") -> str:
        """Format graph data."""
        try:
            if not data:
                return "No results"
            
            if format_type == "text":
                return self._format_text_graph(data)
            elif format_type == "json":
                return self._format_json_graph(data)
            elif format_type == "summary":
                return self._format_summary_graph(data)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
        except Exception as e:
            self.logger.error(f"Error formatting graph: {e}")
            return str(e)
    
    def _format_text_graph(self, data: List[Dict[str, Any]]) -> str:
        """Format graph as text with network statistics."""
        try:
            # Extract nodes and edges
            nodes, edges = self._extract_graph_elements(data)
            
            # Calculate statistics
            stats = self._calculate_graph_stats(nodes, edges)
            
            lines = [
                "Graph Analysis",
                "=" * 50,
                "",
                "Network Statistics:",
                "-" * 20,
                f"Nodes:     {stats['node_count']}",
                f"Edges:     {stats['edge_count']}",
                f"Density:   {stats['density']:.4f}",
                f"Avg Degree: {stats['avg_degree']:.2f}",
                "",
                "Node Distribution:",
                "-" * 20
            ]
            
            for degree, count in stats['degree_dist'].items():
                lines.append(f"Degree {degree}: {count} nodes")
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting text graph: {e}")
            return str(e)
    
    def _format_json_graph(self, data: List[Dict[str, Any]]) -> str:
        """Format graph as JSON with metadata."""
        try:
            # Extract nodes and edges
            nodes, edges = self._extract_graph_elements(data)
            
            # Calculate statistics
            stats = self._calculate_graph_stats(nodes, edges)
            
            result = {
                'nodes': list(nodes),
                'edges': list(edges),
                'metadata': {
                    'statistics': stats,
                    'properties': self._calculate_graph_properties(nodes, edges)
                }
            }
            
            return json.dumps(result, indent=2)
        except Exception as e:
            self.logger.error(f"Error formatting JSON graph: {e}")
            return str(e)
    
    def _format_summary_graph(self, data: List[Dict[str, Any]]) -> str:
        """Format graph summary with key insights."""
        try:
            # Extract nodes and edges
            nodes, edges = self._extract_graph_elements(data)
            
            # Calculate statistics and properties
            stats = self._calculate_graph_stats(nodes, edges)
            props = self._calculate_graph_properties(nodes, edges)
            
            lines = [
                "Graph Summary",
                "=" * 50,
                "",
                "Basic Statistics:",
                "-" * 20,
                f"Number of Nodes: {stats['node_count']}",
                f"Number of Edges: {stats['edge_count']}",
                f"Graph Density:   {stats['density']:.4f}",
                "",
                "Properties:",
                "-" * 20,
                f"Connected:     {props['is_connected']}",
                f"Has Cycles:    {props['has_cycles']}",
                f"Max Path Len:  {props['max_path_length']}",
                "",
                "Structure:",
                "-" * 20,
                f"Clusters:      {props['cluster_count']}",
                f"Leaf Nodes:    {props['leaf_count']}",
                f"Bridge Edges:  {props['bridge_count']}"
            ]
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error formatting graph summary: {e}")
            return str(e)
    
    def _extract_graph_elements(self,
                              data: List[Dict[str, Any]]) -> tuple[set, set]:
        """Extract nodes and edges from graph data."""
        nodes = set()
        edges = set()
        
        for item in data:
            if 'source' in item and 'target' in item:
                # Edge data
                source = str(item['source'])
                target = str(item['target'])
                nodes.add(source)
                nodes.add(target)
                edges.add((source, target))
            elif 'id' in item:
                # Node data
                nodes.add(str(item['id']))
        
        return nodes, edges
    
    def _calculate_graph_stats(self,
                             nodes: set,
                             edges: set) -> Dict[str, Any]:
        """Calculate basic graph statistics."""
        node_count = len(nodes)
        edge_count = len(edges)
        
        # Calculate density
        max_edges = node_count * (node_count - 1) / 2
        density = edge_count / max_edges if max_edges > 0 else 0
        
        # Calculate degree distribution
        degree_dist = {}
        for node in nodes:
            degree = sum(1 for edge in edges if node in edge)
            degree_dist[degree] = degree_dist.get(degree, 0) + 1
        
        return {
            'node_count': node_count,
            'edge_count': edge_count,
            'density': density,
            'avg_degree': 2 * edge_count / node_count if node_count > 0 else 0,
            'degree_dist': degree_dist
        }
    
    def _calculate_graph_properties(self,
                                 nodes: set,
                                 edges: set) -> Dict[str, Any]:
        """Calculate advanced graph properties."""
        # Build adjacency list
        adj_list = {node: set() for node in nodes}
        for source, target in edges:
            adj_list[source].add(target)
            adj_list[target].add(source)
        
        # Check connectivity
        visited = set()
        def dfs(node):
            visited.add(node)
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs(neighbor)
        
        if nodes:
            dfs(next(iter(nodes)))
        is_connected = len(visited) == len(nodes)
        
        # Check for cycles
        has_cycles = False
        visited = set()
        path = set()
        
        def check_cycles(node, parent=None):
            nonlocal has_cycles
            visited.add(node)
            path.add(node)
            
            for neighbor in adj_list[node]:
                if neighbor == parent:
                    continue
                if neighbor in path:
                    has_cycles = True
                    return
                if neighbor not in visited:
                    check_cycles(neighbor, node)
            
            path.remove(node)
        
        for node in nodes:
            if node not in visited:
                check_cycles(node)
        
        # Count properties
        leaf_count = sum(1 for node in nodes if len(adj_list[node]) == 1)
        bridge_count = sum(
            1 for edge in edges
            if self._is_bridge(edge[0], edge[1], adj_list)
        )
        
        return {
            'is_connected': is_connected,
            'has_cycles': has_cycles,
            'max_path_length': self._find_max_path_length(adj_list),
            'cluster_count': self._count_clusters(nodes, edges),
            'leaf_count': leaf_count,
            'bridge_count': bridge_count
        }
    
    def _is_bridge(self,
                  u: str,
                  v: str,
                  adj_list: Dict[str, set]) -> bool:
        """Check if edge (u,v) is a bridge."""
        # Remove edge
        adj_list[u].remove(v)
        adj_list[v].remove(u)
        
        # Check if nodes are still connected
        visited = set()
        def dfs(node):
            visited.add(node)
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(u)
        is_bridge = v not in visited
        
        # Restore edge
        adj_list[u].add(v)
        adj_list[v].add(u)
        
        return is_bridge
    
    def _find_max_path_length(self, adj_list: Dict[str, set]) -> int:
        """Find length of longest path in graph."""
        max_length = 0
        visited = set()
        
        def dfs(node, length=0):
            nonlocal max_length
            visited.add(node)
            max_length = max(max_length, length)
            
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs(neighbor, length + 1)
            
            visited.remove(node)
        
        for node in adj_list:
            dfs(node)
        
        return max_length
    
    def _count_clusters(self, nodes: set, edges: set) -> int:
        """Count number of connected components."""
        # Build adjacency list
        adj_list = {node: set() for node in nodes}
        for source, target in edges:
            adj_list[source].add(target)
            adj_list[target].add(source)
        
        # Count components
        visited = set()
        count = 0
        
        def dfs(node):
            visited.add(node)
            for neighbor in adj_list[node]:
                if neighbor not in visited:
                    dfs(neighbor)
        
        for node in nodes:
            if node not in visited:
                count += 1
                dfs(node)
        
        return count 