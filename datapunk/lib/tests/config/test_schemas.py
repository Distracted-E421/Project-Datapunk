import pytest
from pydantic import ValidationError
from typing import Dict, Any

from datapunk_shared.config.schemas import (
    LogLevel,
    LoggingConfig,
    SecurityConfig,
    CacheConfig,
    MetricsConfig,
    TracingConfig,
    ResourceLimits,
    ServiceConfig,
    BackupConfig,
    MaintenanceConfig,
    FeatureFlags,
    GlobalConfig
)

class TestLogLevel:
    """Test log level enumeration."""
    
    def test_valid_levels(self):
        """Test valid log levels."""
        assert LogLevel.DEBUG == "debug"
        assert LogLevel.INFO == "info"
        assert LogLevel.WARNING == "warning"
        assert LogLevel.ERROR == "error"
        assert LogLevel.CRITICAL == "critical"
    
    def test_invalid_level(self):
        """Test invalid log level."""
        with pytest.raises(ValueError):
            LogLevel("invalid")

class TestLoggingConfig:
    """Test logging configuration."""
    
    def test_default_values(self):
        """Test default logging configuration."""
        config = LoggingConfig()
        assert config.level == LogLevel.INFO
        assert config.format == "json"
        assert config.output == "stdout"
        assert config.file_path is None
        assert config.rotation == "1 day"
        assert config.retention == "30 days"
    
    def test_custom_values(self):
        """Test custom logging configuration."""
        config = LoggingConfig(
            level=LogLevel.DEBUG,
            format="text",
            output="file",
            file_path="/var/log/app.log",
            rotation="12 hours",
            retention="7 days"
        )
        assert config.level == LogLevel.DEBUG
        assert config.format == "text"
        assert config.output == "file"
        assert config.file_path == "/var/log/app.log"
        assert config.rotation == "12 hours"
        assert config.retention == "7 days"

class TestSecurityConfig:
    """Test security configuration."""
    
    def test_required_fields(self):
        """Test required security fields."""
        with pytest.raises(ValidationError):
            SecurityConfig()  # Missing required fields
        
        with pytest.raises(ValidationError):
            SecurityConfig(encryption_key="short")  # Key too short
    
    def test_valid_config(self):
        """Test valid security configuration."""
        config = SecurityConfig(
            encryption_key="a" * 32,
            jwt_secret="b" * 32,
            token_expiry=7200,
            allowed_origins=["https://example.com"],
            ssl_enabled=True,
            ssl_cert="/path/to/cert",
            ssl_key="/path/to/key"
        )
        assert config.encryption_key == "a" * 32
        assert config.jwt_secret == "b" * 32
        assert config.token_expiry == 7200
        assert config.allowed_origins == ["https://example.com"]
        assert config.ssl_enabled is True
        assert config.ssl_cert == "/path/to/cert"
        assert config.ssl_key == "/path/to/key"

class TestCacheConfig:
    """Test cache configuration."""
    
    def test_default_values(self):
        """Test default cache configuration."""
        config = CacheConfig()
        assert config.enabled is True
        assert config.backend == "redis"
        assert config.ttl == 300
        assert config.max_size == "1GB"
        assert config.eviction_policy == "lru"
    
    def test_custom_values(self):
        """Test custom cache configuration."""
        config = CacheConfig(
            enabled=False,
            backend="memcached",
            ttl=600,
            max_size="2GB",
            eviction_policy="lfu"
        )
        assert config.enabled is False
        assert config.backend == "memcached"
        assert config.ttl == 600
        assert config.max_size == "2GB"
        assert config.eviction_policy == "lfu"

class TestMetricsConfig:
    """Test metrics configuration."""
    
    def test_default_values(self):
        """Test default metrics configuration."""
        config = MetricsConfig()
        assert config.enabled is True
        assert config.interval == 60
        assert config.retention_days == 30
        assert config.exporters == ["prometheus"]
    
    def test_custom_values(self):
        """Test custom metrics configuration."""
        config = MetricsConfig(
            enabled=False,
            interval=30,
            retention_days=60,
            exporters=["prometheus", "graphite"]
        )
        assert config.enabled is False
        assert config.interval == 30
        assert config.retention_days == 60
        assert config.exporters == ["prometheus", "graphite"]

class TestTracingConfig:
    """Test tracing configuration."""
    
    def test_default_values(self):
        """Test default tracing configuration."""
        config = TracingConfig()
        assert config.enabled is True
        assert config.sampler_type == "probabilistic"
        assert config.sampling_rate == 0.1
        assert config.exporter == "jaeger"
    
    def test_invalid_sampling_rate(self):
        """Test invalid sampling rate validation."""
        with pytest.raises(ValidationError):
            TracingConfig(sampling_rate=1.5)
        
        with pytest.raises(ValidationError):
            TracingConfig(sampling_rate=-0.1)

class TestResourceLimits:
    """Test resource limits configuration."""
    
    def test_default_values(self):
        """Test default resource limits."""
        config = ResourceLimits()
        assert config.cpu_limit == "1.0"
        assert config.memory_limit == "2Gi"
        assert config.storage_limit == "10Gi"
        assert config.max_connections == 1000
        assert config.max_file_descriptors == 65535
    
    def test_custom_values(self):
        """Test custom resource limits."""
        config = ResourceLimits(
            cpu_limit="2.0",
            memory_limit="4Gi",
            storage_limit="20Gi",
            max_connections=2000,
            max_file_descriptors=32768
        )
        assert config.cpu_limit == "2.0"
        assert config.memory_limit == "4Gi"
        assert config.storage_limit == "20Gi"
        assert config.max_connections == 2000
        assert config.max_file_descriptors == 32768

class TestServiceConfig:
    """Test service configuration."""
    
    def test_required_fields(self):
        """Test required service configuration fields."""
        with pytest.raises(ValidationError):
            ServiceConfig()  # Missing required fields
    
    def test_name_validation(self):
        """Test service name validation."""
        # Valid names
        ServiceConfig(
            name="test-service",
            host="localhost",
            security=SecurityConfig(
                encryption_key="a" * 32,
                jwt_secret="b" * 32
            )
        )
        
        # Invalid names
        with pytest.raises(ValidationError):
            ServiceConfig(
                name="Test_Service",  # Invalid characters
                host="localhost",
                security=SecurityConfig(
                    encryption_key="a" * 32,
                    jwt_secret="b" * 32
                )
            )
    
    def test_version_validation(self):
        """Test version format validation."""
        # Valid versions
        ServiceConfig(
            name="test-service",
            version="1.0.0",
            host="localhost",
            security=SecurityConfig(
                encryption_key="a" * 32,
                jwt_secret="b" * 32
            )
        )
        
        # Invalid versions
        with pytest.raises(ValidationError):
            ServiceConfig(
                name="test-service",
                version="invalid",
                host="localhost",
                security=SecurityConfig(
                    encryption_key="a" * 32,
                    jwt_secret="b" * 32
                )
            )

class TestBackupConfig:
    """Test backup configuration."""
    
    def test_default_values(self):
        """Test default backup configuration."""
        config = BackupConfig()
        assert config.enabled is True
        assert config.schedule == "0 0 * * *"
        assert config.retention_count == 7
        assert config.storage_path == "/backups"
        assert config.compression is True
        assert config.encryption is True

class TestMaintenanceConfig:
    """Test maintenance configuration."""
    
    def test_default_values(self):
        """Test default maintenance configuration."""
        config = MaintenanceConfig()
        assert config.enabled is True
        assert config.window_start == "00:00"
        assert config.window_duration == 120
        assert config.auto_vacuum is True
        assert config.auto_analyze is True

class TestFeatureFlags:
    """Test feature flags configuration."""
    
    def test_default_values(self):
        """Test default feature flags."""
        config = FeatureFlags()
        assert config.experimental_features is False
        assert config.beta_features is False
        assert config.debug_mode is False
        assert config.maintenance_mode is False

class TestGlobalConfig:
    """Test global configuration."""
    
    @pytest.fixture
    def valid_config_data(self):
        """Valid configuration data fixture."""
        return {
            "environment": "development",
            "timezone": "UTC",
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": "test_db"
            },
            "redis": {
                "host": "localhost",
                "port": 6379
            },
            "service_ports": {
                "api": 8080,
                "admin": 8081
            },
            "monitoring": {
                "enabled": True,
                "interval": 60
            },
            "security": {
                "encryption_key": "a" * 32,
                "jwt_secret": "b" * 32
            }
        }
    
    def test_validation(self, valid_config_data):
        """Test global configuration validation."""
        # Valid config
        config = GlobalConfig(**valid_config_data)
        assert config.environment == "development"
        assert config.timezone == "UTC"
        
        # Test extra fields rejection
        data_with_extra = valid_config_data.copy()
        data_with_extra["extra_field"] = "value"
        with pytest.raises(ValidationError):
            GlobalConfig(**data_with_extra)
        
        # Test required fields
        invalid_data = valid_config_data.copy()
        del invalid_data["environment"]
        with pytest.raises(ValidationError):
            GlobalConfig(**invalid_data) 