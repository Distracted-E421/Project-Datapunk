from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Set
import ssl
import OpenSSL
from datetime import datetime, timedelta
import hashlib
import secrets

class ServiceStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

@dataclass
class ServiceCertificate:
    service_id: str
    cert_pem: str
    private_key_pem: str  # Only used during initial creation
    fingerprint: str
    issued_at: datetime
    expires_at: datetime
    status: ServiceStatus = ServiceStatus.ACTIVE

@dataclass
class ServiceRegistration:
    service_id: str
    name: str
    description: str
    roles: Set[str]
    allowed_endpoints: Set[str]  # Regex patterns for allowed endpoints
    cert_fingerprints: Set[str] = field(default_factory=set)
    status: ServiceStatus = ServiceStatus.ACTIVE

class ServiceAuthManager:
    def __init__(self, ca_cert_path: str, ca_key_path: str):
        """Initialize with CA certificate and private key for signing service certs."""
        self._load_ca(ca_cert_path, ca_key_path)
        self._services: Dict[str, ServiceRegistration] = {}
        self._certificates: Dict[str, ServiceCertificate] = {}
        
    def _load_ca(self, cert_path: str, key_path: str):
        """Load CA certificate and private key."""
        with open(cert_path, 'rb') as f:
            self._ca_cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM,
                f.read()
            )
            
        with open(key_path, 'rb') as f:
            self._ca_key = OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM,
                f.read()
            )
            
    def register_service(self, name: str, description: str, roles: Set[str],
                        allowed_endpoints: Set[str]) -> ServiceRegistration:
        """Register a new service."""
        service_id = self._generate_service_id(name)
        
        if service_id in self._services:
            raise ValueError(f"Service {name} already registered")
            
        registration = ServiceRegistration(
            service_id=service_id,
            name=name,
            description=description,
            roles=roles,
            allowed_endpoints=allowed_endpoints
        )
        
        self._services[service_id] = registration
        return registration
        
    def _generate_service_id(self, name: str) -> str:
        """Generate unique service ID."""
        timestamp = datetime.utcnow().isoformat()
        random = secrets.token_hex(8)
        return hashlib.sha256(f"{name}:{timestamp}:{random}".encode()).hexdigest()[:32]
        
    def create_certificate(self, service_id: str, validity_days: int = 365) -> ServiceCertificate:
        """Create a new certificate for a service."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not registered")
            
        if self._services[service_id].status != ServiceStatus.ACTIVE:
            raise ValueError(f"Service {service_id} is not active")
            
        # Generate key pair
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        
        # Create certificate
        cert = OpenSSL.crypto.X509()
        cert.get_subject().CN = service_id
        cert.set_serial_number(int(secrets.token_hex(16), 16))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(validity_days * 24 * 60 * 60)
        cert.set_issuer(self._ca_cert.get_subject())
        cert.set_pubkey(key)
        cert.sign(self._ca_key, 'sha256')
        
        # Convert to PEM format
        cert_pem = OpenSSL.crypto.dump_certificate(
            OpenSSL.crypto.FILETYPE_PEM, cert
        ).decode()
        key_pem = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key
        ).decode()
        
        # Calculate fingerprint
        fingerprint = hashlib.sha256(cert_pem.encode()).hexdigest()
        
        # Create certificate record
        certificate = ServiceCertificate(
            service_id=service_id,
            cert_pem=cert_pem,
            private_key_pem=key_pem,
            fingerprint=fingerprint,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=validity_days)
        )
        
        # Store certificate and update service registration
        self._certificates[fingerprint] = certificate
        self._services[service_id].cert_fingerprints.add(fingerprint)
        
        return certificate
        
    def validate_certificate(self, cert_pem: str) -> Optional[ServiceRegistration]:
        """Validate a service certificate and return service registration if valid."""
        try:
            # Parse certificate
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM,
                cert_pem.encode()
            )
            
            # Calculate fingerprint
            fingerprint = hashlib.sha256(cert_pem.encode()).hexdigest()
            
            # Check if certificate is known
            certificate = self._certificates.get(fingerprint)
            if not certificate:
                return None
                
            # Check if certificate is still valid
            if certificate.status != ServiceStatus.ACTIVE:
                return None
                
            if datetime.utcnow() > certificate.expires_at:
                return None
                
            # Get service registration
            service = self._services.get(certificate.service_id)
            if not service or service.status != ServiceStatus.ACTIVE:
                return None
                
            # Verify certificate is still registered to service
            if fingerprint not in service.cert_fingerprints:
                return None
                
            return service
            
        except Exception:
            return None
            
    def revoke_certificate(self, fingerprint: str):
        """Revoke a certificate."""
        if fingerprint not in self._certificates:
            raise ValueError(f"Certificate {fingerprint} not found")
            
        certificate = self._certificates[fingerprint]
        certificate.status = ServiceStatus.REVOKED
        
        # Remove from service registration
        service = self._services.get(certificate.service_id)
        if service:
            service.cert_fingerprints.remove(fingerprint)
            
    def suspend_service(self, service_id: str):
        """Suspend a service."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
            
        service = self._services[service_id]
        service.status = ServiceStatus.SUSPENDED
        
        # Suspend all certificates
        for fingerprint in service.cert_fingerprints:
            if fingerprint in self._certificates:
                self._certificates[fingerprint].status = ServiceStatus.SUSPENDED
                
    def activate_service(self, service_id: str):
        """Activate a suspended service."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
            
        service = self._services[service_id]
        if service.status == ServiceStatus.REVOKED:
            raise ValueError(f"Cannot activate revoked service {service_id}")
            
        service.status = ServiceStatus.ACTIVE
        
        # Reactivate certificates
        for fingerprint in service.cert_fingerprints:
            if fingerprint in self._certificates:
                cert = self._certificates[fingerprint]
                if cert.status == ServiceStatus.SUSPENDED:
                    cert.status = ServiceStatus.ACTIVE 