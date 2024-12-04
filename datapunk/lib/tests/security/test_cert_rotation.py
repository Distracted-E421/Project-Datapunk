import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from datapunk_shared.security.cert_rotation import (
    CertificateRotator,
    RotationConfig,
    RotationStrategy,
    RotationResult,
    RotationError
)

@pytest.fixture
def rotation_config():
    return RotationConfig(
        name="test_rotator",
        cert_dir="/path/to/certs",
        backup_dir="/path/to/backups",
        rotation_interval_days=30,
        overlap_days=7,
        key_size=2048,
        hash_algorithm="sha256",
        notification_threshold_days=14,
        strategy=RotationStrategy.GRADUAL
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
async def cert_rotator(rotation_config, mock_cert):
    with patch('builtins.open', MagicMock()):
        rotator = CertificateRotator(rotation_config)
        rotator.current_cert, rotator.current_key = mock_cert
        await rotator.initialize()
        return rotator

@pytest.mark.asyncio
async def test_rotator_initialization(cert_rotator, rotation_config):
    """Test certificate rotator initialization"""
    assert cert_rotator.config == rotation_config
    assert cert_rotator.is_initialized
    assert cert_rotator.current_cert is not None
    assert cert_rotator.current_key is not None

@pytest.mark.asyncio
async def test_rotation_check(cert_rotator):
    """Test rotation check"""
    # Certificate not due for rotation
    result = await cert_rotator.check_rotation_needed()
    assert not result.needed
    
    # Simulate certificate near expiration
    cert_rotator.current_cert = x509.CertificateBuilder().not_valid_after(
        datetime.utcnow() + timedelta(days=cert_rotator.config.notification_threshold_days - 1)
    ).serial_number(
        x509.random_serial_number()
    ).subject_name(
        x509.Name([])
    ).issuer_name(
        x509.Name([])
    ).public_key(
        cert_rotator.current_key.public_key()
    ).sign(cert_rotator.current_key, hashes.SHA256())
    
    result = await cert_rotator.check_rotation_needed()
    assert result.needed
    assert result.days_until_rotation < cert_rotator.config.notification_threshold_days

@pytest.mark.asyncio
async def test_certificate_rotation(cert_rotator):
    """Test certificate rotation"""
    # Perform rotation
    result = await cert_rotator.rotate_certificate()
    
    assert result.success
    assert result.new_cert is not None
    assert result.new_key is not None
    assert result.new_cert.serial_number != cert_rotator.current_cert.serial_number

@pytest.mark.asyncio
async def test_backup_creation(cert_rotator):
    """Test backup creation"""
    # Create backup
    backup_result = await cert_rotator.create_backup()
    
    assert backup_result.success
    assert backup_result.backup_path is not None
    
    # Verify backup
    with patch('builtins.open', MagicMock()):
        verify_result = await cert_rotator.verify_backup(backup_result.backup_path)
        assert verify_result.success

@pytest.mark.asyncio
async def test_gradual_rotation(cert_rotator):
    """Test gradual rotation strategy"""
    # Start gradual rotation
    result = await cert_rotator.start_gradual_rotation()
    
    assert result.success
    assert result.new_cert is not None
    assert result.old_cert is not None
    assert result.overlap_period == timedelta(days=cert_rotator.config.overlap_days)

@pytest.mark.asyncio
async def test_emergency_rotation(cert_rotator):
    """Test emergency rotation"""
    # Perform emergency rotation
    result = await cert_rotator.emergency_rotate()
    
    assert result.success
    assert result.new_cert is not None
    assert result.notification_sent
    assert result.backup_created

@pytest.mark.asyncio
async def test_rotation_rollback(cert_rotator):
    """Test rotation rollback"""
    # Perform rotation
    rotation_result = await cert_rotator.rotate_certificate()
    
    # Simulate failure and rollback
    rollback_result = await cert_rotator.rollback_rotation(rotation_result.rotation_id)
    
    assert rollback_result.success
    assert cert_rotator.current_cert.serial_number == rotation_result.old_cert.serial_number

@pytest.mark.asyncio
async def test_rotation_metrics(cert_rotator):
    """Test rotation metrics collection"""
    metrics = []
    cert_rotator.set_metrics_callback(metrics.append)
    
    await cert_rotator.rotate_certificate()
    
    assert len(metrics) > 0
    assert any(m["type"] == "certificate_rotation" for m in metrics)
    assert any(m["type"] == "rotation_duration" for m in metrics)

@pytest.mark.asyncio
async def test_rotation_notifications(cert_rotator):
    """Test rotation notifications"""
    notification_handler = AsyncMock()
    cert_rotator.set_notification_handler(notification_handler)
    
    # Trigger rotation that should send notification
    cert_rotator.current_cert = x509.CertificateBuilder().not_valid_after(
        datetime.utcnow() + timedelta(days=cert_rotator.config.notification_threshold_days - 1)
    ).serial_number(
        x509.random_serial_number()
    ).subject_name(
        x509.Name([])
    ).issuer_name(
        x509.Name([])
    ).public_key(
        cert_rotator.current_key.public_key()
    ).sign(cert_rotator.current_key, hashes.SHA256())
    
    await cert_rotator.check_and_notify()
    
    notification_handler.assert_called_once()

@pytest.mark.asyncio
async def test_concurrent_rotations(cert_rotator):
    """Test handling of concurrent rotation attempts"""
    # Start first rotation
    first_rotation = cert_rotator.rotate_certificate()
    
    # Attempt second rotation
    with pytest.raises(RotationError):
        await cert_rotator.rotate_certificate()
    
    # Complete first rotation
    result = await first_rotation
    assert result.success

@pytest.mark.asyncio
async def test_rotation_history(cert_rotator):
    """Test rotation history tracking"""
    # Perform multiple rotations
    for _ in range(3):
        await cert_rotator.rotate_certificate()
    
    history = await cert_rotator.get_rotation_history()
    
    assert len(history) == 3
    assert all(entry.success for entry in history)
    assert all(entry.timestamp is not None for entry in history)

@pytest.mark.asyncio
async def test_custom_rotation_strategy(cert_rotator):
    """Test custom rotation strategy"""
    # Define custom strategy
    async def custom_strategy(cert, key):
        # Custom rotation logic
        return RotationResult(
            success=True,
            new_cert=cert,
            new_key=key,
            strategy="custom"
        )
    
    cert_rotator.add_rotation_strategy("custom", custom_strategy)
    
    # Use custom strategy
    result = await cert_rotator.rotate_certificate(strategy="custom")
    assert result.success
    assert result.strategy == "custom" 