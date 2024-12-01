import unittest
from datetime import datetime, timedelta
import numpy as np
from shapely.geometry import Polygon, Point
import tempfile
import os
from ..src.storage.index.strategies.partitioning.visualization import (
    TopologyVisualizer,
    MetricsVisualizer,
    DashboardManager,
    DashboardConfig,
    DashboardMetrics,
    PerformanceVisualizer,
    InteractiveVisualizer
)
from ..src.storage.index.strategies.partitioning.distributed import (
    ClusterState,
    PartitionNode
)

class TestTopologyVisualizer(unittest.TestCase):
    def setUp(self):
        self.visualizer = TopologyVisualizer()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_update_topology(self):
        """Test topology update with cluster state"""
        # Create mock cluster state
        nodes = {
            'node1': PartitionNode('node1', status='active', partitions=['p1', 'p2']),
            'node2': PartitionNode('node2', status='degraded', partitions=['p3'])
        }
        cluster_state = ClusterState(nodes=nodes)
        
        # Update topology
        self.visualizer.update_topology(cluster_state)
        
        # Verify graph structure
        self.assertEqual(len(self.visualizer.graph.nodes()), 2)
        self.assertTrue('node1' in self.visualizer.graph)
        self.assertTrue('node2' in self.visualizer.graph)
        
    def test_plot_topology(self):
        """Test topology plotting"""
        # Create mock cluster state
        nodes = {
            'node1': PartitionNode('node1', status='active', partitions=['p1', 'p2']),
            'node2': PartitionNode('node2', status='degraded', partitions=['p3'])
        }
        cluster_state = ClusterState(nodes=nodes)
        self.visualizer.update_topology(cluster_state)
        
        # Test plot generation
        output_path = os.path.join(self.temp_dir, 'topology.html')
        self.visualizer.plot_topology(output_path)
        self.assertTrue(os.path.exists(output_path))
        
    def test_export_topology_data(self):
        """Test topology data export"""
        # Create mock cluster state
        nodes = {
            'node1': PartitionNode('node1', status='active', partitions=['p1', 'p2']),
            'node2': PartitionNode('node2', status='degraded', partitions=['p3'])
        }
        cluster_state = ClusterState(nodes=nodes)
        self.visualizer.update_topology(cluster_state)
        
        # Test export
        output_path = os.path.join(self.temp_dir, 'topology.json')
        self.visualizer.export_topology_data(output_path)
        self.assertTrue(os.path.exists(output_path))

class TestMetricsVisualizer(unittest.TestCase):
    def setUp(self):
        self.visualizer = MetricsVisualizer()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_add_metrics(self):
        """Test adding metrics data"""
        node_id = 'node1'
        metrics = {
            'cpu_usage': 50.0,
            'memory_usage': 60.0,
            'disk_usage': 70.0,
            'network_io': 1000,
            'iops': 100,
            'partition_count': 5
        }
        
        self.visualizer.add_metrics(node_id, metrics)
        self.assertTrue(node_id in self.visualizer.metrics_history)
        self.assertEqual(len(self.visualizer.metrics_history[node_id]), 1)
        
    def test_plot_node_metrics(self):
        """Test node metrics plotting"""
        # Add sample metrics
        node_id = 'node1'
        for i in range(10):
            metrics = {
                'cpu_usage': 50.0 + i,
                'memory_usage': 60.0 + i,
                'disk_usage': 70.0 + i,
                'network_io': 1000 + i * 100,
                'iops': 100 + i * 10,
                'partition_count': 5 + i
            }
            self.visualizer.add_metrics(node_id, metrics)
            
        # Test plot generation
        output_path = os.path.join(self.temp_dir, 'node_metrics.html')
        self.visualizer.plot_node_metrics(output_path, node_id)
        self.assertTrue(os.path.exists(output_path))
        
    def test_plot_cluster_overview(self):
        """Test cluster overview plotting"""
        # Add sample metrics for multiple nodes
        for node_id in ['node1', 'node2']:
            for i in range(10):
                metrics = {
                    'cpu_usage': 50.0 + i,
                    'memory_usage': 60.0 + i,
                    'disk_usage': 70.0 + i,
                    'network_io': 1000 + i * 100,
                    'iops': 100 + i * 10,
                    'partition_count': 5 + i,
                    'status': 'active'
                }
                self.visualizer.add_metrics(node_id, metrics)
                
        # Test plot generation
        output_path = os.path.join(self.temp_dir, 'cluster_overview.html')
        self.visualizer.plot_cluster_overview(output_path)
        self.assertTrue(os.path.exists(output_path))

class TestPerformanceVisualizer(unittest.TestCase):
    def setUp(self):
        self.visualizer = PerformanceVisualizer()
        self.temp_dir = tempfile.mkdtemp()
        
    def test_add_performance_data(self):
        """Test adding performance data"""
        operation = 'query1'
        metrics = {
            'latency': 100.0,
            'throughput': 1000,
            'cpu_usage': 50.0,
            'memory_usage': 60.0
        }
        
        self.visualizer.add_performance_data(operation, metrics)
        self.assertTrue(operation in self.visualizer.performance_data)
        
    def test_plot_latency_distribution(self):
        """Test latency distribution plotting"""
        # Add sample performance data
        operation = 'query1'
        for i in range(100):
            metrics = {
                'latency': 100.0 + np.random.normal(0, 10),
                'throughput': 1000 + np.random.normal(0, 100),
                'cpu_usage': 50.0 + np.random.normal(0, 5),
                'memory_usage': 60.0 + np.random.normal(0, 5)
            }
            self.visualizer.add_performance_data(operation, metrics)
            
        # Test plot generation
        output_path = os.path.join(self.temp_dir, 'latency_dist.html')
        self.visualizer.plot_latency_distribution(output_path)
        self.assertTrue(os.path.exists(output_path))
        
    def test_analyze_performance_anomalies(self):
        """Test performance anomaly detection"""
        # Add sample performance data with anomalies
        operation = 'query1'
        for i in range(100):
            latency = 100.0 + np.random.normal(0, 10)
            if i > 90:  # Add anomalies
                latency += 100.0
                
            metrics = {
                'latency': latency,
                'throughput': 1000 + np.random.normal(0, 100)
            }
            self.visualizer.add_performance_data(operation, metrics)
            
        # Test anomaly detection
        anomalies = self.visualizer.analyze_performance_anomalies(operation)
        self.assertTrue(len(anomalies) > 0)
        
    def test_establish_performance_baseline(self):
        """Test performance baseline establishment"""
        # Add sample performance data
        operation = 'query1'
        for i in range(100):
            metrics = {
                'latency': 100.0 + np.random.normal(0, 10),
                'throughput': 1000 + np.random.normal(0, 100)
            }
            self.visualizer.add_performance_data(operation, metrics)
            
        # Establish baseline
        self.visualizer.establish_performance_baseline(operation)
        self.assertTrue(operation in self.visualizer.baseline_stats)
        self.assertTrue('latency' in self.visualizer.baseline_stats[operation])
        self.assertTrue('throughput' in self.visualizer.baseline_stats[operation])

class TestDashboardManager(unittest.TestCase):
    def setUp(self):
        self.topology_viz = TopologyVisualizer()
        self.metrics_viz = MetricsVisualizer()
        self.dashboard = DashboardManager(self.topology_viz, self.metrics_viz)
        
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard.app)
        self.assertIsNotNone(self.dashboard.topology_viz)
        self.assertIsNotNone(self.dashboard.metrics_viz)
        
    def test_dashboard_config(self):
        """Test dashboard configuration"""
        config = DashboardConfig()
        self.assertEqual(config.update_interval, 5)
        self.assertEqual(config.default_time_range, '1H')
        
    def test_dashboard_metrics(self):
        """Test dashboard metrics tracking"""
        metrics = DashboardMetrics()
        
        # Record some metrics
        metrics.record_update(0.1)
        metrics.record_error()
        
        # Check metrics
        stats = metrics.get_metrics()
        self.assertEqual(stats['update_count'], 1)
        self.assertEqual(stats['error_count'], 1)
        self.assertAlmostEqual(stats['avg_update_time'], 0.1)

class TestInteractiveVisualizer(unittest.TestCase):
    def setUp(self):
        self.topology_viz = TopologyVisualizer()
        self.metrics_viz = MetricsVisualizer()
        self.performance_viz = PerformanceVisualizer()
        self.visualizer = InteractiveVisualizer(
            self.topology_viz,
            self.metrics_viz,
            self.performance_viz
        )
        self.temp_dir = tempfile.mkdtemp()
        
    def test_initialization(self):
        """Test interactive visualizer initialization"""
        self.assertIsNotNone(self.visualizer.app)
        self.assertIsNotNone(self.visualizer.topology_viz)
        self.assertIsNotNone(self.visualizer.metrics_viz)
        self.assertIsNotNone(self.visualizer.performance_viz)
        self.assertEqual(self.visualizer.update_interval, 5)
        
    def test_state_management(self):
        """Test visualization state management"""
        # Set some state
        self.visualizer.selected_nodes = {'node1', 'node2'}
        self.visualizer.selected_metrics = {'cpu_usage', 'memory_usage'}
        self.visualizer.time_window = '6H'
        
        # Export state
        state_path = os.path.join(self.temp_dir, 'viz_state.json')
        self.visualizer.export_visualization_state(state_path)
        self.assertTrue(os.path.exists(state_path))
        
        # Clear state
        self.visualizer.selected_nodes.clear()
        self.visualizer.selected_metrics.clear()
        self.visualizer.time_window = '1H'
        
        # Import state
        self.visualizer.import_visualization_state(state_path)
        self.assertEqual(self.visualizer.selected_nodes, {'node1', 'node2'})
        self.assertEqual(self.visualizer.selected_metrics, 
                        {'cpu_usage', 'memory_usage'})
        self.assertEqual(self.visualizer.time_window, '6H')
        
    def test_time_range_parsing(self):
        """Test time range parsing"""
        self.assertEqual(
            self.visualizer._parse_time_range('1H'),
            timedelta(hours=1)
        )
        self.assertEqual(
            self.visualizer._parse_time_range('6H'),
            timedelta(hours=6)
        )
        self.assertEqual(
            self.visualizer._parse_time_range('24H'),
            timedelta(hours=24)
        )
        self.assertEqual(
            self.visualizer._parse_time_range('7D'),
            timedelta(days=7)
        )
        
    def test_view_creation(self):
        """Test view creation methods"""
        # Add some test data
        node_id = 'node1'
        metrics = {
            'cpu_usage': 50.0,
            'memory_usage': 60.0,
            'latency': 100.0,
            'throughput': 1000
        }
        self.metrics_viz.add_metrics(node_id, metrics)
        self.performance_viz.add_performance_data(node_id, metrics)
        
        # Set selections
        self.visualizer.selected_nodes = {node_id}
        self.visualizer.selected_metrics = {'cpu_usage', 'memory_usage'}
        
        # Test view creation
        topology_view = self.visualizer._create_topology_view()
        self.assertIsNotNone(topology_view)
        
        metrics_view = self.visualizer._create_metrics_view()
        self.assertIsNotNone(metrics_view)
        
        latency_dist = self.visualizer._create_latency_distribution()
        self.assertIsNotNone(latency_dist)
        
        resource_corr = self.visualizer._create_resource_correlation()
        self.assertIsNotNone(resource_corr)
        
        perf_trends = self.visualizer._create_performance_trends()
        self.assertIsNotNone(perf_trends)
        
    def test_anomaly_alerts(self):
        """Test anomaly alert creation"""
        # Add normal data
        node_id = 'node1'
        for i in range(90):
            metrics = {
                'latency': 100.0 + np.random.normal(0, 10),
                'throughput': 1000 + np.random.normal(0, 100)
            }
            self.performance_viz.add_performance_data(node_id, metrics)
            
        # Add anomalous data
        for i in range(10):
            metrics = {
                'latency': 300.0 + np.random.normal(0, 10),
                'throughput': 500 + np.random.normal(0, 100)
            }
            self.performance_viz.add_performance_data(node_id, metrics)
            
        self.visualizer.selected_nodes = {node_id}
        alerts = self.visualizer._create_anomaly_alerts()
        self.assertTrue(len(alerts) > 0)

if __name__ == '__main__':
    unittest.main() 