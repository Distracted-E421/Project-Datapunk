import pytest
from unittest.mock import patch

class TestExternalIntegrations:
    @pytest.mark.asyncio
    async def test_haystack_integration(self, nlp_pipeline):
        with patch('src.integrations.haystack.HaystackClient') as mock_client:
            mock_client.return_value.query.return_value = {"answer": "test"}
            result = await nlp_pipeline.query("test question")
            assert "answer" in result

    @pytest.mark.asyncio
    async def test_langchain_integration(self, nlp_pipeline):
        with patch('src.integrations.langchain.LangChainClient') as mock_client:
            mock_client.return_value.process.return_value = {"response": "test"}
            result = await nlp_pipeline.process_chain("test input")
            assert "response" in result
