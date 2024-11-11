# tests/nlp/cache/test_storage.py
import pytest
from src.nlp.cache.storage import CacheStorage

class TestCacheStorage:
    @pytest.fixture
    def storage(self):
        return CacheStorage(max_size=100)
        
    def test_key_generation_consistency(self, storage):
        data = {"text": "test", "task": "sentiment"}
        key1 = storage._generate_key(data)
        key2 = storage._generate_key(data)
        
        assert key1 == key2