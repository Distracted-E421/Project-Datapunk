from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import shutil
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import queue

from .manager import IndexManager
from .stats import StatisticsStore
from .monitor import IndexMonitor

logger = logging.getLogger(__name__)

@dataclass
class BackupMetadata:
    """Metadata for a backup."""
    backup_id: str
    timestamp: datetime
    index_name: str
    backup_type: str  # full, incremental
    size_bytes: int
    checksum: str
    parent_backup_id: Optional[str] = None
    
@dataclass
class RecoveryPoint:
    """Point-in-time recovery marker."""
    timestamp: datetime
    backup_id: str
    transaction_id: str
    consistent: bool
    indexes: Set[str]

class BackupManager:
    """Manages index backups and recovery."""
    
    def __init__(
        self,
        store: StatisticsStore,
        manager: IndexManager,
        monitor: IndexMonitor,
        backup_dir: Union[str, Path],
        config_path: Optional[Union[str, Path]] = None
    ):
        self.store = store
        self.manager = manager
        self.monitor = monitor
        self.backup_dir = Path(backup_dir)
        self.config_path = Path(config_path) if config_path else None
        
        # Create backup directory structure
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        (self.backup_dir / "full").mkdir(exist_ok=True)
        (self.backup_dir / "incremental").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.recovery_points: List[RecoveryPoint] = []
        self.backup_metadata: Dict[str, BackupMetadata] = {}
        self._load_metadata()
        
        # Background worker
        self._backup_queue = queue.Queue()
        self._worker_thread = threading.Thread(
            target=self._backup_worker,
            daemon=True
        )
        self._worker_thread.start()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load backup configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "retention": {
                    "full_backups_days": 30,
                    "incremental_backups_days": 7,
                    "recovery_points_count": 100
                },
                "scheduling": {
                    "full_backup_interval_hours": 24,
                    "incremental_backup_interval_minutes": 15
                },
                "performance": {
                    "compression_level": 6,
                    "max_concurrent_backups": 3,
                    "chunk_size_mb": 64
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _load_metadata(self):
        """Load backup metadata from disk."""
        metadata_dir = self.backup_dir / "metadata"
        for meta_file in metadata_dir.glob("*.json"):
            with open(meta_file, 'r') as f:
                data = json.load(f)
                metadata = BackupMetadata(
                    backup_id=data["backup_id"],
                    timestamp=datetime.fromisoformat(data["timestamp"]),
                    index_name=data["index_name"],
                    backup_type=data["backup_type"],
                    size_bytes=data["size_bytes"],
                    checksum=data["checksum"],
                    parent_backup_id=data.get("parent_backup_id")
                )
                self.backup_metadata[metadata.backup_id] = metadata
                
    def _save_metadata(self, metadata: BackupMetadata):
        """Save backup metadata to disk."""
        meta_file = self.backup_dir / "metadata" / f"{metadata.backup_id}.json"
        with open(meta_file, 'w') as f:
            json.dump({
                "backup_id": metadata.backup_id,
                "timestamp": metadata.timestamp.isoformat(),
                "index_name": metadata.index_name,
                "backup_type": metadata.backup_type,
                "size_bytes": metadata.size_bytes,
                "checksum": metadata.checksum,
                "parent_backup_id": metadata.parent_backup_id
            }, f, indent=2)
            
    def create_backup(
        self,
        index_name: str,
        backup_type: str = "full",
        async_backup: bool = True
    ) -> str:
        """Create a new backup."""
        backup_id = hashlib.sha256(
            f"{index_name}:{backup_type}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        if async_backup:
            self._backup_queue.put((backup_id, index_name, backup_type))
            return backup_id
            
        return self._perform_backup(backup_id, index_name, backup_type)
        
    def _perform_backup(
        self,
        backup_id: str,
        index_name: str,
        backup_type: str
    ) -> str:
        """Perform the actual backup operation."""
        logger.info(f"Starting {backup_type} backup of {index_name}")
        
        # Get index data
        index_data = self.manager.export_index(index_name)
        if not index_data:
            raise ValueError(f"Index {index_name} not found")
            
        # Calculate parent backup for incremental
        parent_backup_id = None
        if backup_type == "incremental":
            parent_backup_id = self._find_latest_backup(
                index_name,
                "full"
            )
            if not parent_backup_id:
                backup_type = "full"
                
        # Prepare backup path
        backup_path = (
            self.backup_dir / backup_type / f"{backup_id}.backup"
        )
        
        # Write backup data
        with open(backup_path, 'wb') as f:
            # TODO: Implement compression and chunking
            f.write(json.dumps(index_data).encode())
            
        # Calculate checksum
        checksum = hashlib.sha256(
            open(backup_path, 'rb').read()
        ).hexdigest()
        
        # Create and save metadata
        metadata = BackupMetadata(
            backup_id=backup_id,
            timestamp=datetime.now(),
            index_name=index_name,
            backup_type=backup_type,
            size_bytes=backup_path.stat().st_size,
            checksum=checksum,
            parent_backup_id=parent_backup_id
        )
        
        self.backup_metadata[backup_id] = metadata
        self._save_metadata(metadata)
        
        logger.info(f"Completed {backup_type} backup of {index_name}")
        return backup_id
        
    def _backup_worker(self):
        """Background worker for processing async backups."""
        while True:
            try:
                backup_id, index_name, backup_type = self._backup_queue.get()
                self._perform_backup(backup_id, index_name, backup_type)
            except Exception as e:
                logger.error(f"Backup failed: {str(e)}")
            finally:
                self._backup_queue.task_done()
                
    def restore_backup(
        self,
        backup_id: str,
        target_index_name: Optional[str] = None
    ) -> bool:
        """Restore from a backup."""
        if backup_id not in self.backup_metadata:
            raise ValueError(f"Backup {backup_id} not found")
            
        metadata = self.backup_metadata[backup_id]
        backup_path = (
            self.backup_dir / metadata.backup_type / f"{backup_id}.backup"
        )
        
        if not backup_path.exists():
            raise ValueError(f"Backup file not found: {backup_path}")
            
        # Verify checksum
        current_checksum = hashlib.sha256(
            open(backup_path, 'rb').read()
        ).hexdigest()
        
        if current_checksum != metadata.checksum:
            raise ValueError("Backup file corrupted")
            
        # Load backup data
        with open(backup_path, 'rb') as f:
            # TODO: Handle decompression
            index_data = json.loads(f.read().decode())
            
        # Restore to original or new name
        target_name = target_index_name or metadata.index_name
        return self.manager.import_index(target_name, index_data)
        
    def create_recovery_point(
        self,
        transaction_id: str,
        indexes: Set[str]
    ) -> str:
        """Create a point-in-time recovery marker."""
        # Create recovery point
        point = RecoveryPoint(
            timestamp=datetime.now(),
            backup_id=self.create_backup(
                list(indexes)[0],
                "full",
                async_backup=False
            ),
            transaction_id=transaction_id,
            consistent=True,
            indexes=indexes
        )
        
        self.recovery_points.append(point)
        
        # Trim old recovery points
        max_points = self.config["retention"]["recovery_points_count"]
        if len(self.recovery_points) > max_points:
            self.recovery_points = self.recovery_points[-max_points:]
            
        return point.backup_id
        
    def restore_to_point(
        self,
        transaction_id: str
    ) -> bool:
        """Restore to a specific recovery point."""
        # Find recovery point
        point = next(
            (p for p in reversed(self.recovery_points)
             if p.transaction_id == transaction_id),
            None
        )
        
        if not point:
            raise ValueError(f"Recovery point not found: {transaction_id}")
            
        # Restore from backup
        return self.restore_backup(point.backup_id)
        
    def _find_latest_backup(
        self,
        index_name: str,
        backup_type: str
    ) -> Optional[str]:
        """Find the latest backup of specified type."""
        matching_backups = [
            meta for meta in self.backup_metadata.values()
            if meta.index_name == index_name and
            meta.backup_type == backup_type
        ]
        
        if not matching_backups:
            return None
            
        latest = max(matching_backups, key=lambda m: m.timestamp)
        return latest.backup_id
        
    def cleanup_old_backups(self):
        """Remove expired backups."""
        now = datetime.now()
        
        # Calculate retention periods
        full_retention = timedelta(
            days=self.config["retention"]["full_backups_days"]
        )
        incr_retention = timedelta(
            days=self.config["retention"]["incremental_backups_days"]
        )
        
        # Find expired backups
        expired_backups = [
            meta for meta in self.backup_metadata.values()
            if (
                (meta.backup_type == "full" and
                 now - meta.timestamp > full_retention) or
                (meta.backup_type == "incremental" and
                 now - meta.timestamp > incr_retention)
            )
        ]
        
        # Remove expired backups
        for meta in expired_backups:
            backup_path = (
                self.backup_dir / meta.backup_type / f"{meta.backup_id}.backup"
            )
            meta_path = (
                self.backup_dir / "metadata" / f"{meta.backup_id}.json"
            )
            
            try:
                backup_path.unlink(missing_ok=True)
                meta_path.unlink(missing_ok=True)
                del self.backup_metadata[meta.backup_id]
            except Exception as e:
                logger.error(f"Failed to remove backup {meta.backup_id}: {str(e)}")
                
    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity."""
        if backup_id not in self.backup_metadata:
            raise ValueError(f"Backup {backup_id} not found")
            
        metadata = self.backup_metadata[backup_id]
        backup_path = (
            self.backup_dir / metadata.backup_type / f"{backup_id}.backup"
        )
        
        if not backup_path.exists():
            return False
            
        # Verify checksum
        current_checksum = hashlib.sha256(
            open(backup_path, 'rb').read()
        ).hexdigest()
        
        return current_checksum == metadata.checksum