
from typing import Dict, Any
from datetime import datetime

class EventValidator:
    @staticmethod
    def validate_timestamp(timestamp: datetime) -> bool:
        return timestamp is not None and timestamp <= datetime.now(timezone.utc)
    
    @staticmethod
    def validate_coordinates(lat: float, lng: float) -> bool:
        return -90 <= lat <= 90 and -180 <= lng <= 180
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: list) -> bool:
        return all(field in data for field in required_fields)