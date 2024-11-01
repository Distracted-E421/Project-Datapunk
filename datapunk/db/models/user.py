from sqlalchemy import Column, String, Boolean, UUID, JSON, DateTime
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from geoalchemy2 import Geometry
from sqlalchemy.sql import func
from .base import BaseModel
import uuid

class User(BaseModel):
    # Use UUID instead of integer for ID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic fields
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    full_name = Column(String)
    hashed_password = Column(String, nullable=True)
    
    # OAuth related
    provider = Column(String)  # "local", "google", or "microsoft"
    provider_user_id = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    
    # Additional PostgreSQL-specific fields
    metadata = Column(JSONB, default={})  # Efficient JSON storage
    last_location = Column(Geometry('POINT', srid=4326), nullable=True)  # PostGIS
    search_vector = Column(ARRAY(float), nullable=True)  # pgvector compatibility
    
    # Timestamps
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Status
    disabled = Column(Boolean, default=False)
    
    # Add indexes for common queries
    __table_args__ = (
        # GiST index for geometric searches
        {'postgresql_using': 'gist'},
    )
