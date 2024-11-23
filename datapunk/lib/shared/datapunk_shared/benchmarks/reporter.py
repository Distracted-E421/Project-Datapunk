from typing import List, Dict, Any
import json
from datetime import datetime
import statistics
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from jinja2 import Environment, PackageLoader

class BenchmarkReporter:
    """Generate reports from benchmark results"""
    
    def __init__(self, results_dir: str = "benchmark_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.env = Environment(
            loader=PackageLoader('datapunk_shared', 'templates')
        )
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save raw benchmark results"""
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
        """Generate HTML report with visualizations"""
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
        """Generate console-friendly report"""
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
        """Create timing visualization"""
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
        """Create resource usage visualization"""
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