from fastapi import Request
from typing import Dict, List, Set
import re
import json
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from pydantic import BaseModel

class PIIDetector:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
        # Common PII patterns
        self.patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[-. ]?\d{4}[-. ]?\d{4}[-. ]?\d{4}\b',
        }

    async def detect_pii(self, text: str) -> List[Dict]:
        # Use Presidio analyzer to detect PII
        analyzer_results = self.analyzer.analyze(
            text=text,
            language='en'
        )
        
        return [
            {
                'entity_type': result.entity_type,
                'start': result.start,
                'end': result.end,
                'score': result.score
            }
            for result in analyzer_results
        ]

    async def anonymize_pii(self, text: str) -> str:
        # Detect PII
        analyzer_results = self.analyzer.analyze(
            text=text,
            language='en'
        )
        
        # Anonymize detected PII
        anonymized_text = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results
        )
        
        return anonymized_text.text

pii_detector = PIIDetector()

async def pii_middleware(request: Request, call_next):
    # Store original request body
    body = await request.body()
    
    if body:
        try:
            json_body = json.loads(body)
            # Convert to string for PII detection
            text_content = json.dumps(json_body)
            
            # Detect PII
            pii_results = await pii_detector.detect_pii(text_content)
            
            if pii_results:
                # Anonymize content if PII is detected
                anonymized_content = await pii_detector.anonymize_pii(text_content)
                # Modify request with anonymized content
                json_body = json.loads(anonymized_content)
                
                # Create new request with anonymized content
                request._body = json.dumps(json_body).encode()
        
        except json.JSONDecodeError:
            # If not JSON, process as plain text
            text_content = body.decode()
            pii_results = await pii_detector.detect_pii(text_content)
            
            if pii_results:
                anonymized_content = await pii_detector.anonymize_pii(text_content)
                request._body = anonymized_content.encode()
    
    response = await call_next(request)
    return response