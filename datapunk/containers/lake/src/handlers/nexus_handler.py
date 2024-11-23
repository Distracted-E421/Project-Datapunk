from typing import Dict, Any, List
from datetime import datetime
import numpy as np
from ..storage.stores import VectorStore
from ..processing.validator import DataValidator

class NexusHandler:
    """Handles Nexus service requests"""
    
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.validator = DataValidator()
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming Nexus requests"""
        try:
            if 'payload' not in request:
                raise ValueError("Missing payload in request")
                
            payload = request['payload']
            
            if payload['query_type'] == 'vector_search':
                return await self._handle_vector_search(payload)
            else:
                raise ValueError(f"Unsupported query type: {payload['query_type']}")
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _handle_vector_search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle vector similarity search"""
        # Validate and prepare vector
        vector = self.validator.validate_vector(payload['vector'])
        
        # Perform search
        results = await self.vector_store.search_similar(
            vector=vector,
            limit=payload.get('limit', 10)
        )
        
        # Format results
        formatted_results = [
            {
                'id': str(result['id']),
                'similarity': float(1 - result['distance']),  # Convert distance to similarity
                'metadata': result['metadata']
            }
            for result in results
        ]
        
        return {
            'status': 'success',
            'results': formatted_results,
            'timestamp': datetime.utcnow().isoformat()
        } 