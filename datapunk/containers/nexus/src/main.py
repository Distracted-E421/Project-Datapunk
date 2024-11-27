"""
Nexus Gateway Service Entry Point

This module initializes the Nexus Gateway service, which serves as the central routing
and authentication layer for the Datapunk platform. It handles cross-origin requests
and implements core middleware for the service mesh architecture.

NOTE: This service is a critical component in the Gateway Layer, managing all external
requests before routing them to internal services.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI with service identity for discovery and monitoring
app = FastAPI(title="DataPunk Nexus Service")

# Configure CORS to allow secure cross-origin requests
# TODO: Replace wildcard with environment-specific allowed origins
# FIXME: Implement stricter CORS policy for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Currently permissive for development
    allow_credentials=True,  # Required for authentication flows
    allow_methods=["*"],  # Supports all HTTP methods for API flexibility
    allow_headers=["*"],  # Allows custom headers for auth and tracking
)

@app.get("/health")
async def health_check():
    """
    Basic health check endpoint for container orchestration.
    
    NOTE: This is a minimal implementation. See health.py for the
    comprehensive health check system used by the service mesh.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    # Start server with production-grade uvicorn configuration
    # NOTE: Worker count and other settings should be environment-specific
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
