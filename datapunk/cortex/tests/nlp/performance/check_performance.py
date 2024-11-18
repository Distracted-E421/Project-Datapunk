# scripts/check_performance.py
import sys
import json

THRESHOLDS = {
    "latency_p95_ms": 200.0,  # 200ms
    "throughput_rps": 100.0,  # 100 requests/second
    "cache_hit_ratio": 0.95   # 95%
}

def check_performance(results_file):
    with open(results_file) as f:
        results = json.load(f)
        
    # Check against thresholds
    failures = []
    for metric, threshold in THRESHOLDS.items():
        if results[metric] > threshold:
            failures.append(f"{metric}: {results[metric]} > {threshold}")
            
    if failures:
        print("Performance test failures:")
        print("\n".join(failures))
        sys.exit(1)
    
    print("All performance metrics within thresholds")
    sys.exit(0)

if __name__ == "__main__":
    check_performance(sys.argv[1])