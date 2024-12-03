import pytest
import asyncio
import ssl
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
from datetime import datetime, timedelta
from datapunk_shared.mesh.security import (
    MtlsManager,
    MtlsConfig,
    CertificateInfo,
    MtlsError
)

@pytest.fixture
def mtls_config():
    return MtlsConfig(
        ca_cert_path="ca.crt",
        cert_path="service.crt",
        key_path="service.key",
        verify_peer=True,
        cert_refresh_hours=24
    )

@pytest.fixture
def mtls_manager(mtls_config):
    return MtlsManager(config=mtls_config)

@pytest.fixture
def sample_cert_info():
    return CertificateInfo(
        subject="CN=test-service",
        issuer="CN=test-ca",
        not_before=datetime.utcnow(),
        not_after=datetime.utcnow() + timedelta(days=365),
        serial_number="123456",
        fingerprint="ab:cd:ef"
    )

@pytest.mark.asyncio
async def test_mtls_initialization(mtls_manager, mtls_config):
    assert mtls_manager.config == mtls_config
    assert not mtls_manager.is_initialized
    assert mtls_manager.ssl_context is None

@pytest.mark.asyncio
async def test_certificate_loading():
    with patch('ssl.SSLContext') as mock_ssl:
        mock_context = Mock()
        mock_ssl.return_value = mock_context
        
        manager = MtlsManager(MtlsConfig(
            ca_cert_path="ca.crt",
            cert_path="service.crt",
            key_path="service.key"
        ))
        
        await manager.initialize()
        
        mock_context.load_verify_locations.assert_called_once()
        mock_context.load_cert_chain.assert_called_once()
        assert manager.is_initialized

@pytest.mark.asyncio
async def test_certificate_validation(mtls_manager, sample_cert_info):
    with patch.object(mtls_manager, '_load_certificate_info') as mock_load:
        mock_load.return_value = sample_cert_info
        
        is_valid = await mtls_manager.validate_certificate("test.crt")
        assert is_valid
        mock_load.assert_called_once()

@pytest.mark.asyncio
async def test_certificate_expiration_check(mtls_manager):
    expired_cert = CertificateInfo(
        subject="CN=test",
        issuer="CN=ca",
        not_before=datetime.utcnow() - timedelta(days=2),
        not_after=datetime.utcnow() - timedelta(days=1),
        serial_number="123",
        fingerprint="aa:bb:cc"
    )
    
    with patch.object(mtls_manager, '_load_certificate_info') as mock_load:
        mock_load.return_value = expired_cert
        
        is_valid = await mtls_manager.validate_certificate("test.crt")
        assert not is_valid

@pytest.mark.asyncio
async def test_certificate_refresh():
    with patch('ssl.SSLContext') as mock_ssl:
        mock_context = Mock()
        mock_ssl.return_value = mock_context
        
        manager = MtlsManager(MtlsConfig(
            ca_cert_path="ca.crt",
            cert_path="service.crt",
            key_path="service.key",
            cert_refresh_hours=1
        ))
        
        await manager.initialize()
        await manager.refresh_certificates()
        
        assert mock_context.load_cert_chain.call_count == 2

@pytest.mark.asyncio
async def test_peer_verification():
    with patch('ssl.SSLContext') as mock_ssl:
        mock_context = Mock()
        mock_ssl.return_value = mock_context
        
        manager = MtlsManager(MtlsConfig(
            ca_cert_path="ca.crt",
            cert_path="service.crt",
            key_path="service.key",
            verify_peer=True
        ))
        
        await manager.initialize()
        
        assert mock_context.verify_mode == ssl.CERT_REQUIRED
        assert mock_context.check_hostname is True

@pytest.mark.asyncio
async def test_certificate_chain_validation(mtls_manager):
    cert_chain = [
        CertificateInfo(
            subject="CN=service",
            issuer="CN=intermediate",
            not_before=datetime.utcnow(),
            not_after=datetime.utcnow() + timedelta(days=365),
            serial_number="123",
            fingerprint="aa:bb:cc"
        ),
        CertificateInfo(
            subject="CN=intermediate",
            issuer="CN=root",
            not_before=datetime.utcnow(),
            not_after=datetime.utcnow() + timedelta(days=365),
            serial_number="456",
            fingerprint="dd:ee:ff"
        )
    ]
    
    with patch.object(mtls_manager, '_load_certificate_chain') as mock_load:
        mock_load.return_value = cert_chain
        
        is_valid = await mtls_manager.validate_certificate_chain("test.crt")
        assert is_valid

@pytest.mark.asyncio
async def test_certificate_revocation_check(mtls_manager):
    with patch.object(mtls_manager, '_check_revocation_status') as mock_check:
        mock_check.return_value = False  # Not revoked
        
        is_valid = await mtls_manager.validate_certificate(
            "test.crt",
            check_revocation=True
        )
        assert is_valid
        mock_check.assert_called_once()

@pytest.mark.asyncio
async def test_certificate_metrics_collection(mtls_manager, sample_cert_info):
    with patch('datapunk_shared.mesh.metrics.MetricsCollector') as mock_collector:
        with patch.object(mtls_manager, '_load_certificate_info') as mock_load:
            mock_load.return_value = sample_cert_info
            
            await mtls_manager.collect_metrics()
            
            mock_collector.return_value.record_gauge.assert_called()

@pytest.mark.asyncio
async def test_certificate_rotation(mtls_manager):
    with patch.object(mtls_manager, '_rotate_certificates') as mock_rotate:
        await mtls_manager.rotate_certificates()
        mock_rotate.assert_called_once()
        
        # Verify SSL context is reloaded
        assert mtls_manager.ssl_context is not None

@pytest.mark.asyncio
async def test_error_handling(mtls_manager):
    # Test with invalid certificate path
    with pytest.raises(MtlsError):
        await mtls_manager.validate_certificate("nonexistent.crt")

@pytest.mark.asyncio
async def test_certificate_backup(mtls_manager):
    with patch('shutil.copy2') as mock_copy:
        await mtls_manager.backup_certificates()
        assert mock_copy.call_count == 3  # CA cert, cert, and key

@pytest.mark.asyncio
async def test_certificate_permissions(mtls_manager):
    with patch('os.chmod') as mock_chmod:
        await mtls_manager.initialize()
        
        # Should set restrictive permissions on private key
        mock_chmod.assert_called_with(mtls_manager.config.key_path, 0o600)

@pytest.mark.asyncio
async def test_certificate_events(mtls_manager, sample_cert_info):
    events = []
    
    def event_handler(event_type, cert_info):
        events.append((event_type, cert_info))
    
    mtls_manager.on_certificate_event(event_handler)
    
    with patch.object(mtls_manager, '_load_certificate_info') as mock_load:
        mock_load.return_value = sample_cert_info
        await mtls_manager.validate_certificate("test.crt")
        
        assert len(events) > 0
        assert events[0][0] == "validated" 