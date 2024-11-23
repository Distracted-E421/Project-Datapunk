# datapunk/containers/lake/src/processing/validator.py

from typing import Any, Dict, List, Optional, Union
import json
from datetime import datetime
from pydantic import BaseModel, validator
import numpy as np

class DataValidator(BaseModel):
    """Validates data before storage in the Lake"""
    
    class Config:
        arbitrary_types_allowed = True
    
    @validator('*', pre=True)
    def check_null_values(cls, v):
        if v is None:
            raise ValueError("Null values are not allowed")
        return v
    
    @staticmethod
    def validate_vector(vector: Union[List[float], np.ndarray]) -> np.ndarray:
        """Validate vector data"""
        if isinstance(vector, list):
            vector = np.array(vector)
        if not isinstance(vector, np.ndarray):
            raise ValueError("Vector must be a numpy array or list")
        return vector
    
    @staticmethod
    def validate_timestamp(timestamp: Union[str, datetime]) -> datetime:
        """Validate timestamp data"""
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