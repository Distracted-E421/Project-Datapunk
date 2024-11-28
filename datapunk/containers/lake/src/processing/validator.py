# datapunk/containers/lake/src/processing/validator.py

# Core validation module for Lake service data integrity
# Ensures data quality and consistency across all storage engines
# Part of the Lake Service's Data Processing pipeline (see sys-arch.mmd)

from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime
from pydantic import BaseModel, validator
import numpy as np

class DataValidator(BaseModel):
    """
    Primary validation layer for Lake service data processing
    
    Handles validation for:
    - Vector data (for similarity search and ML models)
    - Temporal data (for time series analysis)
    - General data integrity checks
    
    NOTE: This validator is used by both Stream and Batch processing pipelines
    TODO: Add support for spatial data validation (PostGIS integration)
    """
    
    class Config:
        # Required for numpy array validation
        arbitrary_types_allowed = True
    
    @validator('*', pre=True)
    def check_null_values(cls, v):
        """
        Global null check for all fields
        IMPORTANT: Lake service requires non-null values for data integrity
        """
        if v is None:
            raise ValueError("Null values are not allowed")
        return v
    
    @staticmethod
    def validate_vector(vector: Union[List[float], np.ndarray]) -> np.ndarray:
        """
        Validates vector data for storage in pgvector
        
        NOTE: Vectors must be numpy arrays for efficient processing
        TODO: Add dimension validation based on model requirements
        """
        if isinstance(vector, list):
            vector = np.array(vector)
        if not isinstance(vector, np.ndarray):
            raise ValueError("Vector must be a numpy array or list")
        return vector
    
    @staticmethod
    def validate_timestamp(timestamp: Union[str, datetime]) -> datetime:
        """
        Validates timestamp data for TimescaleDB storage
        
        IMPORTANT: All timestamps are converted to UTC datetime objects
        NOTE: Accepts ISO format strings or datetime objects
        """
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp)
            except ValueError:
                raise ValueError("Invalid timestamp format")
        return timestamp
    
    @staticmethod
    def validate_geospatial(geom: Dict[str, Any]) -> Dict[str, Any]:
        """Validate geospatial data"""
        required_keys = ['type', 'coordinates']
        if not all(key in geom for key in required_keys):
            raise ValueError("Invalid GeoJSON format")
        return geom
    
    @staticmethod
    def validate_json(data: Union[str, Dict, List]) -> str:
        """Validate JSON data"""
        if isinstance(data, (dict, list)):
            return json.dumps(data)
        try:
            json.loads(data)
            return data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")