import pytest
import os
import tempfile
import OpenSSL
from datetime import datetime, timedelta
from src.nexus.auth.service_auth import (
    ServiceAuthManager,
    ServiceStatus,
    ServiceCertificate,
    ServiceRegistration
)

@pytest.fixture
def ca_cert_and_key():
    """Create a temporary CA certificate and key for testing."""
    # Generate key
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
    
    # Generate certificate
    cert = OpenSSL.crypto.X509()
    cert.get_subject().CN = "Test CA"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # Valid for 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # Create temporary files
    cert_file = tempfile.NamedTemporaryFile(delete=False)
    key_file = tempfile.NamedTemporaryFile(delete=False)
    
    # Write PEM files
    cert_file.write(OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert))
    key_file.write(OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key))
    
    cert_file.close()
    key_file.close()
    
    yield cert_file.name, key_file.name
    
    # Cleanup
    os.unlink(cert_file.name)
    os.unlink(key_file.name)

@pytest.fixture
def service_auth_manager(ca_cert_and_key):
    cert_path, key_path = ca_cert_and_key
    return ServiceAuthManager(cert_path, key_path)

def test_register_service(service_auth_manager):
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    
    assert registration.name == "test_service"
    assert registration.description == "Test service"
    assert registration.roles == {"service_role"}
    assert registration.allowed_endpoints == {"/api/.*"}
    assert registration.status == ServiceStatus.ACTIVE
    
    # Try registering same service again
    with pytest.raises(ValueError):
        service_auth_manager.register_service(
            name="test_service",
            description="Duplicate service",
            roles=set(),
            allowed_endpoints=set()
        )

def test_create_certificate(service_auth_manager):
    # Register service first
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    
    # Create certificate
    certificate = service_auth_manager.create_certificate(registration.service_id)
    
    assert certificate.service_id == registration.service_id
    assert certificate.status == ServiceStatus.ACTIVE
    assert certificate.fingerprint in registration.cert_fingerprints
    
    # Verify certificate format
    cert = OpenSSL.crypto.load_certificate(
        OpenSSL.crypto.FILETYPE_PEM,
        certificate.cert_pem.encode()
    )
    assert cert.get_subject().CN == registration.service_id

def test_validate_certificate(service_auth_manager):
    # Register service and create certificate
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    certificate = service_auth_manager.create_certificate(registration.service_id)
    
    # Validate certificate
    service = service_auth_manager.validate_certificate(certificate.cert_pem)
    assert service is not None
    assert service.service_id == registration.service_id
    
    # Test invalid certificate
    assert service_auth_manager.validate_certificate("invalid cert") is None

def test_revoke_certificate(service_auth_manager):
    # Register service and create certificate
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    certificate = service_auth_manager.create_certificate(registration.service_id)
    
    # Revoke certificate
    service_auth_manager.revoke_certificate(certificate.fingerprint)
    
    # Certificate should no longer be valid
    assert service_auth_manager.validate_certificate(certificate.cert_pem) is None
    assert certificate.fingerprint not in registration.cert_fingerprints

def test_suspend_and_activate_service(service_auth_manager):
    # Register service and create certificate
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    certificate = service_auth_manager.create_certificate(registration.service_id)
    
    # Suspend service
    service_auth_manager.suspend_service(registration.service_id)
    assert registration.status == ServiceStatus.SUSPENDED
    assert service_auth_manager.validate_certificate(certificate.cert_pem) is None
    
    # Activate service
    service_auth_manager.activate_service(registration.service_id)
    assert registration.status == ServiceStatus.ACTIVE
    assert service_auth_manager.validate_certificate(certificate.cert_pem) is not None

def test_certificate_expiry(service_auth_manager):
    # Register service
    registration = service_auth_manager.register_service(
        name="test_service",
        description="Test service",
        roles={"service_role"},
        allowed_endpoints={"/api/.*"}
    )
    
    # Create certificate with very short validity
    certificate = service_auth_manager.create_certificate(
        registration.service_id,
        validity_days=1
    )
    
    # Certificate should be valid now
    assert service_auth_manager.validate_certificate(certificate.cert_pem) is not None
    
    # Manually expire the certificate
    certificate.expires_at = datetime.utcnow() - timedelta(days=1)
    
    # Certificate should no longer be valid
    assert service_auth_manager.validate_certificate(certificate.cert_pem) is None 