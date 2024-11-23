# datapunk/containers/lake/src/storage/stores.py

from typing import Any, Dict, List, Optional, Union
import asyncpg
from asyncpg import Pool
import numpy as np
from datetime import datetime
from .base import BaseStore

class VectorStore(BaseStore):
    """Handles vector storage operations"""
    
    async def insert_vector(self, vector: np.ndarray, metadata: Dict[str, Any]) -> str:
        """Insert vector with metadata"""
        query = """
        INSERT INTO vectors (embedding, metadata)
        VALUES ($1, $2)
        RETURNING id;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, vector.tolist(), metadata)
    
    async def search_similar(self, vector: np.ndarray, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        query = """
        SELECT id, metadata, embedding <-> $1 as distance
        FROM vectors
        ORDER BY distance
        LIMIT $2;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, vector.tolist(), limit)

class TimeSeriesStore(BaseStore):
    """Handles time series data operations"""
    
    async def insert_metrics(self, metrics: Dict[str, Any], timestamp: datetime) -> str:
        """Insert time series metrics"""
        query = """
        INSERT INTO metrics (timestamp, data)
        VALUES ($1, $2)
        RETURNING id;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, timestamp, metrics)
    
    async def get_metrics(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Retrieve metrics for time range"""
        query = """
        SELECT * FROM metrics
        WHERE timestamp BETWEEN $1 AND $2
        ORDER BY timestamp;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, start_time, end_time)

class SpatialStore(BaseStore):
    """Handles spatial data operations"""
    
    async def insert_location(self, geom: Dict[str, Any], properties: Dict[str, Any]) -> str:
        """Insert spatial data"""
        query = """
        INSERT INTO locations (geom, properties)
        VALUES (ST_GeomFromGeoJSON($1), $2)
        RETURNING id;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, json.dumps(geom), properties)
    
    async def find_nearby(self, lat: float, lon: float, radius: float) -> List[Dict[str, Any]]:
        """Find locations within radius"""
        query = """
        SELECT id, properties,
               ST_AsGeoJSON(geom)::json as geometry,
               ST_Distance(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326)) as distance
        FROM locations
        WHERE ST_DWithin(geom, ST_SetSRID(ST_MakePoint($1, $2), 4326), $3)
        ORDER BY distance;
        """
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, lon, lat, radius)