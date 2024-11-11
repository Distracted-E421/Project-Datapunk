# src/nlp/cache/metrics.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from statistics import mean

@dataclass
class CacheMetrics:
    """Cache performance metrics tracking"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    latencies: list[float] = field(default_factory=list)
    memory_usage_bytes: int = 0
    last_cleanup_time: Optional[datetime] = None
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
        
    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx]