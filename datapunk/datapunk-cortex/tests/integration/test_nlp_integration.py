import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.core.neurocortex import NeuroCortex

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
async def neurocortex():
    config = {
        "neurocortex": {
            "cache": {"type": "memory"},
            "model_selection": {"strategy": "simple"},
            "integrations": {
                "haystack": {},
                "langchain": {}
            }
        }
    }
    return NeuroCortex(config)

class TestNLPIntegration:
    def test_sentiment_endpoint(self, test_client):
        """Test the sentiment analysis endpoint"""
        response = test_client.post(
            "/api/v1/nlp/analyze",
            json={"text": "I love this product!", "task": "sentiment"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sentiment" in data
        assert "confidence" in data
        
    def test_error_handling(self, test_client):
        """Test error handling for invalid requests"""
        response = test_client.post(
            "/api/v1/nlp/analyze",
            json={"text": "", "task": "sentiment"}
        )
        
        assert response.status_code == 400
        assert "error" in response.json()
        
    @pytest.mark.asyncio
    async def test_pipeline_integration(self, neurocortex):
        """Test NLP pipeline integration with NeuroCortex"""
        result = await neurocortex.process_request({
            "type": "nlp",
            "task": "sentiment",
            "text": "Great product!"
        })
        
        assert "sentiment" in result
        assert "confidence" in result
