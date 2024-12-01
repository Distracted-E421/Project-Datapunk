from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
import os
from pathlib import Path
import logging
import tempfile

from .stats import StatisticsStore
from .exporter import StatisticsExporter, ExportFormat, ExportMetadata
from .compression import CompressionOptimizer, CompressionAlgorithm, CompressionLevel
from .migration import MigrationManager, MigrationInfo

logger = logging.getLogger(__name__)

@dataclass
class ChangeSet:
    """Represents changes since last export."""
    added: Set[str]  # New record IDs
    modified: Set[str]  # Modified record IDs
    deleted: Set[str]  # Deleted record IDs
    timestamp: datetime

@dataclass
class IncrementalMetadata:
    """Metadata for incremental exports."""
    base_export: ExportMetadata
    last_increment: datetime
    increment_count: int
    total_changes: int
    checksum: str
    parent_checksum: Optional[str] = None
    compression_info: Optional[Dict[str, Any]] = None
    version: Optional[str] = None

class IncrementalExporter:
    """Handles incremental exports of statistics."""
    
    def __init__(
        self,
        store: StatisticsStore,
        exporter: StatisticsExporter,
        base_dir: Union[str, Path],
        compression_level: CompressionLevel = CompressionLevel.BALANCED,
        auto_select_compression: bool = True,
        migrations_dir: Optional[Union[str, Path]] = None
    ):
        self.store = store
        self.exporter = exporter
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize compression optimizer
        self.compression = CompressionOptimizer(
            level=compression_level,
            auto_select=auto_select_compression
        )
        
        # Initialize migration manager
        self.migrations_dir = Path(migrations_dir) if migrations_dir else self.base_dir / "migrations"
        self.migration_manager = MigrationManager(self.migrations_dir)
        
        # Load or create state file
        self.state_file = self.base_dir / "incremental_state.json"
        self.state = self._load_state()
        
    def create_base_export(
        self,
        format: ExportFormat = ExportFormat.JSON,
        compress: bool = True,
        version: str = "1.0.0"
    ) -> IncrementalMetadata:
        """Create initial base export."""
        logger.info("Creating base export...")
        
        # Create base export
        base_path = self.base_dir / "base"
        base_path.mkdir(exist_ok=True)
        
        # Export uncompressed data first
        temp_base_file = base_path / f"base_temp.{format.value}"
        metadata = self.exporter.export_stats(
            temp_base_file,
            format=format,
            compress=False
        )
        
        # Add version information
        with open(temp_base_file, 'r') as f:
            data = json.load(f)
            data["version"] = version
            
        with open(temp_base_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        # Compress if requested
        base_file = base_path / f"base.{format.value}"
        if compress:
            compression_info = self.compression.compress_file(
                temp_base_file,
                base_file,
                metadata={"format": format.value}
            )
            os.remove(temp_base_file)
        else:
            import shutil
            shutil.move(temp_base_file, base_file)
            compression_info = {
                "algorithm": "none",
                "compression_ratio": 1.0
            }
            
        # Initialize state
        self.state = {
            "base_export": {
                "path": str(base_file),
                "metadata": metadata.__dict__,
                "compression": compression_info,
                "version": version,
                "checksum": self._calculate_checksum(base_file)
            },
            "increments": [],
            "last_export": datetime.now().isoformat()
        }
        self._save_state()
        
        return IncrementalMetadata(
            base_export=metadata,
            last_increment=datetime.now(),
            increment_count=0,
            total_changes=metadata.record_count,
            checksum=self.state["base_export"]["checksum"],
            compression_info=compression_info,
            version=version
        )
        
    def export_increment(
        self,
        format: ExportFormat = ExportFormat.JSON,
        compress: bool = True,
        min_changes: int = 1,
        target_version: Optional[str] = None
    ) -> Optional[IncrementalMetadata]:
        """Create incremental export if changes exist."""
        if not self.state:
            raise ValueError("No base export exists")
            
        # Get changes since last export
        last_export = datetime.fromisoformat(self.state["last_export"])
        changes = self._detect_changes(last_export)
        
        if not changes or sum(len(s) for s in [
            changes.added, changes.modified, changes.deleted
        ]) < min_changes:
            logger.info("No significant changes to export")
            return None
            
        logger.info(
            f"Exporting increment with {len(changes.added)} additions, "
            f"{len(changes.modified)} modifications, "
            f"{len(changes.deleted)} deletions"
        )
        
        # Create increment directory
        increment_dir = self.base_dir / "increments"
        increment_dir.mkdir(exist_ok=True)
        
        # Export changed records to temp file
        temp_increment_path = increment_dir / f"increment_{len(self.state['increments'])}_temp.{format.value}"
        
        # Get records to export
        records = []
        for record_id in changes.added | changes.modified:
            stats = self.store.get_latest_stats(record_id)
            if stats:
                records.append(stats)
                
        # Create increment file
        increment_data = {
            "changes": {
                "added": list(changes.added),
                "modified": list(changes.modified),
                "deleted": list(changes.deleted),
                "timestamp": changes.timestamp.isoformat()
            },
            "records": records,
            "version": self.state["base_export"]["version"]
        }
        
        # Apply migration if needed
        if target_version:
            try:
                increment_data = self.migration_manager.migrate(
                    increment_data,
                    target_version
                )
            except Exception as e:
                logger.error(f"Migration failed: {e}")
                raise
                
        with open(temp_increment_path, 'w') as f:
            json.dump(increment_data, f, indent=2)
            
        # Compress if requested
        increment_path = increment_dir / f"increment_{len(self.state['increments'])}.{format.value}"
        if compress:
            compression_info = self.compression.compress_file(
                temp_increment_path,
                increment_path,
                metadata={"format": format.value}
            )
            os.remove(temp_increment_path)
        else:
            import shutil
            shutil.move(temp_increment_path, increment_path)
            compression_info = {
                "algorithm": "none",
                "compression_ratio": 1.0
            }
            
        # Update state
        increment_info = {
            "path": str(increment_path),
            "changes": len(changes.added) + len(changes.modified) + len(changes.deleted),
            "timestamp": changes.timestamp.isoformat(),
            "compression": compression_info,
            "version": increment_data["version"],
            "checksum": self._calculate_checksum(increment_path)
        }
        
        self.state["increments"].append(increment_info)
        self.state["last_export"] = changes.timestamp.isoformat()
        self._save_state()
        
        return IncrementalMetadata(
            base_export=ExportMetadata(**self.state["base_export"]["metadata"]),
            last_increment=changes.timestamp,
            increment_count=len(self.state["increments"]),
            total_changes=sum(inc["changes"] for inc in self.state["increments"]),
            checksum=increment_info["checksum"],
            compression_info=compression_info,
            version=increment_data["version"],
            parent_checksum=self.state["increments"][-2]["checksum"]
            if len(self.state["increments"]) > 1
            else self.state["base_export"]["checksum"]
        )
        
    def rebuild_full_export(
        self,
        output_path: Union[str, Path],
        format: ExportFormat = ExportFormat.JSON,
        compress: bool = True,
        target_version: Optional[str] = None
    ) -> ExportMetadata:
        """Rebuild full export from base and increments."""
        if not self.state:
            raise ValueError("No base export exists")
            
        logger.info("Rebuilding full export from increments...")
        
        # Create temporary directory for decompressed files
        temp_dir = Path(tempfile.mkdtemp())
        try:
            # Decompress and load base export
            base_temp = temp_dir / "base_temp.json"
            self.compression.decompress_file(
                self.state["base_export"]["path"],
                base_temp
            )
            
            with open(base_temp, 'r') as f:
                full_data = json.load(f)
                
            # Apply increments
            for increment in self.state["increments"]:
                # Decompress increment
                inc_temp = temp_dir / "inc_temp.json"
                self.compression.decompress_file(
                    increment["path"],
                    inc_temp
                )
                
                with open(inc_temp, 'r') as f:
                    increment_data = json.load(f)
                    
                # Remove deleted records
                full_data["statistics"] = [
                    s for s in full_data["statistics"]
                    if s["index_name"] not in increment_data["changes"]["deleted"]
                ]
                
                # Update modified records and add new ones
                record_map = {
                    s["index_name"]: s
                    for s in full_data["statistics"]
                }
                
                for record in increment_data["records"]:
                    record_map[record["index_name"]] = record
                    
                full_data["statistics"] = list(record_map.values())
                
            # Apply migration if needed
            if target_version:
                try:
                    full_data = self.migration_manager.migrate(
                        full_data,
                        target_version
                    )
                except Exception as e:
                    logger.error(f"Migration failed: {e}")
                    raise
                    
            # Export full data to temp file
            temp_output = temp_dir / f"output_temp.{format.value}"
            with open(temp_output, 'w') as f:
                json.dump(full_data, f, indent=2)
                
            # Compress if requested
            if compress:
                compression_info = self.compression.compress_file(
                    temp_output,
                    output_path,
                    metadata={"format": format.value}
                )
            else:
                import shutil
                shutil.copy2(temp_output, output_path)
                
        finally:
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
        return ExportMetadata(
            timestamp=datetime.now(),
            record_count=len(full_data["statistics"]),
            format=format,
            compressed=compress,
            version=full_data.get("version")
        )
        
    def get_migration_info(self, version: str) -> Optional[MigrationInfo]:
        """Get information about a migration."""
        return self.migration_manager.get_migration_info(version)
        
    def create_migration(
        self,
        version: str,
        description: str,
        template: Optional[str] = None
    ) -> Path:
        """Create a new migration script."""
        return self.migration_manager.create_migration(
            version,
            description,
            template
        )
        
    def verify_integrity(self) -> bool:
        """Verify integrity of base export and increments."""
        if not self.state:
            return False
            
        logger.info("Verifying export integrity...")
        
        # Verify base export
        base_checksum = self._calculate_checksum(self.state["base_export"]["path"])
        if base_checksum != self.state["base_export"]["checksum"]:
            logger.error("Base export checksum mismatch")
            return False
            
        # Verify increments
        for increment in self.state["increments"]:
            checksum = self._calculate_checksum(increment["path"])
            if checksum != increment["checksum"]:
                logger.error(f"Increment checksum mismatch: {increment['path']}")
                return False
                
        return True
        
    def cleanup_old_increments(
        self,
        max_age_days: int = 30,
        max_count: int = 100
    ):
        """Remove old increments to save space."""
        if not self.state or not self.state["increments"]:
            return
            
        logger.info("Cleaning up old increments...")
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        keep_increments = []
        
        for increment in self.state["increments"]:
            timestamp = datetime.fromisoformat(increment["timestamp"])
            if timestamp > cutoff_date and len(keep_increments) < max_count:
                keep_increments.append(increment)
            else:
                # Remove increment file
                try:
                    os.remove(increment["path"])
                except OSError:
                    logger.warning(f"Failed to remove increment: {increment['path']}")
                    
        self.state["increments"] = keep_increments
        self._save_state()
        
    def _detect_changes(self, since: datetime) -> ChangeSet:
        """Detect changes since last export."""
        # Get current state
        current_stats = self.store.get_stats_history("*")
        current_ids = {s.index_name for s in current_stats}
        
        # Get previous state
        previous_stats = self.store.get_stats_history("*", end_time=since)
        previous_ids = {s.index_name for s in previous_stats}
        
        # Find changes
        added = current_ids - previous_ids
        deleted = previous_ids - current_ids
        
        # Find modifications
        modified = set()
        for stat in current_stats:
            if (
                stat.index_name not in added and
                stat.created_at > since
            ):
                modified.add(stat.index_name)
                
        return ChangeSet(
            added=added,
            modified=modified,
            deleted=deleted,
            timestamp=datetime.now()
        )
        
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}
        
    def _save_state(self):
        """Save state to file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def _calculate_checksum(self, path: Union[str, Path]) -> str:
        """Calculate SHA-256 checksum of file."""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for block in iter(lambda: f.read(4096), b''):
                sha256.update(block)
        return sha256.hexdigest() 