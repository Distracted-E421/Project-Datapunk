import asyncio
import pytest
from typing import List, Dict, Any
from pathlib import Path
from datapunk_shared.benchmarks.reporter import BenchmarkReporter

async def run_benchmarks(
    test_path: str = "tests/benchmarks",
    report_type: str = "html"
) -> str:
    """Run benchmarks and generate report"""
    # Collect results
    results: List[Dict[str, Any]] = []
    
    # Run pytest with benchmark marker
    pytest.main([
        test_path,
        "-m", "benchmark",
        "--benchmark-only",
        "-v"
    ])
    
    # Generate report
    reporter = BenchmarkReporter()
    reporter.save_results(results)
    return reporter.generate_report(results, report_type)

if __name__ == "__main__":
    report_path = asyncio.run(run_benchmarks())
    print(f"Benchmark report generated: {report_path}") 