from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Set
import re
import hashlib
import zxcvbn  # For password strength estimation

@dataclass
class PasswordPolicy:
    min_length: int = 12
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special: bool = True
    max_repeated_chars: int = 3
    min_unique_chars: int = 7
    history_size: int = 10  # Number of previous passwords to remember
    min_password_age: timedelta = timedelta(days=1)  # Minimum time before password can be changed
    max_password_age: timedelta = timedelta(days=90)  # Maximum password age before requiring change
    min_strength_score: int = 3  # Minimum zxcvbn strength score (0-4)

@dataclass
class PasswordHistory:
    user_id: str
    current_hash: str
    previous_hashes: List[str] = field(default_factory=list)
    last_change: datetime = field(default_factory=datetime.utcnow)
    previous_changes: List[datetime] = field(default_factory=list)

class PasswordManager:
    def __init__(self, policy: Optional[PasswordPolicy] = None):
        self.policy = policy or PasswordPolicy()
        self._history: dict[str, PasswordHistory] = {}
        
    def validate_password_strength(self, password: str, user_info: dict = None) -> tuple[bool, List[str]]:
        """Validate password against policy and check strength."""
        errors = []
        
        # Basic policy checks
        if len(password) < self.policy.min_length:
            errors.append(f"Password must be at least {self.policy.min_length} characters long")
            
        if self.policy.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
            
        if self.policy.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
            
        if self.policy.require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
            
        if self.policy.require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
            
        # Check for repeated characters
        for char in set(password):
            if password.count(char) > self.policy.max_repeated_chars:
                errors.append(f"Character '{char}' is repeated too many times")
                break
                
        # Check unique characters
        if len(set(password)) < self.policy.min_unique_chars:
            errors.append(f"Password must contain at least {self.policy.min_unique_chars} unique characters")
            
        # Check password strength using zxcvbn
        strength_result = zxcvbn.zxcvbn(password, user_inputs=list(user_info.values()) if user_info else None)
        if strength_result['score'] < self.policy.min_strength_score:
            errors.append(f"Password is too weak. Suggestions: {', '.join(strength_result['feedback']['suggestions'])}")
            
        return len(errors) == 0, errors
        
    def hash_password(self, password: str) -> str:
        """Hash password using strong algorithm."""
        salt = hashlib.sha256(str(datetime.utcnow().timestamp()).encode()).hexdigest()
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000,  # Number of iterations
            dklen=64  # Length of the derived key
        ).hex() + ':' + salt
        
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash."""
        if ':' not in password_hash:
            return False
            
        stored_hash, salt = password_hash.split(':')
        verify_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000,
            dklen=64
        ).hex()
        return stored_hash == verify_hash
        
    def can_change_password(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if user can change their password."""
        if user_id not in self._history:
            return True, None
            
        history = self._history[user_id]
        time_since_change = datetime.utcnow() - history.last_change
        
        if time_since_change < self.policy.min_password_age:
            return False, f"Password was changed too recently. Wait {self.policy.min_password_age - time_since_change}"
            
        return True, None
        
    def password_requires_change(self, user_id: str) -> bool:
        """Check if password needs to be changed due to age."""
        if user_id not in self._history:
            return False
            
        history = self._history[user_id]
        time_since_change = datetime.utcnow() - history.last_change
        return time_since_change > self.policy.max_password_age
        
    def update_password(self, user_id: str, new_password: str, user_info: dict = None) -> tuple[bool, Optional[str]]:
        """Update user's password if it meets all requirements."""
        # Validate password strength
        is_valid, errors = self.validate_password_strength(new_password, user_info)
        if not is_valid:
            return False, "\n".join(errors)
            
        # Check if password change is allowed
        can_change, error = self.can_change_password(user_id)
        if not can_change:
            return False, error
            
        # Hash new password
        new_hash = self.hash_password(new_password)
        
        # Check password history
        if user_id in self._history:
            history = self._history[user_id]
            all_hashes = [history.current_hash] + history.previous_hashes
            
            # Check if password was used before
            for old_hash in all_hashes:
                if self.verify_password(new_password, old_hash):
                    return False, f"Password was used in the last {self.policy.history_size} changes"
                    
            # Update history
            history.previous_hashes = ([history.current_hash] + history.previous_hashes)[:self.policy.history_size-1]
            history.previous_changes = ([history.last_change] + history.previous_changes)[:self.policy.history_size-1]
            history.current_hash = new_hash
            history.last_change = datetime.utcnow()
        else:
            # Create new history
            self._history[user_id] = PasswordHistory(
                user_id=user_id,
                current_hash=new_hash
            )
            
        return True, None
        
    def get_password_age(self, user_id: str) -> Optional[timedelta]:
        """Get the age of the current password."""
        if user_id not in self._history:
            return None
            
        return datetime.utcnow() - self._history[user_id].last_change
        
    def get_password_history(self, user_id: str) -> Optional[List[datetime]]:
        """Get password change history dates."""
        if user_id not in self._history:
            return None
            
        history = self._history[user_id]
        return [history.last_change] + history.previous_changes 