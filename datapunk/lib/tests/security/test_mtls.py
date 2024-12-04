import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datapunk_shared.security.mtls import (
    MTLSManager,
    MTLSConfig,
    CertificateInfo,
    MTLSError
)

@pytest.fixture
def mtls_config():
    return MTLSConfig(
        name="test_mtls",
        ca_cert_path="/path/to/ca.crt",
        ca_key_path="/path/to/ca.key",
        cert_dir="/path/to/certs",
        cert_validity_days=365,
        key_size=2048,
        hash_algorithm="sha256",
        subject_info={
            "country_name": "US",
            "state_name": "California",
            "locality_name": "San Francisco",
            "org_name": "Datapunk",
            "common_name": "test.datapunk.io"
        }
    )

@pytest.fixture
def mock_ca_cert():
    # Generate a mock CA certificate
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Datapunk"),
        x509.NameAttribute(NameOID.COMMON_NAME, "Datapunk CA")
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True
    ).sign(private_key, hashes.SHA256())
    
    return cert, private_key

@pytest.fixture
async def mtls_manager(mtls_config, mock_ca_cert):
    with patch('builtins.open', MagicMock()):
        manager = MTLSManager(mtls_config)
        manager.ca_cert, manager.ca_key = mock_ca_cert
        await manager.initialize()
        return manager

@pytest.mark.asyncio
async def test_manager_initialization(mtls_manager, mtls_config):
    """Test MTLS manager initialization"""
    assert mtls_manager.config == mtls_config
    assert mtls_manager.is_initialized
    assert mtls_manager.ca_cert is not None
    assert mtls_manager.ca_key is not None

@pytest.mark.asyncio
async def test_certificate_generation(mtls_manager):
    """Test certificate generation"""
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    
    cert, key = await mtls_manager.generate_certificate(cert_info)
    
    assert isinstance(cert, x509.Certificate)
    assert isinstance(key, rsa.RSAPrivateKey)
    assert cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == cert_info.common_name

@pytest.mark.asyncio
async def test_certificate_validation(mtls_manager):
    """Test certificate validation"""
    # Generate a valid certificate
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    cert, _ = await mtls_manager.generate_certificate(cert_info)
    
    # Validate the certificate
    result = await mtls_manager.validate_certificate(cert)
    assert result.is_valid
    assert not result.errors

@pytest.mark.asyncio
async def test_certificate_revocation(mtls_manager):
    """Test certificate revocation"""
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    cert, _ = await mtls_manager.generate_certificate(cert_info)
    
    # Revoke the certificate
    await mtls_manager.revoke_certificate(cert.serial_number)
    
    # Validate the revoked certificate
    result = await mtls_manager.validate_certificate(cert)
    assert not result.is_valid
    assert "revoked" in str(result.errors[0])

@pytest.mark.asyncio
async def test_certificate_renewal(mtls_manager):
    """Test certificate renewal"""
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    old_cert, old_key = await mtls_manager.generate_certificate(cert_info)
    
    # Renew the certificate
    new_cert, new_key = await mtls_manager.renew_certificate(old_cert)
    
    assert new_cert.serial_number != old_cert.serial_number
    assert new_cert.not_valid_after > old_cert.not_valid_after

@pytest.mark.asyncio
async def test_certificate_storage(mtls_manager):
    """Test certificate storage"""
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    cert, key = await mtls_manager.generate_certificate(cert_info)
    
    # Mock file operations
    with patch('builtins.open', MagicMock()):
        await mtls_manager.store_certificate(cert, key, "test_cert")
        stored_cert = await mtls_manager.load_certificate("test_cert")
        
        assert stored_cert.serial_number == cert.serial_number

@pytest.mark.asyncio
async def test_error_handling(mtls_manager):
    """Test error handling"""
    # Test with invalid certificate info
    invalid_info = CertificateInfo(
        common_name="",  # Invalid common name
        organization="Datapunk",
        validity_days=365
    )
    
    with pytest.raises(MTLSError):
        await mtls_manager.generate_certificate(invalid_info)
    
    # Test with invalid certificate for validation
    with pytest.raises(MTLSError):
        await mtls_manager.validate_certificate(None)

@pytest.mark.asyncio
async def test_certificate_chain_validation(mtls_manager):
    """Test certificate chain validation"""
    # Generate intermediate CA
    intermediate_info = CertificateInfo(
        common_name="Intermediate CA",
        organization="Datapunk",
        validity_days=365,
        is_ca=True
    )
    intermediate_cert, intermediate_key = await mtls_manager.generate_certificate(intermediate_info)
    
    # Generate leaf certificate signed by intermediate
    leaf_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    
    with patch.object(mtls_manager, 'ca_cert', intermediate_cert), \
         patch.object(mtls_manager, 'ca_key', intermediate_key):
        leaf_cert, _ = await mtls_manager.generate_certificate(leaf_info)
    
    # Validate the chain
    result = await mtls_manager.validate_certificate_chain([leaf_cert, intermediate_cert])
    assert result.is_valid

@pytest.mark.asyncio
async def test_certificate_expiration(mtls_manager):
    """Test certificate expiration handling"""
    # Generate a certificate that's about to expire
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=1  # Short validity
    )
    cert, _ = await mtls_manager.generate_certificate(cert_info)
    
    # Check expiration
    expiration_check = await mtls_manager.check_certificate_expiration(cert)
    assert expiration_check.expires_soon
    assert expiration_check.days_until_expiration <= 1

@pytest.mark.asyncio
async def test_certificate_metrics(mtls_manager):
    """Test certificate metrics collection"""
    metrics = []
    mtls_manager.set_metrics_callback(metrics.append)
    
    cert_info = CertificateInfo(
        common_name="test.service.datapunk.io",
        organization="Datapunk",
        validity_days=365
    )
    await mtls_manager.generate_certificate(cert_info)
    
    assert len(metrics) > 0
    assert any(m["type"] == "certificate_generation" for m in metrics)
    assert any(m["type"] == "certificate_validity" for m in metrics)

@pytest.mark.asyncio
async def test_bulk_operations(mtls_manager):
    """Test bulk certificate operations"""
    # Generate multiple certificates
    cert_infos = [
        CertificateInfo(
            common_name=f"test{i}.service.datapunk.io",
            organization="Datapunk",
            validity_days=365
        )
        for i in range(5)
    ]
    
    certs = await mtls_manager.generate_certificates_bulk(cert_infos)
    assert len(certs) == len(cert_infos)
    
    # Validate all certificates
    results = await mtls_manager.validate_certificates_bulk(certs)
    assert all(r.is_valid for r in results) 