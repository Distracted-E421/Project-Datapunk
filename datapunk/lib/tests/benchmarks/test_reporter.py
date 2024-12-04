import pytest
from unittest.mock import Mock, patch, mock_open
import json
from datetime import datetime
from pathlib import Path
import plotly.graph_objects as go
from jinja2 import Environment

from datapunk_shared.benchmarks.reporter import BenchmarkReporter

@pytest.fixture
def sample_results():
    """Sample benchmark results for testing."""
    return [
        {
            "name": "test_operation_1",
            "operation": "read",
            "iterations": 100,
            "timings": {
                "mean": 0.001234,
                "median": 0.001000,
                "p95": 0.001500,
                "p99": 0.002000,
                "min": 0.000900,
                "max": 0.002500
            },
            "resources": {
                "memory_mb": 256.5,
                "cpu_percent": 45.2
            }
        },
        {
            "name": "test_operation_2",
            "operation": "write",
            "iterations": 100,
            "timings": {
                "mean": 0.002345,
                "median": 0.002100,
                "p95": 0.002800,
                "p99": 0.003200,
                "min": 0.001800,
                "max": 0.003500
            },
            "resources": {
                "memory_mb": 312.8,
                "cpu_percent": 65.7
            }
        }
    ]

@pytest.fixture
def mock_jinja_env():
    """Mock Jinja2 environment."""
    env = Mock(spec=Environment)
    template = Mock()
    template.render.return_value = "<html>Test Report</html>"
    env.get_template.return_value = template
    return env

@pytest.fixture
def reporter(tmp_path, mock_jinja_env):
    """Create BenchmarkReporter instance with mocked dependencies."""
    with patch('datapunk_shared.benchmarks.reporter.Environment') as mock_env:
        mock_env.return_value = mock_jinja_env
        reporter = BenchmarkReporter(str(tmp_path))
        return reporter

class TestBenchmarkReporter:
    def test_init_creates_results_directory(self, tmp_path):
        """Test that init creates the results directory if it doesn't exist."""
        results_dir = tmp_path / "benchmark_results"
        BenchmarkReporter(str(results_dir))
        assert results_dir.exists()
        assert results_dir.is_dir()

    def test_save_results(self, reporter, sample_results, tmp_path):
        """Test saving benchmark results to JSON file."""
        with patch('builtins.open', mock_open()) as mock_file:
            reporter.save_results(sample_results)
            
            # Verify file was opened for writing
            mock_file.assert_called_once()
            # Verify JSON was written with correct data
            written_data = json.loads(
                mock_file().write.call_args[0][0]
            )
            assert len(written_data) == 2
            assert written_data[0]["name"] == "test_operation_1"
            assert written_data[1]["name"] == "test_operation_2"

    def test_generate_html_report(self, reporter, sample_results, mock_jinja_env, tmp_path):
        """Test HTML report generation."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        with patch('pathlib.Path.write_text') as mock_write:
            report_path = reporter._generate_html_report(sample_results, timestamp)
            
            # Verify template was rendered
            template = mock_jinja_env.get_template.return_value
            template.render.assert_called_once()
            
            # Verify render args
            render_kwargs = template.render.call_args[1]
            assert render_kwargs["timestamp"] == timestamp
            assert render_kwargs["results"] == sample_results
            assert "timing_plot" in render_kwargs
            assert "resource_plot" in render_kwargs
            
            # Verify report was written
            mock_write.assert_called_once()
            assert isinstance(report_path, str)
            assert "report_" in report_path
            assert ".html" in report_path

    def test_generate_console_report(self, reporter, sample_results):
        """Test console report generation."""
        report = reporter._generate_console_report(sample_results)
        
        # Verify report content
        assert "Benchmark Results" in report
        assert "test_operation_1" in report
        assert "test_operation_2" in report
        assert "Timings (seconds):" in report
        assert "Resources:" in report
        
        # Verify metrics are included
        assert "Mean:" in report
        assert "Median:" in report
        assert "P95:" in report
        assert "P99:" in report
        assert "Memory:" in report
        assert "CPU:" in report

    def test_create_timing_plot(self, reporter, sample_results):
        """Test timing plot creation."""
        fig = reporter._create_timing_plot(sample_results)
        
        assert isinstance(fig, go.Figure)
        # Verify figure structure
        assert len(fig.data) == 4  # 2 bars + 2 box plots
        assert fig.data[0].type == "bar"  # Mean timing bars
        assert fig.data[1].type == "bar"  # P95 timing bars
        assert fig.data[2].type == "box"  # First operation box plot
        assert fig.data[3].type == "box"  # Second operation box plot

    def test_create_resource_plot(self, reporter, sample_results):
        """Test resource plot creation."""
        fig = reporter._create_resource_plot(sample_results)
        
        assert isinstance(fig, go.Figure)
        # Verify figure structure
        assert len(fig.data) == 2  # Memory bar + CPU bar
        assert fig.data[0].type == "bar"  # Memory usage bars
        assert fig.data[1].type == "bar"  # CPU usage bars
        
        # Verify data
        assert fig.data[0].y[0] == sample_results[0]["resources"]["memory_mb"]
        assert fig.data[1].y[0] == sample_results[0]["resources"]["cpu_percent"]

    def test_generate_report_html(self, reporter, sample_results):
        """Test report generation with HTML type."""
        with patch.object(reporter, '_generate_html_report') as mock_html:
            mock_html.return_value = "test_report.html"
            report = reporter.generate_report(sample_results, "html")
            
            mock_html.assert_called_once()
            assert report == "test_report.html"

    def test_generate_report_console(self, reporter, sample_results):
        """Test report generation with console type."""
        with patch.object(reporter, '_generate_console_report') as mock_console:
            mock_console.return_value = "Console Report"
            report = reporter.generate_report(sample_results, "console")
            
            mock_console.assert_called_once()
            assert report == "Console Report" 