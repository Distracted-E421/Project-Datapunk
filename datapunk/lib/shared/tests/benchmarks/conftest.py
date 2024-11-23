import pytest
import asyncio
import time
from typing import Dict, Any, Callable
from functools import wraps
import statistics
from dataclasses import dataclass
from datetime import datetime
import psutil

@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    operation: str
    iterations: int
    mean_time: float
    median_time: float
    p95_time: float
    p99_time: float
    min_time: float
    max_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "operation": self.operation,
            "iterations": self.iterations,
            "timings": {
                "mean": self.mean_time,
                "median": self.median_time,
                "p95": self.p95_time,
                "p99": self.p99_time,
                "min": self.min_time,
                "max": self.max_time
            },
            "resources": {
                "memory_mb": self.memory_usage,
                "cpu_percent": self.cpu_usage
            },
            "timestamp": self.timestamp.isoformat()
        }

def benchmark(iterations: int = 1000):
    """Decorator for benchmarking async functions"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            timings = []
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            start_cpu = psutil.Process().cpu_percent()
            
            for _ in range(iterations):
                start = time.perf_counter()
                await func(*args, **kwargs)
                end = time.perf_counter()
                timings.append(end - start)
            
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            end_cpu = psutil.Process().cpu_percent()
            
            sorted_timings = sorted(timings)
            result = BenchmarkResult(
                name=func.__name__,
                operation=func.__doc__ or "Unknown operation",
                iterations=iterations,
                mean_time=statistics.mean(timings),
                median_time=statistics.median(timings),
                p95_time=sorted_timings[int(0.95 * iterations)],
                p99_time=sorted_timings[int(0.99 * iterations)],
                min_time=min(timings),
                max_time=max(timings),
                memory_usage=end_memory - start_memory,
                cpu_usage=end_cpu - start_cpu,
                timestamp=datetime.utcnow()
            )
            
            return result
        return wrapper
    return decorator

@pytest.fixture
def benchmark_db():
    """Database for storing benchmark results"""
    return [] 