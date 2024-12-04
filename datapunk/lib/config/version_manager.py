from typing import Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path
import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

"""
Version control for your configs that doesn't suck

Because tracking changes shouldn't require a PhD in Git. This module handles
version control for configuration files with checksums, timestamps, and actual
human-readable descriptions of what changed.

Features:
- Automatic checksum generation (no more "did this actually change?")
- Version history that makes sense
- Diff comparisons that don't make your eyes bleed
- Metadata tracking that's actually useful

NOTE: All versions are stored as JSON for easy reading and modification
TODO: Add rollback functionality for when shit hits the fan
"""

class ConfigVersion(BaseModel):
    """
    Track what changed and why it matters
    
    Stores metadata about each config version including who changed it,
    what they changed, and most importantly, why they changed it.
    
    The checksum ensures nothing got fucked up between saves.
    """
    version: str
    timestamp: datetime
    description: str
    author: Optional[str] = None
    changes: Dict[str, Any]
    checksum: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ConfigVersionManager:
    """
    Keep your configs under control
    
    Handles saving, loading, and comparing config versions. Each version
    is stored as a separate file with its own checksum and metadata.
    
    Implementation Notes:
    - Versions are stored in JSON format for easy inspection
    - Checksums use SHA256 (because we're not animals)
    - Version files are named v{version}.json
    - Comparisons ignore order differences (because who cares?)
    
    FIXME: Add better error handling for corrupted version files
    """
    
    def __init__(self, version_dir: str = "config_versions"):
        """
        Set up version tracking in the specified directory
        
        Args:
            version_dir: Where to store version files (creates if missing)
        """
        self.version_dir = Path(version_dir)
        self.version_dir.mkdir(exist_ok=True)
        self.current_version: Optional[ConfigVersion] = None
        
    def save_version(
        self,
        config: Dict[str, Any],
        version: str,
        description: str,
        author: Optional[str] = None
    ) -> ConfigVersion:
        """
        Save a new config version with all its metadata
        
        Creates a checksum of the config to ensure integrity and stores
        everything in a version file. The description better be meaningful
        or future you is gonna be pissed.
        
        Args:
            config: The configuration to save
            version: Version identifier (e.g., "1.0.0")
            description: Why this change was made
            author: Who to blame when things break
        """
        import hashlib
        
        # Calculate checksum
        config_str = json.dumps(config, sort_keys=True)
        checksum = hashlib.sha256(config_str.encode()).hexdigest()
        
        # Create version metadata
        version_meta = ConfigVersion(
            version=version,
            timestamp=datetime.utcnow(),
            description=description,
            author=author,
            changes=config,
            checksum=checksum
        )
        
        # Save version file
        version_file = self.version_dir / f"v{version}.json"
        with open(version_file, 'w') as f:
            json.dump(version_meta.dict(), f, indent=2)
        
        # Update current version
        self.current_version = version_meta
        
        logger.info(
            "Saved configuration version",
            version=version,
            checksum=checksum
        )
        
        return version_meta
    
    def load_version(self, version: str) -> Dict[str, Any]:
        """Load specific configuration version"""
        version_file = self.version_dir / f"v{version}.json"
        
        if not version_file.exists():
            raise ValueError(f"Version {version} not found")
            
        with open(version_file, 'r') as f:
            version_data = json.load(f)
            
        # Validate version metadata
        version_meta = ConfigVersion(**version_data)
        self.current_version = version_meta
        
        return version_meta.changes
    
    def get_version_history(self) -> List[ConfigVersion]:
        """Get list of all configuration versions"""
        versions = []
        for version_file in sorted(self.version_dir.glob("v*.json")):
            with open(version_file, 'r') as f:
                version_data = json.load(f)
                versions.append(ConfigVersion(**version_data))
        return versions
    
    def compare_versions(
        self,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """Compare two configuration versions"""
        from deepdiff import DeepDiff
        
        config1 = self.load_version(version1)
        config2 = self.load_version(version2)
        
        return DeepDiff(config1, config2, ignore_order=True)
    
    def rollback(self, version: str) -> Dict[str, Any]:
        """Rollback to specific version"""
        config = self.load_version(version)
        
        # Save rollback as new version
        next_version = self._get_next_version()
        self.save_version(
            config,
            next_version,
            f"Rollback to version {version}",
            "system"
        )
        
        return config
    
    def _get_next_version(self) -> str:
        """Get next version number"""
        versions = [
            int(f.stem[1:])
            for f in self.version_dir.glob("v*.json")
        ]
        return str(max(versions, default=0) + 1) 