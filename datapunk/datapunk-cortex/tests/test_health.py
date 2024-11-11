import pytest
from fastapi.testclient import TestClient

def test_health_check(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_component_health(test_client):
    components = ["haystack", "langchain", "model_service"]
    for component in components:
        response = test_client.get(f"/health/{component}")
        assert response.status_code in [200, 503]
