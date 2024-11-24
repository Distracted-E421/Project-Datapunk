from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
import json
import hashlib
from enum import Enum

logger = structlog.get_logger()

class ComplianceStandard(Enum):
    """Supported compliance standards."""
    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOX = "sox"
    PCI = "pci"
    ISO27001 = "iso27001"

@dataclass
class ComplianceConfig:
    """Configuration for compliance requirements."""
    standards: Set[ComplianceStandard]
    retention_period: timedelta
    encryption_required: bool = True
    pii_detection: bool = True
    audit_signing: bool = True
    immutable_storage: bool = True

class ComplianceAuditor:
    """Handles compliance-specific audit requirements."""
    
    def __init__(self,
                 config: ComplianceConfig,
                 metrics_client,
                 storage_client):
        self.config = config
        self.metrics = metrics_client
        self.storage = storage_client
        self.logger = logger.bind(component="compliance_audit")
    
    async def process_event(self, event: Dict) -> Dict:
        """Process event for compliance requirements."""
        try:
            # Add compliance metadata
            event["compliance"] = {
                "standards": [s.value for s in self.config.standards],
                "timestamp": datetime.utcnow().isoformat(),
                "hash": self._generate_event_hash(event)
            }
            
            # Handle PII if configured
            if self.config.pii_detection:
                event = await self._handle_pii(event)
            
            # Sign event if required
            if self.config.audit_signing:
                event["signature"] = await self._sign_event(event)
            
            # Store in immutable storage if configured
            if self.config.immutable_storage:
                await self._store_immutable(event)
            
            return event
            
        except Exception as e:
            self.logger.error("compliance_processing_failed",
                            error=str(e))
            self.metrics.increment("compliance_processing_errors")
            raise
    
    def _generate_event_hash(self, event: Dict) -> str:
        """Generate cryptographic hash of event."""
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha256(event_str.encode()).hexdigest()
    
    async def _handle_pii(self, event: Dict) -> Dict:
        """Handle PII data in event."""
        pii_fields = {
            "email", "phone", "address", "ssn", "credit_card",
            "passport", "driver_license"
        }
        
        def mask_pii(value: str) -> str:
            """Mask PII data."""
            if len(value) <= 4:
                return "*" * len(value)
            return value[:2] + "*" * (len(value) - 4) + value[-2:]
        
        def process_dict(d: Dict) -> Dict:
            """Recursively process dictionary for PII."""
            result = {}
            for k, v in d.items():
                if k.lower() in pii_fields:
                    result[k] = mask_pii(str(v))
                elif isinstance(v, dict):
                    result[k] = process_dict(v)
                elif isinstance(v, list):
                    result[k] = [
                        process_dict(i) if isinstance(i, dict) else i
                        for i in v
                    ]
                else:
                    result[k] = v
            return result
        
        return process_dict(event)
    
    async def _sign_event(self, event: Dict) -> str:
        """Sign event for integrity verification."""
        # Implementation would use proper cryptographic signing
        # This is a placeholder
        event_hash = self._generate_event_hash(event)
        timestamp = datetime.utcnow().isoformat()
        return f"{event_hash}:{timestamp}"
    
    async def _store_immutable(self, event: Dict) -> None:
        """Store event in immutable storage."""
        try:
            key = f"audit:immutable:{event['event_type']}:{event['timestamp']}"
            await self.storage.store_immutable(key, json.dumps(event))
            
        except Exception as e:
            self.logger.error("immutable_storage_failed",
                            error=str(e))
            raise 