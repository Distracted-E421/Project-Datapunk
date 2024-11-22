import pytest
from src.nlp.pipeline import NLPPipeline

@pytest.fixture
async def nlp_pipeline():
    return NLPPipeline()

class TestNLPPipeline:
    @pytest.mark.asyncio
    async def test_sentiment_analysis_basic(self, nlp_pipeline):
        """Test basic sentiment analysis functionality"""
        text = "I love this product!"
        result = await nlp_pipeline.process(text, task="sentiment")
        
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis_neutral(self, nlp_pipeline):
        """Test sentiment analysis with neutral text"""
        text = "The sky is blue."
        result = await nlp_pipeline.process(text, task="sentiment")
        
        assert isinstance(result, dict)
        assert "sentiment" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, nlp_pipeline):
        """Test cache retrieval"""
        text = "test"
        # First call
        result1 = await nlp_pipeline.process(text, task="sentiment")
        # Second call should hit cache
        result2 = await nlp_pipeline.process(text, task="sentiment")
        
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_invalid_task(self, nlp_pipeline):
        """Test handling of invalid task"""
        with pytest.raises(ValueError, match="Unsupported task"):
            await nlp_pipeline.process("test", task="invalid_task")
            
    @pytest.mark.asyncio
    async def test_empty_text(self, nlp_pipeline):
        """Test handling of empty text"""
        with pytest.raises(ValueError, match="Empty text"):
            await nlp_pipeline.process("", task="sentiment")
