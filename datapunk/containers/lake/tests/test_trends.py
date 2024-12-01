import unittest
from datetime import datetime, timedelta
import tempfile
import os
import numpy as np
import pandas as pd

from ..src.storage.index.stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    StatisticsStore
)
from ..src.storage.index.trends import (
    TrendAnalyzer,
    TrendType,
    Seasonality,
    Anomaly,
    Forecast,
    TrendAnalysis
)

class TestTrendAnalyzer(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_stats.db")
        
        # Initialize store and analyzer
        self.store = StatisticsStore(self.db_path)
        self.analyzer = TrendAnalyzer(self.store)
        
        # Create sample data
        self._create_sample_data()
        
    def tearDown(self):
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
        
    def _create_sample_data(self):
        """Create sample historical data for testing."""
        base_time = datetime.now() - timedelta(days=30)
        
        # Create trend data
        for i in range(720):  # 30 days of hourly data
            # Add seasonal pattern
            hour = i % 24
            seasonal_factor = np.sin(2 * np.pi * hour / 24)
            
            # Add trend
            trend_factor = i / 100
            
            # Add noise
            noise = np.random.normal(0, 0.1)
            
            stats = IndexStats(
                index_name="test_index",
                table_name="test_table",
                index_type="btree",
                created_at=base_time + timedelta(hours=i),
                usage=IndexUsageStats(
                    total_reads=1000 + i * 10,
                    total_writes=500 + i * 5,
                    avg_read_time_ms=1.0 + trend_factor + seasonal_factor + noise,
                    avg_write_time_ms=2.0 + trend_factor + seasonal_factor + noise,
                    cache_hits=800 + i * 8,
                    cache_misses=200 + i * 2
                ),
                size=IndexSizeStats(
                    total_entries=10000 + i * 100,
                    depth=4,
                    size_bytes=102400 + i * 1024,
                    fragmentation_ratio=0.1 + i * 0.001
                ),
                condition=IndexConditionStats(
                    condition_string="status = 'active'",
                    selectivity=0.3 + trend_factor + noise,
                    false_positive_rate=0.1 + trend_factor + noise,
                    evaluation_time_ms=0.3 + trend_factor + seasonal_factor + noise
                )
            )
            self.store.save_stats(stats)
            
        # Add some anomalies
        anomaly_times = [
            base_time + timedelta(days=10),
            base_time + timedelta(days=20)
        ]
        
        for time in anomaly_times:
            stats = IndexStats(
                index_name="test_index",
                table_name="test_table",
                index_type="btree",
                created_at=time,
                usage=IndexUsageStats(
                    total_reads=10000,  # Anomalous spike
                    total_writes=5000,
                    avg_read_time_ms=10.0,  # Anomalous spike
                    avg_write_time_ms=20.0,  # Anomalous spike
                    cache_hits=8000,
                    cache_misses=2000
                ),
                size=IndexSizeStats(
                    total_entries=100000,
                    depth=4,
                    size_bytes=1024000,
                    fragmentation_ratio=0.5
                ),
                condition=IndexConditionStats(
                    condition_string="status = 'active'",
                    selectivity=0.8,
                    false_positive_rate=0.5,
                    evaluation_time_ms=1.0
                )
            )
            self.store.save_stats(stats)
            
    def test_performance_trend_analysis(self):
        analysis = self.analyzer.analyze_performance_trends("test_index")
        
        # Verify trend detection
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.trend_type, TrendType.INCREASING)
        self.assertGreater(analysis.slope, 0)
        self.assertGreater(analysis.r_squared, 0.7)  # Strong fit
        
        # Verify seasonality detection
        self.assertIsNotNone(analysis.seasonality)
        self.assertEqual(analysis.seasonality.period, 24)
        self.assertGreater(analysis.seasonality.strength, 0)
        self.assertTrue(len(analysis.seasonality.peaks) > 0)
        
        # Verify anomaly detection
        self.assertTrue(len(analysis.anomalies) > 0)
        for anomaly in analysis.anomalies:
            self.assertGreater(anomaly.deviation, 3)
            
        # Verify forecast
        self.assertIsNotNone(analysis.forecast)
        self.assertEqual(len(analysis.forecast.timestamps), 24)
        self.assertTrue(all(
            lower <= value <= upper
            for lower, value, upper in zip(
                analysis.forecast.confidence_lower,
                analysis.forecast.values,
                analysis.forecast.confidence_upper
            )
        ))
        
    def test_growth_pattern_analysis(self):
        analysis = self.analyzer.analyze_growth_patterns("test_index")
        
        self.assertIsNotNone(analysis)
        self.assertEqual(analysis.trend_type, TrendType.INCREASING)
        
        # Verify growth metrics
        self.assertGreater(analysis.slope, 0)
        self.assertGreater(analysis.r_squared, 0.9)  # Very strong fit for linear growth
        
        # Verify change points
        self.assertTrue(len(analysis.change_points) > 0)
        
    def test_condition_effectiveness_analysis(self):
        analysis = self.analyzer.analyze_condition_effectiveness("test_index")
        
        self.assertIsNotNone(analysis)
        self.assertTrue(len(analysis.anomalies) > 0)
        
        # Verify correlation matrix
        self.assertIn('selectivity', analysis.correlation_matrix)
        self.assertIn('false_positives', analysis.correlation_matrix)
        
    def test_trend_type_detection(self):
        # Test increasing trend
        series = pd.Series(np.linspace(0, 10, 100))
        trend_type = self.analyzer._determine_trend_type(series)
        self.assertEqual(trend_type, TrendType.INCREASING)
        
        # Test decreasing trend
        series = pd.Series(np.linspace(10, 0, 100))
        trend_type = self.analyzer._determine_trend_type(series)
        self.assertEqual(trend_type, TrendType.DECREASING)
        
        # Test stable trend
        series = pd.Series(np.ones(100))
        trend_type = self.analyzer._determine_trend_type(series)
        self.assertEqual(trend_type, TrendType.STABLE)
        
        # Test cyclic trend
        x = np.linspace(0, 4*np.pi, 100)
        series = pd.Series(np.sin(x))
        trend_type = self.analyzer._determine_trend_type(series)
        self.assertEqual(trend_type, TrendType.CYCLIC)
        
        # Test fluctuating trend
        series = pd.Series(np.random.normal(0, 1, 100))
        trend_type = self.analyzer._determine_trend_type(series)
        self.assertEqual(trend_type, TrendType.FLUCTUATING)
        
    def test_seasonality_detection(self):
        # Create data with known seasonality
        timestamps = pd.date_range(
            start=datetime.now(),
            periods=100,
            freq='H'
        )
        values = np.sin(2 * np.pi * np.arange(100) / 24)  # 24-hour cycle
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        
        seasonality = self.analyzer._detect_seasonality(df)
        
        self.assertIsNotNone(seasonality)
        self.assertEqual(seasonality.period, 24)
        self.assertGreater(seasonality.strength, 0.5)
        
    def test_anomaly_detection(self):
        # Create normal data with known anomalies
        data = np.random.normal(0, 1, 100)
        data[50] = 10  # Add obvious anomaly
        
        df = pd.DataFrame({
            'timestamp': pd.date_range(
                start=datetime.now(),
                periods=100,
                freq='H'
            ),
            'value': data
        })
        
        anomalies = self.analyzer._detect_anomalies(df)
        
        self.assertTrue(len(anomalies) > 0)
        self.assertGreater(anomalies[0].deviation, 3)
        
    def test_forecast_generation(self):
        # Create data with trend and seasonality
        timestamps = pd.date_range(
            start=datetime.now(),
            periods=100,
            freq='H'
        )
        trend = np.linspace(0, 10, 100)
        seasonal = np.sin(2 * np.pi * np.arange(100) / 24)
        values = trend + seasonal + np.random.normal(0, 0.1, 100)
        
        df = pd.DataFrame({
            'timestamp': timestamps,
            'value': values
        })
        
        forecast = self.analyzer._generate_forecast(df)
        
        self.assertIsNotNone(forecast)
        self.assertEqual(len(forecast.timestamps), 24)
        self.assertEqual(len(forecast.values), 24)
        self.assertEqual(len(forecast.confidence_lower), 24)
        self.assertEqual(len(forecast.confidence_upper), 24)
        
    def test_change_point_detection(self):
        # Create data with known change points
        data = np.concatenate([
            np.ones(50),
            np.ones(50) * 2
        ])
        
        df = pd.DataFrame({
            'timestamp': pd.date_range(
                start=datetime.now(),
                periods=100,
                freq='H'
            ),
            'value': data
        })
        
        change_points = self.analyzer._detect_change_points(df)
        
        self.assertTrue(len(change_points) > 0)
        # Change point should be near index 50
        expected_time = df['timestamp'].iloc[50]
        self.assertTrue(any(
            abs((cp - expected_time).total_seconds()) < 3600
            for cp in change_points
        )) 