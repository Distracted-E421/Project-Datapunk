import pytest

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_invalid_input(self, nlp_pipeline):
        with pytest.raises(ValueError):
            await nlp_pipeline.process(None, task="sentiment")
            
    @pytest.mark.asyncio
    async def test_model_not_found(self, nlp_pipeline):
        with pytest.raises(KeyError):
            await nlp_pipeline.process("test", task="nonexistent_model")
            
    @pytest.mark.asyncio
    async def test_rate_limiting(self, nlp_pipeline):
        # Simulate rate limit exceeded
        for _ in range(100):
            await nlp_pipeline.process("test", task="sentiment")
        with pytest.raises(Exception, match="Rate limit exceeded"):
            await nlp_pipeline.process("test", task="sentiment")
