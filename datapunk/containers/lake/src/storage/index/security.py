from typing import Dict, Any, List, Optional, Union, Set
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from enum import Enum
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import threading
import uuid

logger = logging.getLogger(__name__)

class Permission(Enum):
    """Index operation permissions."""
    READ = "read"
    WRITE = "write"
    CREATE = "create"
    DELETE = "delete"
    BACKUP = "backup"
    RESTORE = "restore"
    ADMIN = "admin"

class AuditAction(Enum):
    """Audit log action types."""
    INDEX_CREATE = "index_create"
    INDEX_DELETE = "index_delete"
    INDEX_READ = "index_read"
    INDEX_WRITE = "index_write"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    PERMISSION_CHANGE = "permission_change"
    ENCRYPTION_CHANGE = "encryption_change"
    CONFIG_CHANGE = "config_change"

@dataclass
class Role:
    """Security role definition."""
    name: str
    permissions: Set[Permission]
    indexes: Set[str]  # Wildcard "*" means all indexes

@dataclass
class User:
    """User definition."""
    user_id: str
    roles: Set[str]
    api_key: str
    api_key_hash: str
    created_at: datetime
    last_access: datetime

@dataclass
class AuditLog:
    """Audit log entry."""
    timestamp: datetime
    action: AuditAction
    user_id: str
    index_name: Optional[str]
    details: Dict[str, Any]
    status: str
    client_ip: Optional[str] = None

class SecurityManager:
    """Manages index security."""
    
    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        audit_dir: Optional[Union[str, Path]] = None
    ):
        self.config_path = Path(config_path) if config_path else None
        self.audit_dir = Path(audit_dir) if audit_dir else Path("audit_logs")
        
        # Create audit directory
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize state
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}
        self._load_security_data()
        
        # Initialize encryption
        self.encryption_key = self._derive_encryption_key(
            self.config["encryption"]["master_key"]
        )
        self.fernet = Fernet(self.encryption_key)
        
        # Thread-local storage for current user context
        self.context = threading.local()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load security configuration."""
        if not self.config_path or not self.config_path.exists():
            return {
                "audit": {
                    "enabled": True,
                    "retention_days": 90,
                    "log_rotation_size_mb": 100
                },
                "authentication": {
                    "api_key_expiry_days": 90,
                    "max_failed_attempts": 5,
                    "lockout_duration_minutes": 30
                },
                "encryption": {
                    "enabled": True,
                    "algorithm": "AES-256-GCM",
                    "master_key": "default-master-key-change-in-production",
                    "key_rotation_days": 30
                }
            }
            
        with open(self.config_path, 'r') as f:
            return json.load(f)
            
    def _load_security_data(self):
        """Load roles and users from storage."""
        # TODO: Implement persistent storage
        # For now, create default admin role and user
        self.roles["admin"] = Role(
            name="admin",
            permissions=set(Permission),
            indexes={"*"}
        )
        
        self.roles["reader"] = Role(
            name="reader",
            permissions={Permission.READ},
            indexes={"*"}
        )
        
        self.roles["writer"] = Role(
            name="writer",
            permissions={Permission.READ, Permission.WRITE},
            indexes={"*"}
        )
        
        # Create admin user
        api_key = self._generate_api_key()
        self.users["admin"] = User(
            user_id="admin",
            roles={"admin"},
            api_key=api_key,
            api_key_hash=self._hash_api_key(api_key),
            created_at=datetime.now(),
            last_access=datetime.now()
        )
        
    def _derive_encryption_key(self, master_key: str) -> bytes:
        """Derive encryption key from master key."""
        salt = b"datapunk-index-encryption"  # In production, use secure random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        return base64.urlsafe_b64encode(
            kdf.derive(master_key.encode())
        )
        
    def _generate_api_key(self) -> str:
        """Generate new API key."""
        return base64.urlsafe_b64encode(
            uuid.uuid4().bytes
        ).decode('ascii')
        
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for storage."""
        return hashlib.sha256(
            api_key.encode()
        ).hexdigest()
        
    def authenticate(self, api_key: str) -> Optional[str]:
        """Authenticate user by API key."""
        api_key_hash = self._hash_api_key(api_key)
        
        for user_id, user in self.users.items():
            if hmac.compare_digest(
                user.api_key_hash.encode(),
                api_key_hash.encode()
            ):
                user.last_access = datetime.now()
                self.context.user_id = user_id
                return user_id
                
        return None
        
    def check_permission(
        self,
        user_id: str,
        permission: Permission,
        index_name: str
    ) -> bool:
        """Check if user has required permission."""
        if user_id not in self.users:
            return False
            
        user = self.users[user_id]
        
        for role_name in user.roles:
            if role_name not in self.roles:
                continue
                
            role = self.roles[role_name]
            
            if (
                permission in role.permissions and
                (index_name in role.indexes or "*" in role.indexes)
            ):
                return True
                
        return False
        
    def audit_log(
        self,
        action: AuditAction,
        index_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status: str = "success",
        client_ip: Optional[str] = None
    ):
        """Record audit log entry."""
        if not self.config["audit"]["enabled"]:
            return
            
        user_id = getattr(self.context, "user_id", "anonymous")
        
        log_entry = AuditLog(
            timestamp=datetime.now(),
            action=action,
            user_id=user_id,
            index_name=index_name,
            details=details or {},
            status=status,
            client_ip=client_ip
        )
        
        # Write to audit log file
        log_file = self.audit_dir / f"audit_{datetime.now():%Y%m}.log"
        with open(log_file, 'a') as f:
            json.dump(
                {
                    "timestamp": log_entry.timestamp.isoformat(),
                    "action": log_entry.action.value,
                    "user_id": log_entry.user_id,
                    "index_name": log_entry.index_name,
                    "details": log_entry.details,
                    "status": log_entry.status,
                    "client_ip": log_entry.client_ip
                },
                f
            )
            f.write('\n')
            
    def encrypt_data(self, data: bytes) -> bytes:
        """Encrypt data using current encryption key."""
        if not self.config["encryption"]["enabled"]:
            return data
            
        return self.fernet.encrypt(data)
        
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using current encryption key."""
        if not self.config["encryption"]["enabled"]:
            return encrypted_data
            
        return self.fernet.decrypt(encrypted_data)
        
    def create_user(
        self,
        user_id: str,
        roles: Set[str]
    ) -> str:
        """Create new user."""
        if user_id in self.users:
            raise ValueError(f"User {user_id} already exists")
            
        # Validate roles
        for role in roles:
            if role not in self.roles:
                raise ValueError(f"Role {role} does not exist")
                
        # Generate API key
        api_key = self._generate_api_key()
        
        # Create user
        self.users[user_id] = User(
            user_id=user_id,
            roles=roles,
            api_key=api_key,
            api_key_hash=self._hash_api_key(api_key),
            created_at=datetime.now(),
            last_access=datetime.now()
        )
        
        self.audit_log(
            AuditAction.PERMISSION_CHANGE,
            details={"action": "create_user", "user_id": user_id}
        )
        
        return api_key
        
    def create_role(
        self,
        name: str,
        permissions: Set[Permission],
        indexes: Set[str]
    ):
        """Create new role."""
        if name in self.roles:
            raise ValueError(f"Role {name} already exists")
            
        self.roles[name] = Role(
            name=name,
            permissions=permissions,
            indexes=indexes
        )
        
        self.audit_log(
            AuditAction.PERMISSION_CHANGE,
            details={"action": "create_role", "role": name}
        )
        
    def rotate_encryption_key(self):
        """Rotate encryption key."""
        # Generate new key
        new_key = self._derive_encryption_key(
            str(uuid.uuid4())
        )
        
        # TODO: Re-encrypt all data with new key
        
        self.encryption_key = new_key
        self.fernet = Fernet(new_key)
        
        self.audit_log(
            AuditAction.ENCRYPTION_CHANGE,
            details={"action": "key_rotation"}
        ) 