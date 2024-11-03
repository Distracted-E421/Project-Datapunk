from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "datapunk-cortex"
    }

@router.get("/haystack")
async def haystack_health() -> Dict[str, Any]:
    """Check Haystack component health"""
    try:
        # Add actual Haystack health check logic here
        return {
            "status": "healthy",
            "component": "haystack"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

@router.get("/models")
async def models_health() -> Dict[str, Any]:
    """Check model service health"""
    return {
        "status": "healthy",
        "component": "model_service",
        "loaded_models": []  # Add actual model status here
    }

@router.get("/cache")
async def cache_health() -> Dict[str, Any]:
    """Check cache service health"""
    return {
        "status": "healthy",
        "component": "cache",
        "hit_rate": 0.0  # Add actual cache metrics here
    }