from typing import List, Dict, Any
import json
from datetime import datetime
import statistics
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jinja2 import Environment, PackageLoader

class BenchmarkReporter:
    """A comprehensive benchmark reporting system that generates both HTML and console-based 
    performance reports with visualizations.
    
    This class handles the collection, analysis, and visualization of benchmark results,
    supporting both timing metrics and resource utilization data. It uses Plotly for
    interactive visualizations and Jinja2 for HTML report templating.
    
    Note: Requires a 'templates' directory with appropriate Jinja2 templates.
    """
    
    def __init__(self, results_dir: str = "benchmark_results"):
        """
        Args:
            results_dir: Directory path for storing benchmark results and reports.
                        Created if it doesn't exist.
        """
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        # Initialize Jinja2 environment for HTML templating
        # NOTE: Assumes templates are packaged with datapunk_shared
        self.env = Environment(
            loader=PackageLoader('datapunk_shared', 'templates')
        )
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Persists raw benchmark results as JSON for future analysis or comparison.
        
        The results are stored with a UTC timestamp to ensure unique filenames and 
        enable chronological tracking of performance changes.
        
        Args:
            results: List of benchmark result dictionaries containing timing and resource metrics
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"benchmark_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def generate_report(self, results: List[Dict[str, Any]], report_type: str = "html"):
        """Generate benchmark report"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        if report_type == "html":
            return self._generate_html_report(results, timestamp)
        else:
            return self._generate_console_report(results)
    
    def _generate_html_report(self, results: List[Dict[str, Any]], timestamp: str):
        """Generates an interactive HTML report with visualizations and detailed metrics.
        
        The report includes:
        - Interactive Plotly visualizations for timing and resource metrics
        - Detailed benchmark results in a structured format
        - Timestamp for tracking when the benchmarks were run
        
        TODO: Add export functionality for different visualization formats (PNG, SVG)
        TODO: Add comparison with historical benchmark results
        
        Args:
            results: List of benchmark results to include in the report
            timestamp: UTC timestamp string for the report
            
        Returns:
            Path to the generated HTML report file
        """
        # Create figures
        timing_fig = self._create_timing_plot(results)
        resource_fig = self._create_resource_plot(results)
        
        # Generate HTML
        template = self.env.get_template('benchmark_report.html')
        html_content = template.render(
            timestamp=timestamp,
            results=results,
            timing_plot=timing_fig.to_html(full_html=False),
            resource_plot=resource_fig.to_html(full_html=False)
        )
        
        # Save report
        report_file = self.results_dir / f"report_{timestamp}.html"
        report_file.write_text(html_content)
        return str(report_file)
    
    def _generate_console_report(self, results: List[Dict[str, Any]]) -> str:
        """Generates a text-based report suitable for terminal output.
        
        Includes key statistics for each benchmark:
        - Timing metrics (mean, median, P95, P99)
        - Resource utilization (memory, CPU)
        
        This format is particularly useful for CI/CD pipelines or quick analysis.
        
        Args:
            results: List of benchmark results to report
            
        Returns:
            Formatted string containing the benchmark report
        """
        report_lines = ["Benchmark Results", "================="]
        
        for result in results:
            report_lines.extend([
                f"\nTest: {result['name']} ({result['operation']})",
                f"Iterations: {result['iterations']}",
                "\nTimings (seconds):",
                f"  Mean:   {result['timings']['mean']:.6f}",
                f"  Median: {result['timings']['median']:.6f}",
                f"  P95:    {result['timings']['p95']:.6f}",
                f"  P99:    {result['timings']['p99']:.6f}",
                "\nResources:",
                f"  Memory: {result['resources']['memory_mb']:.2f} MB",
                f"  CPU:    {result['resources']['cpu_percent']:.1f}%",
                "-" * 50
            ])
        
        return "\n".join(report_lines)
    
    def _create_timing_plot(self, results: List[Dict[str, Any]]) -> go.Figure:
        """Creates a two-panel visualization of timing metrics using Plotly.
        
        Top panel: Bar chart comparing mean and P95 timings across operations
        Bottom panel: Box plots showing timing distributions (min, median, max)
        
        Args:
            results: List of benchmark results to visualize
            
        Returns:
            Plotly Figure object containing the timing visualizations
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Operation Timings", "Timing Distribution")
        )
        
        # Add timing bars
        names = [r['name'] for r in results]
        mean_times = [r['timings']['mean'] for r in results]
        p95_times = [r['timings']['p95'] for r in results]
        
        fig.add_trace(
            go.Bar(name="Mean", x=names, y=mean_times),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(name="P95", x=names, y=p95_times),
            row=1, col=1
        )
        
        # Add box plots
        for result in results:
            fig.add_trace(
                go.Box(
                    name=result['name'],
                    y=[result['timings']['min'], 
                       result['timings']['median'],
                       result['timings']['max']]
                ),
                row=2, col=1
            )
        
        fig.update_layout(height=800, showlegend=True)
        return fig
    
    def _create_resource_plot(self, results: List[Dict[str, Any]]) -> go.Figure:
        """Creates a side-by-side visualization of memory and CPU usage metrics.
        
        Left panel: Memory usage in MB
        Right panel: CPU utilization percentage
        
        This visualization helps identify resource-intensive operations and potential
        optimization targets.
        
        Args:
            results: List of benchmark results to visualize
            
        Returns:
            Plotly Figure object containing the resource usage visualizations
        """
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Memory Usage (MB)", "CPU Usage (%)")
        )
        
        names = [r['name'] for r in results]
        memory = [r['resources']['memory_mb'] for r in results]
        cpu = [r['resources']['cpu_percent'] for r in results]
        
        fig.add_trace(
            go.Bar(x=names, y=memory),
            row=1, col=1
        )
        fig.add_trace(
            go.Bar(x=names, y=cpu),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        return fig 