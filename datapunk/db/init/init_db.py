from ..config.database import engine, Base
from ..models.user import User
from sqlalchemy import text
import asyncio

async def init_db():
    async with engine.begin() as conn:
        # Create extensions first
        extensions = [
            'postgis',
            'vector',
            'uuid-ossp',
            'pg_trgm',
            'hstore',
            'postgis_topology',
            'postgis_raster',
            'fuzzystrmatch'  # Useful for fuzzy string matching
        ]
        
        for ext in extensions:
            try:
                await conn.execute(text(f'CREATE EXTENSION IF NOT EXISTS {ext}'))
                print(f"Extension {ext} created or already exists")
            except Exception as e:
                print(f"Warning: Could not create extension {ext}: {e}")

        # Drop all existing tables
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
