from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel

class NLPRequest(BaseModel):
    text: str
    task: str = "sentiment"

router = APIRouter(prefix="/api/v1/nlp")

@router.post("/analyze")
async def analyze_text(request: NLPRequest) -> Dict[str, Any]:
    try:
        result = await nlp_pipeline.process(
            text=request.text,
            task=request.task
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
