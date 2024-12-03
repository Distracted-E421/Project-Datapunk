import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime
from pathlib import Path
import hashlib

from datapunk_shared.config.version_manager import ConfigVersionManager, ConfigVersion

@pytest.fixture
def version_dir(tmp_path):
    """Create temporary version directory."""
    return tmp_path / "versions"

@pytest.fixture
def version_manager(version_dir):
    """Create version manager instance."""
    return ConfigVersionManager(str(version_dir))

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "service": {
            "name": "test-service",
            "port": 8080
        },
        "database": {
            "host": "localhost",
            "port": 5432
        }
    }

class TestConfigVersion:
    """Test configuration version model."""
    
    def test_version_model(self):
        """Test version model creation and validation."""
        timestamp = datetime.utcnow()
        version = ConfigVersion(
            version="1.0.0",
            timestamp=timestamp,
            description="Initial version",
            author="test_user",
            changes={"test": "data"},
            checksum="abc123"
        )
        
        assert version.version == "1.0.0"
        assert version.timestamp == timestamp
        assert version.description == "Initial version"
        assert version.author == "test_user"
        assert version.changes == {"test": "data"}
        assert version.checksum == "abc123"
    
    def test_json_encoding(self):
        """Test JSON encoding of version model."""
        timestamp = datetime.utcnow()
        version = ConfigVersion(
            version="1.0.0",
            timestamp=timestamp,
            description="Test version",
            changes={"test": "data"},
            checksum="abc123"
        )
        
        # Convert to dict (simulating JSON encoding)
        version_dict = version.dict()
        assert version_dict["timestamp"] == timestamp.isoformat()

class TestConfigVersionManager:
    """Test configuration version manager."""
    
    def test_initialization(self, version_dir):
        """Test version manager initialization."""
        manager = ConfigVersionManager(str(version_dir))
        assert manager.version_dir == Path(version_dir)
        assert manager.version_dir.exists()
        assert manager.current_version is None
    
    def test_save_version(self, version_manager, sample_config):
        """Test saving configuration version."""
        version = "1.0.0"
        description = "Initial version"
        author = "test_user"
        
        # Save version
        version_meta = version_manager.save_version(
            sample_config,
            version,
            description,
            author
        )
        
        # Verify metadata
        assert version_meta.version == version
        assert version_meta.description == description
        assert version_meta.author == author
        assert version_meta.changes == sample_config
        
        # Verify checksum
        config_str = json.dumps(sample_config, sort_keys=True)
        expected_checksum = hashlib.sha256(config_str.encode()).hexdigest()
        assert version_meta.checksum == expected_checksum
        
        # Verify file was created
        version_file = version_manager.version_dir / f"v{version}.json"
        assert version_file.exists()
        
        # Verify file contents
        with open(version_file, 'r') as f:
            saved_data = json.load(f)
            assert saved_data["version"] == version
            assert saved_data["description"] == description
            assert saved_data["author"] == author
            assert saved_data["changes"] == sample_config
            assert saved_data["checksum"] == expected_checksum
    
    def test_load_version(self, version_manager, sample_config):
        """Test loading configuration version."""
        # Save a version
        version = "1.0.0"
        version_manager.save_version(
            sample_config,
            version,
            "Test version"
        )
        
        # Load the version
        loaded_config = version_manager.load_version(version)
        assert loaded_config == sample_config
        
        # Test loading non-existent version
        with pytest.raises(ValueError):
            version_manager.load_version("nonexistent")
    
    def test_version_history(self, version_manager, sample_config):
        """Test retrieving version history."""
        # Save multiple versions
        versions = ["1.0.0", "1.1.0", "1.2.0"]
        for version in versions:
            version_manager.save_version(
                sample_config,
                version,
                f"Version {version}"
            )
        
        # Get version history
        history = version_manager.get_version_history()
        assert len(history) == len(versions)
        
        # Verify versions are ordered correctly
        for i, version in enumerate(versions):
            assert history[i].version == version
    
    def test_compare_versions(self, version_manager):
        """Test version comparison."""
        # Save two different configs
        config1 = {"name": "test1", "value": 1}
        config2 = {"name": "test2", "value": 2}
        
        version_manager.save_version(config1, "1.0.0", "First version")
        version_manager.save_version(config2, "2.0.0", "Second version")
        
        # Compare versions
        diff = version_manager.compare_versions("1.0.0", "2.0.0")
        assert diff  # Should contain differences
        
        # Compare identical versions
        version_manager.save_version(config1, "1.0.1", "Copy of first")
        diff = version_manager.compare_versions("1.0.0", "1.0.1")
        assert not diff  # Should be empty
    
    def test_rollback(self, version_manager, sample_config):
        """Test configuration rollback."""
        # Save initial version
        version_manager.save_version(
            sample_config,
            "1.0.0",
            "Initial version"
        )
        
        # Save modified version
        modified_config = sample_config.copy()
        modified_config["service"]["port"] = 9090
        version_manager.save_version(
            modified_config,
            "2.0.0",
            "Modified version"
        )
        
        # Rollback to first version
        rollback_config = version_manager.rollback("1.0.0")
        assert rollback_config == sample_config
        
        # Verify new version was created for rollback
        versions = version_manager.get_version_history()
        assert len(versions) == 3  # Original + Modified + Rollback
        assert versions[-1].description == "Rollback to version 1.0.0"
        assert versions[-1].author == "system"
    
    def test_next_version(self, version_manager, sample_config):
        """Test next version number generation."""
        # Empty directory
        assert version_manager._get_next_version() == "1"
        
        # With existing versions
        version_manager.save_version(sample_config, "1", "First")
        version_manager.save_version(sample_config, "2", "Second")
        assert version_manager._get_next_version() == "3"
    
    def test_error_handling(self, version_manager):
        """Test error handling in version operations."""
        # Test invalid version file
        invalid_file = version_manager.version_dir / "v1.0.0.json"
        invalid_file.write_text("invalid json")
        
        with pytest.raises(Exception):
            version_manager.load_version("1.0.0")
        
        # Test missing version file
        with pytest.raises(ValueError):
            version_manager.load_version("nonexistent")
        
        # Test invalid version comparison
        with pytest.raises(ValueError):
            version_manager.compare_versions("1.0.0", "nonexistent") 