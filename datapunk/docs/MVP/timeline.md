# Datapunk MVP Timeline

```python
WEEK_1 = {
    "Day 1-2": {
        "core_setup": {
            "database": """
                # PostgreSQL with pgvector ready to go
                CREATE EXTENSION IF NOT EXISTS vector;
                
                # Core tables with vector columns ready for later
                CREATE TABLE documents (
                    id SERIAL PRIMARY KEY,
                    content TEXT,
                    embedding vector(768),  # Ready for BERT embeddings
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """,
            "fastapi": {
                "main.py": "Basic CRUD endpoints",
                "auth.py": "Simple JWT authentication",
                "schemas.py": "Pydantic models with vector field support"
            }
        }
    },
    "Day 3-5": {
        "data_ingestion": {
            "google_takeout": {
                "parser.py": "Basic JSON/HTML parsing",
                "processor.py": "Async bulk upload support",
                "endpoints.py": "Upload and processing endpoints"
            }
        }
    }
}

WEEK_2 = {
    "Day 1-3": {
        "search_foundation": {
            "basic_search.py": """
                # Ready for both keyword and vector search
                async def search(
                    query: str,
                    search_type: Literal["keyword", "semantic"] = "keyword",
                    limit: int = 10
                ):
                    if search_type == "semantic":
                        # Placeholder for future AI embedding
                        pass
                    return await keyword_search(query, limit)
            """,
            "indexing.py": "Basic indexing utilities"
        }
    },
    "Day 4-5": {
        "visualization": {
            "timeline.py": "Basic timeline view of data",
            "stats.py": "Simple analytics endpoints"
        }
    }
}

WEEK_3 = {
    "Day 1-3": {
        "ui_basics": {
            "dashboard": "Simple data overview",
            "search": "Search interface with type toggle",
            "upload": "Drag-and-drop upload interface"
        }
    },
    "Day 4": {
        "testing": {
            "integration_tests": "Core functionality tests",
            "load_tests": "Basic performance validation"
        }
    },
    "Day 5": {
        "documentation": {
            "api_docs": "OpenAPI documentation",
            "setup_guide": "Installation instructions",
            "future_ai": "AI integration points documented"
        }
    }
}
```
