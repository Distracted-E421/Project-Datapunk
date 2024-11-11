# datapunk/datapunk-cortex/tests/conftest.py
import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.neurocortex import NeuroCortex

# Add src to Python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def nlp_pipeline():
    config = {
        "cache": {"type": "memory"},
        "model_selection": {"strategy": "simple"},
        "integrations": {
            "haystack": {"enabled": False},
            "langchain": {"enabled": False}
        }
    }
    return NeuroCortex(config)