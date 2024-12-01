from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
import logging
from datetime import datetime

from ..processing.validator import DataValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/processing", tags=["processing"])

class ValidationRequest(BaseModel):
    """Data validation request model"""
    data: Dict[str, Any]
    schema_name: str
    strict_mode: bool = False

class ValidationResponse(BaseModel):
    """Data validation response model"""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class TransformationRequest(BaseModel):
    """Data transformation request model"""
    data: Dict[str, Any]
    transformation_type: str
    options: Optional[Dict[str, Any]] = None

def init_processing_routes(validator: DataValidator):
    """Initialize processing routes with dependencies"""

    @router.post("/validate", response_model=ValidationResponse)
    async def validate_data(request: ValidationRequest):
        """Validate data against schema"""
        try:
            validation_result = await validator.validate(
                data=request.data,
                schema_name=request.schema_name,
                strict_mode=request.strict_mode
            )

            return ValidationResponse(
                is_valid=validation_result['is_valid'],
                errors=validation_result.get('errors', []),
                warnings=validation_result.get('warnings', []),
                metadata={
                    'schema_name': request.schema_name,
                    'strict_mode': request.strict_mode,
                    'timestamp': datetime.utcnow()
                }
            )
        except Exception as e:
            logger.error(f"Data validation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/validate/batch")
    async def validate_batch(file: UploadFile = File(...), schema_name: str = None):
        """Validate batch data from file"""
        try:
            batch_results = await validator.validate_batch(
                file=file,
                schema_name=schema_name
            )

            return {
                'total_records': batch_results['total'],
                'valid_records': batch_results['valid'],
                'invalid_records': batch_results['invalid'],
                'error_summary': batch_results['error_summary'],
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Batch validation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/transform")
    async def transform_data(request: TransformationRequest):
        """Transform data using specified transformation"""
        try:
            transformed_data = await validator.transform(
                data=request.data,
                transformation_type=request.transformation_type,
                options=request.options
            )

            return {
                'transformed_data': transformed_data,
                'transformation_type': request.transformation_type,
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Data transformation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/schemas")
    async def list_schemas():
        """List available validation schemas"""
        try:
            return {
                'schemas': await validator.list_schemas(),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to list schemas: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/transformations")
    async def list_transformations():
        """List available transformation types"""
        try:
            return {
                'transformations': await validator.list_transformations(),
                'timestamp': datetime.utcnow()
            }
        except Exception as e:
            logger.error(f"Failed to list transformations: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 