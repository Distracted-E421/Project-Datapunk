from typing import Dict, Any, List, Optional, Set
import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import hashlib
from .node import PartitionNode
from .network import NetworkManager, NetworkMessage, MessageTypes

class BackupState:
    """Represents backup state of a partition"""
    
    def __init__(self, partition_id: str):
        self.partition_id = partition_id
        self.last_backup = None
        self.backup_size = 0
        self.checksum = None
        self.version = 0
        self.metadata: Dict[str, Any] = {}
        
class RecoveryManager:
    """Manages backup and recovery of partitions"""
    
    def __init__(self, node: PartitionNode,
                 network: NetworkManager,
                 backup_dir: str):
        self.node = node
        self.network = network
        self.backup_dir = Path(backup_dir)
        self.backup_states: Dict[str, BackupState] = {}
        self.logger = logging.getLogger(__name__)
        self._stop = False
        self._backup_thread = None
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Register message handlers
        self._register_handlers()
        
        # Configuration
        self.backup_interval = timedelta(hours=1)
        self.retention_period = timedelta(days=7)
        self.max_concurrent_restores = 3
        self.restore_semaphore = asyncio.Semaphore(self.max_concurrent_restores)
        
    async def start(self):
        """Start recovery manager"""
        self._stop = False
        self._backup_thread = asyncio.create_task(self._backup_loop())
        
    async def stop(self):
        """Stop recovery manager"""
        self._stop = True
        if self._backup_thread:
            self._backup_thread.cancel()
            try:
                await self._backup_thread
            except asyncio.CancelledError:
                pass
                
    async def create_backup(self, partition_id: str) -> bool:
        """Create backup of a partition"""
        try:
            # Get partition data
            data = await self._get_partition_data(partition_id)
            if not data:
                return False
                
            # Create backup state if not exists
            if partition_id not in self.backup_states:
                self.backup_states[partition_id] = BackupState(partition_id)
                
            state = self.backup_states[partition_id]
            
            # Create backup file
            backup_path = self._get_backup_path(partition_id, state.version)
            
            # Write data
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(data))
                
            # Update state
            state.last_backup = datetime.now()
            state.backup_size = backup_path.stat().st_size
            state.checksum = self._calculate_checksum(backup_path)
            state.version += 1
            state.metadata = {
                'timestamp': state.last_backup.isoformat(),
                'size': state.backup_size,
                'checksum': state.checksum,
                'version': state.version
            }
            
            # Write metadata
            await self._write_metadata(partition_id, state.metadata)
            
            return True
        except Exception as e:
            self.logger.error(f"Backup failed for partition {partition_id}: {str(e)}")
            return False
            
    async def restore_partition(self, partition_id: str,
                              version: Optional[int] = None) -> bool:
        """Restore partition from backup"""
        async with self.restore_semaphore:
            try:
                state = self.backup_states.get(partition_id)
                if not state:
                    return False
                    
                # Determine version to restore
                restore_version = version if version is not None else state.version - 1
                
                # Get backup path
                backup_path = self._get_backup_path(partition_id, restore_version)
                if not backup_path.exists():
                    return False
                    
                # Verify checksum
                current_checksum = self._calculate_checksum(backup_path)
                if current_checksum != state.checksum:
                    self.logger.error(f"Checksum mismatch for partition {partition_id}")
                    return False
                    
                # Read backup data
                async with aiofiles.open(backup_path, 'r') as f:
                    data = json.loads(await f.read())
                    
                # Restore partition
                success = await self._restore_partition_data(partition_id, data)
                
                if success:
                    # Notify other nodes
                    await self._notify_restore_complete(partition_id, restore_version)
                    
                return success
            except Exception as e:
                self.logger.error(f"Restore failed for partition {partition_id}: {str(e)}")
                return False
                
    def _register_handlers(self):
        """Register message handlers"""
        self.network.register_handler(
            MessageTypes.RECOVERY_REQUEST,
            self._handle_recovery_request
        )
        self.network.register_handler(
            MessageTypes.RECOVERY_RESPONSE,
            self._handle_recovery_response
        )
        
    async def _backup_loop(self):
        """Background loop for periodic backups"""
        while not self._stop:
            try:
                await self._perform_periodic_backup()
                await self._cleanup_old_backups()
            except Exception as e:
                self.logger.error(f"Backup loop error: {str(e)}")
                
            # Sleep until next backup
            await asyncio.sleep(self.backup_interval.total_seconds())
            
    async def _perform_periodic_backup(self):
        """Perform periodic backup of all partitions"""
        for partition_id in self.node.get_partitions():
            if await self._should_backup(partition_id):
                await self.create_backup(partition_id)
                
    async def _should_backup(self, partition_id: str) -> bool:
        """Check if partition should be backed up"""
        state = self.backup_states.get(partition_id)
        if not state or not state.last_backup:
            return True
            
        time_since_backup = datetime.now() - state.last_backup
        return time_since_backup >= self.backup_interval
        
    async def _cleanup_old_backups(self):
        """Clean up old backup files"""
        now = datetime.now()
        for state in self.backup_states.values():
            if not state.last_backup:
                continue
                
            # Find old backup files
            for version in range(state.version):
                backup_path = self._get_backup_path(state.partition_id, version)
                if not backup_path.exists():
                    continue
                    
                # Check age
                backup_time = datetime.fromtimestamp(backup_path.stat().st_mtime)
                if now - backup_time > self.retention_period:
                    backup_path.unlink()
                    
    def _get_backup_path(self, partition_id: str, version: int) -> Path:
        """Get path for backup file"""
        return self.backup_dir / f"{partition_id}_v{version}.backup"
        
    async def _write_metadata(self, partition_id: str,
                            metadata: Dict[str, Any]):
        """Write backup metadata"""
        metadata_path = self.backup_dir / f"{partition_id}_metadata.json"
        async with aiofiles.open(metadata_path, 'w') as f:
            await f.write(json.dumps(metadata))
            
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    async def _get_partition_data(self, partition_id: str) -> Optional[Dict[str, Any]]:
        """Get partition data for backup"""
        # This would integrate with your partition storage system
        pass
        
    async def _restore_partition_data(self, partition_id: str,
                                    data: Dict[str, Any]) -> bool:
        """Restore partition data"""
        # This would integrate with your partition storage system
        pass
        
    async def _notify_restore_complete(self, partition_id: str,
                                     version: int):
        """Notify other nodes of restore completion"""
        notification = {
            'partition_id': partition_id,
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'node_id': self.node.node_id
        }
        
        await self.network.broadcast(
            MessageTypes.RECOVERY_RESPONSE,
            notification,
            self._get_replica_nodes(partition_id)
        )
        
    async def _handle_recovery_request(self, message: NetworkMessage):
        """Handle recovery request from another node"""
        request = message.payload
        partition_id = request['partition_id']
        
        if not self.node.has_partition(partition_id):
            return
            
        # Send backup to requesting node
        state = self.backup_states.get(partition_id)
        if not state:
            return
            
        backup_path = self._get_backup_path(partition_id, state.version - 1)
        if not backup_path.exists():
            return
            
        # Read backup data
        async with aiofiles.open(backup_path, 'r') as f:
            data = json.loads(await f.read())
            
        response = {
            'partition_id': partition_id,
            'version': state.version - 1,
            'data': data,
            'checksum': state.checksum
        }
        
        await self.network.send_message(NetworkMessage(
            MessageTypes.RECOVERY_RESPONSE,
            self.node.node_id,
            message.source,
            response
        ))
        
    async def _handle_recovery_response(self, message: NetworkMessage):
        """Handle recovery response from another node"""
        response = message.payload
        partition_id = response['partition_id']
        
        # Verify response
        if not self._verify_recovery_response(response):
            return
            
        # Update local state
        if partition_id in self.backup_states:
            state = self.backup_states[partition_id]
            state.version = response['version']
            state.checksum = response['checksum']
            state.last_backup = datetime.now()
            
    def _verify_recovery_response(self, response: Dict[str, Any]) -> bool:
        """Verify recovery response data"""
        try:
            # Verify required fields
            required_fields = ['partition_id', 'version', 'data', 'checksum']
            if not all(field in response for field in required_fields):
                return False
                
            # Verify data integrity
            data_str = json.dumps(response['data'])
            calculated_checksum = hashlib.sha256(data_str.encode()).hexdigest()
            
            return calculated_checksum == response['checksum']
        except Exception:
            return False
            
    def _get_replica_nodes(self, partition_id: str) -> List[str]:
        """Get nodes that should have replicas of partition"""
        # This would integrate with your replication system
        return []
        
    def get_backup_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all backups"""
        status = {}
        for partition_id, state in self.backup_states.items():
            status[partition_id] = {
                'last_backup': state.last_backup.isoformat() if state.last_backup else None,
                'backup_size': state.backup_size,
                'version': state.version,
                'has_backup': self._get_backup_path(partition_id, state.version - 1).exists()
            }
        return status 