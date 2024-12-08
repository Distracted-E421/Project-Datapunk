from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
from datetime import datetime

from ..query.parser.query_parser_sql import SQLParser
from ..query.parser.query_parser_nosql import NoSQLParser
from ..query.validation.validation_sql import SQLValidator
from ..query.validation.validation_nosql import NoSQLValidator
from ..query.optimizer.optimizer_core import QueryOptimizer
from ..query.executor.query_exec_core import QueryExecutor
from ..query.executor.streaming import StreamingExecutor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    query_type: str  # "sql" or "nosql"
    parameters: Optional[Dict[str, Any]] = None
    streaming: bool = False
    timeout_seconds: Optional[int] = None

class QueryResponse(BaseModel):
    """Query response model"""
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    execution_time_ms: float

class StreamingQueryResponse(BaseModel):
    """Streaming query response model"""
    stream_id: str
    metadata: Dict[str, Any]

def init_query_routes(
    sql_parser: SQLParser,
    nosql_parser: NoSQLParser,
    sql_validator: SQLValidator,
    nosql_validator: NoSQLValidator,
    optimizer: QueryOptimizer,
    executor: QueryExecutor,
    streaming_executor: StreamingExecutor
):
    """Initialize query routes with dependencies"""

    @router.post("/execute", response_model=QueryResponse)
    async def execute_query(request: QueryRequest):
        """Execute a SQL or NoSQL query"""
        try:
            start_time = datetime.now()

            # Parse query
            if request.query_type == "sql":
                parsed_query = sql_parser.parse(request.query)
                sql_validator.validate(parsed_query)
            else:
                parsed_query = nosql_parser.parse(request.query)
                nosql_validator.validate(parsed_query)

            # Optimize query
            optimized_query = optimizer.optimize(parsed_query)

            # Execute query
            results = await executor.execute(
                query=optimized_query,
                parameters=request.parameters,
                timeout_seconds=request.timeout_seconds
            )

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return QueryResponse(
                results=results,
                metadata={
                    'query_type': request.query_type,
                    'optimizations_applied': optimizer.get_applied_optimizations(),
                    'rows_processed': len(results)
                },
                execution_time_ms=execution_time
            )
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/stream", response_model=StreamingQueryResponse)
    async def stream_query(request: QueryRequest, background_tasks: BackgroundTasks):
        """Execute a streaming query"""
        try:
            if not request.streaming:
                raise HTTPException(
                    status_code=400,
                    detail="Streaming must be enabled for this endpoint"
                )

            # Parse and validate query
            if request.query_type == "sql":
                parsed_query = sql_parser.parse(request.query)
                sql_validator.validate(parsed_query)
            else:
                parsed_query = nosql_parser.parse(request.query)
                nosql_validator.validate(parsed_query)

            # Optimize query
            optimized_query = optimizer.optimize(parsed_query)

            # Start streaming execution in background
            stream_id = await streaming_executor.start_stream(
                query=optimized_query,
                parameters=request.parameters
            )

            background_tasks.add_task(
                streaming_executor.process_stream,
                stream_id=stream_id
            )

            return StreamingQueryResponse(
                stream_id=stream_id,
                metadata={
                    'query_type': request.query_type,
                    'stream_status': 'started',
                    'optimizations_applied': optimizer.get_applied_optimizations()
                }
            )
        except Exception as e:
            logger.error(f"Streaming query failed: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/stream/{stream_id}/status")
    async def get_stream_status(stream_id: str):
        """Get status of a streaming query"""
        try:
            return await streaming_executor.get_stream_status(stream_id)
        except Exception as e:
            logger.error(f"Failed to get stream status: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/stream/{stream_id}")
    async def cancel_stream(stream_id: str):
        """Cancel a streaming query"""
        try:
            await streaming_executor.cancel_stream(stream_id)
            return {'status': 'cancelled', 'stream_id': stream_id}
        except Exception as e:
            logger.error(f"Failed to cancel stream: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router 