from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
from ...core.neurocortex import NeuroCortex

router = APIRouter()

@router.post("/")
async def predict(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    neurocortex: NeuroCortex
):
    """Handle synchronous prediction requests"""
    try:
        result = await neurocortex.process_request(request)
        background_tasks.add_task(log_prediction, request, result)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def predict_stream(
    request: Dict[str, Any],
    neurocortex: NeuroCortex
):
    """Handle streaming prediction requests"""
    request["streaming"] = True
    try:
        async for result in neurocortex.process_stream(request):
            yield result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))