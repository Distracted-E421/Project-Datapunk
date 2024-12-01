from typing import Dict, Any, List, Optional
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import json
from datetime import datetime
from ..distributed.node import PartitionNode
from ..distributed.coordinator import ClusterState

class TopologyVisualizer:
    """Visualizes cluster topology and partition distribution"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.node_positions = {}
        self.node_colors = {
            'active': '#2ecc71',
            'degraded': '#f1c40f',
            'unhealthy': '#e74c3c',
            'unknown': '#95a5a6'
        }
        
    def update_topology(self, cluster_state: ClusterState):
        """Update topology with current cluster state"""
        self.graph.clear()
        
        # Add nodes
        for node_id, node in cluster_state.nodes.items():
            self._add_node(node)
            
        # Add edges (connections between nodes)
        self._add_connections(cluster_state)
        
        # Update layout
        self._update_layout()
        
    def plot_topology(self, output_path: str,
                     title: str = "Cluster Topology",
                     width: int = 1200,
                     height: int = 800):
        """Generate interactive topology plot"""
        # Create plotly figure
        fig = go.Figure()
        
        # Add nodes
        node_x = []
        node_y = []
        node_colors = []
        node_sizes = []
        node_texts = []
        
        for node in self.graph.nodes():
            pos = self.node_positions[node]
            node_x.append(pos[0])
            node_y.append(pos[1])
            node_data = self.graph.nodes[node]
            node_colors.append(self.node_colors[node_data['status']])
            node_sizes.append(20 + len(node_data['partitions']) * 2)
            node_texts.append(self._create_node_text(node, node_data))
            
        fig.add_trace(go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers',
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color='white')
            ),
            text=node_texts,
            hoverinfo='text',
            name='Nodes'
        ))
        
        # Add edges
        edge_x = []
        edge_y = []
        edge_texts = []
        
        for edge in self.graph.edges():
            x0, y0 = self.node_positions[edge[0]]
            x1, y1 = self.node_positions[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            edge_data = self.graph.edges[edge]
            edge_texts.append(self._create_edge_text(edge, edge_data))
            
        fig.add_trace(go.Scatter(
            x=edge_x,
            y=edge_y,
            mode='lines',
            line=dict(width=1, color='#7f8c8d'),
            hoverinfo='text',
            text=edge_texts,
            name='Connections'
        ))
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=False,
            width=width,
            height=height,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white'
        )
        
        # Save plot
        fig.write_html(output_path)
        
    def plot_partition_distribution(self, output_path: str,
                                  title: str = "Partition Distribution"):
        """Generate partition distribution visualization"""
        # Create figure
        plt.figure(figsize=(12, 8))
        
        # Get partition counts
        node_ids = []
        partition_counts = []
        colors = []
        
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            node_ids.append(node)
            partition_counts.append(len(node_data['partitions']))
            colors.append(self.node_colors[node_data['status']])
            
        # Create bar plot
        plt.bar(node_ids, partition_counts, color=colors)
        plt.title(title)
        plt.xlabel("Node ID")
        plt.ylabel("Number of Partitions")
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Save plot
        plt.savefig(output_path)
        plt.close()
        
    def export_topology_data(self, output_path: str):
        """Export topology data as JSON"""
        data = {
            'nodes': [],
            'edges': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Export nodes
        for node in self.graph.nodes():
            node_data = self.graph.nodes[node]
            pos = self.node_positions[node]
            data['nodes'].append({
                'id': node,
                'status': node_data['status'],
                'partitions': list(node_data['partitions']),
                'metrics': node_data.get('metrics', {}),
                'position': {'x': pos[0], 'y': pos[1]}
            })
            
        # Export edges
        for edge in self.graph.edges():
            edge_data = self.graph.edges[edge]
            data['edges'].append({
                'source': edge[0],
                'target': edge[1],
                'metrics': edge_data.get('metrics', {})
            })
            
        # Write to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    def _add_node(self, node: PartitionNode):
        """Add node to topology graph"""
        self.graph.add_node(
            node.node_id,
            status=node.status,
            partitions=node.get_partitions(),
            metrics=node.metrics,
            capacity=node.capacity
        )
        
    def _add_connections(self, cluster_state: ClusterState):
        """Add connections between nodes"""
        # Add edges based on partition co-location
        partition_locations = cluster_state.partition_locations
        for partition_id, nodes in partition_locations.items():
            nodes = list(nodes)
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    if self.graph.has_edge(nodes[i], nodes[j]):
                        self.graph.edges[nodes[i], nodes[j]]['weight'] += 1
                    else:
                        self.graph.add_edge(nodes[i], nodes[j], weight=1)
                        
    def _update_layout(self):
        """Update node positions using force-directed layout"""
        self.node_positions = nx.spring_layout(self.graph)
        
    def _create_node_text(self, node_id: str,
                         node_data: Dict[str, Any]) -> str:
        """Create hover text for node"""
        return (
            f"Node: {node_id}<br>"
            f"Status: {node_data['status']}<br>"
            f"Partitions: {len(node_data['partitions'])}<br>"
            f"CPU Usage: {node_data['metrics'].get('cpu_usage', 0):.1f}%<br>"
            f"Memory Usage: {node_data['metrics'].get('memory_usage', 0):.1f}%<br>"
            f"Disk Usage: {node_data['metrics'].get('disk_usage', 0):.1f}%"
        )
        
    def _create_edge_text(self, edge: tuple,
                         edge_data: Dict[str, Any]) -> str:
        """Create hover text for edge"""
        return (
            f"Connection: {edge[0]} ↔ {edge[1]}<br>"
            f"Shared Partitions: {edge_data.get('weight', 0)}"
        )
        
    def get_topology_metrics(self) -> Dict[str, Any]:
        """Get metrics about the topology"""
        return {
            'node_count': self.graph.number_of_nodes(),
            'edge_count': self.graph.number_of_edges(),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes(),
            'density': nx.density(self.graph),
            'clustering_coefficient': nx.average_clustering(self.graph),
            'connected_components': nx.number_connected_components(self.graph)
        } 