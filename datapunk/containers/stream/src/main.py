"""
Stream Service Entry Point

This module initializes the Stream Service, which handles real-time event processing
and distribution within the Datapunk platform. It configures CORS for secure
cross-origin communication and sets up basic health monitoring.

NOTE: This service is part of the Core Services layer, processing events from
various sources and maintaining stream state.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI with service identity for discovery and monitoring
app = FastAPI(title="DataPunk Stream Service")

# Configure CORS for secure cross-origin event streaming
# NOTE: Current configuration is permissive for development
# TODO: Implement environment-specific CORS policies
# FIXME: Add proper origin validation for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # Currently allows all origins
    allow_credentials=True,   # Required for WebSocket connections
    allow_methods=["*"],      # Supports all HTTP methods
    allow_headers=["*"],      # Allows custom headers for auth
)

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint for container orchestration.
    
    NOTE: This endpoint is used by Docker's health check system
    TODO: Add detailed health metrics for monitoring
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    # Start server with production-grade uvicorn configuration
    # NOTE: Port 8001 is reserved for Stream Service in the architecture
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 