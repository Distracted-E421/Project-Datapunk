# tests/nlp/cache/test_metrics.py
import pytest
from src.nlp.cache.metrics import CacheMetrics

class TestCacheMetrics:
    def test_hit_ratio_calculation(self):
        metrics = CacheMetrics()
        metrics.hits = 75
        metrics.misses = 25
        
        assert metrics.hit_ratio == 0.75
        
    def test_empty_metrics(self):
        metrics = CacheMetrics()
        assert metrics.hit_ratio == 0.0