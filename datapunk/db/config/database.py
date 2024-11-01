from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import text
from typing import AsyncGenerator
import os

# PostgreSQL specific connection string with additional parameters
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/datapunk"
    "?sslmode=disable"  # Adjust SSL mode as needed for your environment
)

# Configure engine with PostgreSQL-specific settings
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # SQL logging for development
    pool_size=20,  # Adjust based on your needs
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
    pool_timeout=30,  # Connection timeout in seconds
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False  # Recommended for async operations
)

Base: DeclarativeMeta = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            # Enable PostGIS for this session
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS postgis'))
            # Enable pgvector for vector operations
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            # Enable additional useful PostgreSQL extensions
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS pg_trgm'))  # For text search
            await session.execute(text('CREATE EXTENSION IF NOT EXISTS hstore'))  # For key-value storage
            
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
