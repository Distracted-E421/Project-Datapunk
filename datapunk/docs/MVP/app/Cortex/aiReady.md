# AI-Ready Integration Points

```python
# Ready for immediate AI integration after MVP
AI_HOOKS = {
    "embedding_service": {
        "interface": """
        class EmbeddingService(Protocol):
            async def embed_text(self, text: str) -> List[float]:
                pass
        """,
        "implementations": [
            "DummyEmbedding",  # Returns zeros for MVP
            "SentenceTransformer",  # Ready to plug in
            "OpenAIEmbedding"  # Ready to plug in
        ]
    },
    
    "search_service": {
        "interface": """
        class SearchService(Protocol):
            async def search(
                self, 
                query: str,
                search_type: SearchType,
                limit: int = 10
            ) -> List[Document]:
                pass
        """,
        "implementations": [
            "KeywordSearch",  # MVP implementation
            "VectorSearch",   # Ready for when embeddings are added
            "HybridSearch"    # Ready for combining both
        ]
    }
}
```

```python
BONUS_AI_FEATURES = {
    "Week 3 - If Ahead": {
        "Day 4": {
            "basic_embeddings": {
                "model": "sentence-transformers/all-MiniLM-L6-v2",
                "batch_size": 32,
                "async_processing": True
            }
        },
        "Day 5": {
            "semantic_search": {
                "vector_search": True,
                "hybrid_search": False  # Save for later
            }
        }
    }
}
```
