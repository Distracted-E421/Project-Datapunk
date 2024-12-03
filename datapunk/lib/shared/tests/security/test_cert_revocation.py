import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datapunk_shared.security.cert_revocation import (
    CertificateRevocator,
    RevocationConfig,
    RevocationReason,
    RevocationResult,
    RevocationError
)

@pytest.fixture
def revocation_config():
    return RevocationConfig(
        name="test_revocator",
        crl_path="/path/to/crl",
        ocsp_url="https://ocsp.datapunk.io",
        update_interval=3600,  # 1 hour
        backup_dir="/path/to/backups",
        notification_enabled=True,
        metrics_enabled=True
    )

@pytest.fixture
def mock_cert():
    # Generate a mock certificate
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "test.service.datapunk.io")
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
    ).sign(private_key, hashes.SHA256())
    
    return cert, private_key

@pytest.fixture
async def cert_revocator(revocation_config, mock_cert):
    with patch('builtins.open', MagicMock()):
        revocator = CertificateRevocator(revocation_config)
        revocator.ca_cert, revocator.ca_key = mock_cert
        await revocator.initialize()
        return revocator

@pytest.mark.asyncio
async def test_revocator_initialization(cert_revocator, revocation_config):
    """Test certificate revocator initialization"""
    assert cert_revocator.config == revocation_config
    assert cert_revocator.is_initialized
    assert cert_revocator.ca_cert is not None
    assert cert_revocator.ca_key is not None

@pytest.mark.asyncio
async def test_certificate_revocation(cert_revocator, mock_cert):
    """Test certificate revocation"""
    cert, _ = mock_cert
    
    # Revoke certificate
    result = await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.KEY_COMPROMISE
    )
    
    assert result.success
    assert result.serial_number == cert.serial_number
    assert result.reason == RevocationReason.KEY_COMPROMISE

@pytest.mark.asyncio
async def test_crl_generation(cert_revocator):
    """Test CRL generation"""
    # Generate CRL
    crl_result = await cert_revocator.generate_crl()
    
    assert crl_result.success
    assert crl_result.crl is not None
    assert isinstance(crl_result.crl, x509.CertificateRevocationList)

@pytest.mark.asyncio
async def test_ocsp_response(cert_revocator, mock_cert):
    """Test OCSP response generation"""
    cert, _ = mock_cert
    
    # Generate OCSP response
    response = await cert_revocator.generate_ocsp_response(cert.serial_number)
    
    assert response.status == "good"  # Not revoked yet
    
    # Revoke and check again
    await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.KEY_COMPROMISE
    )
    
    response = await cert_revocator.generate_ocsp_response(cert.serial_number)
    assert response.status == "revoked"

@pytest.mark.asyncio
async def test_revocation_check(cert_revocator, mock_cert):
    """Test revocation status check"""
    cert, _ = mock_cert
    
    # Check before revocation
    status = await cert_revocator.check_revocation_status(cert.serial_number)
    assert not status.is_revoked
    
    # Revoke and check again
    await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.SUPERSEDED
    )
    
    status = await cert_revocator.check_revocation_status(cert.serial_number)
    assert status.is_revoked
    assert status.reason == RevocationReason.SUPERSEDED

@pytest.mark.asyncio
async def test_bulk_revocation(cert_revocator):
    """Test bulk certificate revocation"""
    # Generate multiple certificates
    certs = []
    for _ in range(5):
        cert, _ = await cert_revocator.generate_test_certificate()
        certs.append(cert)
    
    # Revoke all certificates
    results = await cert_revocator.revoke_certificates_bulk(
        [cert.serial_number for cert in certs],
        RevocationReason.CESSATION_OF_OPERATION
    )
    
    assert len(results) == len(certs)
    assert all(r.success for r in results)

@pytest.mark.asyncio
async def test_revocation_metrics(cert_revocator, mock_cert):
    """Test revocation metrics collection"""
    cert, _ = mock_cert
    metrics = []
    cert_revocator.set_metrics_callback(metrics.append)
    
    await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.KEY_COMPROMISE
    )
    
    assert len(metrics) > 0
    assert any(m["type"] == "certificate_revocation" for m in metrics)
    assert any(m["type"] == "crl_update" for m in metrics)

@pytest.mark.asyncio
async def test_revocation_notifications(cert_revocator, mock_cert):
    """Test revocation notifications"""
    cert, _ = mock_cert
    notification_handler = AsyncMock()
    cert_revocator.set_notification_handler(notification_handler)
    
    await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.KEY_COMPROMISE
    )
    
    notification_handler.assert_called_once()

@pytest.mark.asyncio
async def test_crl_update_scheduling(cert_revocator):
    """Test CRL update scheduling"""
    update_handler = AsyncMock()
    cert_revocator.set_crl_update_handler(update_handler)
    
    # Start update scheduler
    await cert_revocator.start_crl_updates()
    await asyncio.sleep(0.1)  # Allow scheduler to run
    
    update_handler.assert_called()
    
    # Stop scheduler
    await cert_revocator.stop_crl_updates()

@pytest.mark.asyncio
async def test_revocation_history(cert_revocator, mock_cert):
    """Test revocation history tracking"""
    cert, _ = mock_cert
    
    # Revoke certificate
    await cert_revocator.revoke_certificate(
        cert.serial_number,
        RevocationReason.KEY_COMPROMISE
    )
    
    # Get history
    history = await cert_revocator.get_revocation_history()
    
    assert len(history) == 1
    assert history[0].serial_number == cert.serial_number
    assert history[0].reason == RevocationReason.KEY_COMPROMISE

@pytest.mark.asyncio
async def test_error_handling(cert_revocator):
    """Test error handling"""
    # Test with invalid serial number
    with pytest.raises(RevocationError):
        await cert_revocator.revoke_certificate(
            None,
            RevocationReason.KEY_COMPROMISE
        )
    
    # Test with invalid reason
    with pytest.raises(RevocationError):
        await cert_revocator.revoke_certificate(
            123,
            "invalid_reason"
        )

@pytest.mark.asyncio
async def test_crl_distribution(cert_revocator):
    """Test CRL distribution"""
    # Generate and distribute CRL
    distribution_result = await cert_revocator.distribute_crl()
    
    assert distribution_result.success
    assert distribution_result.distribution_points > 0
    assert distribution_result.timestamp is not None

@pytest.mark.asyncio
async def test_ocsp_responder(cert_revocator, mock_cert):
    """Test OCSP responder"""
    cert, _ = mock_cert
    
    # Start OCSP responder
    await cert_revocator.start_ocsp_responder()
    
    # Test OCSP request
    response = await cert_revocator.handle_ocsp_request(cert.serial_number)
    assert response is not None
    assert response.response_status == "successful"
    
    # Stop responder
    await cert_revocator.stop_ocsp_responder() 