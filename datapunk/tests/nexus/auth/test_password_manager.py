import pytest
from datetime import timedelta
from src.nexus.auth.password_manager import PasswordManager, PasswordPolicy

@pytest.fixture
def password_manager():
    return PasswordManager()

@pytest.fixture
def strict_policy():
    return PasswordPolicy(
        min_length=16,
        require_uppercase=True,
        require_lowercase=True,
        require_numbers=True,
        require_special=True,
        max_repeated_chars=2,
        min_unique_chars=10,
        history_size=5,
        min_password_age=timedelta(hours=24),
        max_password_age=timedelta(days=30),
        min_strength_score=4
    )

def test_password_validation_basic(password_manager):
    # Test valid password
    is_valid, errors = password_manager.validate_password_strength("SecureP@ssw0rd123")
    assert is_valid is True
    assert not errors
    
    # Test too short
    is_valid, errors = password_manager.validate_password_strength("Short1!")
    assert is_valid is False
    assert any("length" in e.lower() for e in errors)
    
    # Test missing uppercase
    is_valid, errors = password_manager.validate_password_strength("securepassw0rd!")
    assert is_valid is False
    assert any("uppercase" in e.lower() for e in errors)
    
    # Test missing lowercase
    is_valid, errors = password_manager.validate_password_strength("SECUREPASSW0RD!")
    assert is_valid is False
    assert any("lowercase" in e.lower() for e in errors)
    
    # Test missing number
    is_valid, errors = password_manager.validate_password_strength("SecurePassword!")
    assert is_valid is False
    assert any("number" in e.lower() for e in errors)
    
    # Test missing special character
    is_valid, errors = password_manager.validate_password_strength("SecurePassword123")
    assert is_valid is False
    assert any("special" in e.lower() for e in errors)

def test_password_validation_advanced(password_manager, strict_policy):
    password_manager.policy = strict_policy
    
    # Test repeated characters
    is_valid, errors = password_manager.validate_password_strength("PassswordTest123!")
    assert is_valid is False
    assert any("repeated" in e.lower() for e in errors)
    
    # Test unique characters
    is_valid, errors = password_manager.validate_password_strength("Aaa111!!!Bbb")
    assert is_valid is False
    assert any("unique" in e.lower() for e in errors)
    
    # Test with user info
    is_valid, errors = password_manager.validate_password_strength(
        "SecureP@ssw0rd123",
        user_info={"username": "secure", "email": "test@example.com"}
    )
    assert is_valid is False  # Should fail due to containing parts of username

def test_password_history(password_manager):
    user_id = "test_user"
    
    # Set initial password
    success, _ = password_manager.update_password(user_id, "SecureP@ssw0rd123")
    assert success is True
    
    # Try to reuse the same password
    success, error = password_manager.update_password(user_id, "SecureP@ssw0rd123")
    assert success is False
    assert "history" in error.lower()
    
    # Use different password
    success, _ = password_manager.update_password(user_id, "NewSecureP@ssw0rd456")
    assert success is True
    
    # Check password history
    history = password_manager.get_password_history(user_id)
    assert len(history) == 2

def test_password_age_restrictions(password_manager):
    user_id = "test_user"
    
    # Set initial password
    success, _ = password_manager.update_password(user_id, "SecureP@ssw0rd123")
    assert success is True
    
    # Try to change password too soon
    password_manager.policy.min_password_age = timedelta(days=1)
    success, error = password_manager.update_password(user_id, "NewSecureP@ssw0rd456")
    assert success is False
    assert "recently" in error.lower()
    
    # Check if password requires change
    password_manager.policy.max_password_age = timedelta(days=0)  # Immediate expiry
    assert password_manager.password_requires_change(user_id) is True

def test_password_hashing(password_manager):
    password = "SecureP@ssw0rd123"
    
    # Hash password
    hashed = password_manager.hash_password(password)
    assert hashed != password
    assert ":" in hashed  # Should contain salt
    
    # Verify correct password
    assert password_manager.verify_password(password, hashed) is True
    
    # Verify incorrect password
    assert password_manager.verify_password("WrongPassword", hashed) is False

def test_password_strength_scoring(password_manager):
    # Test very weak password
    is_valid, errors = password_manager.validate_password_strength("password123")
    assert is_valid is False
    assert any("weak" in e.lower() for e in errors)
    
    # Test dictionary word with substitutions
    is_valid, errors = password_manager.validate_password_strength("P@ssw0rd123!")
    assert is_valid is False
    assert any("weak" in e.lower() for e in errors)
    
    # Test strong password
    is_valid, errors = password_manager.validate_password_strength("j2K9!mP#qR$vX5nL")
    assert is_valid is True
    assert not errors

def test_password_age_tracking(password_manager):
    user_id = "test_user"
    
    # Set initial password
    password_manager.update_password(user_id, "SecureP@ssw0rd123")
    
    # Check password age
    age = password_manager.get_password_age(user_id)
    assert age is not None
    assert age.total_seconds() >= 0
    
    # Check non-existent user
    age = password_manager.get_password_age("nonexistent_user")
    assert age is None

def test_concurrent_password_updates(password_manager):
    user_id = "test_user"
    
    # Set initial password
    success1, _ = password_manager.update_password(user_id, "SecureP@ssw0rd123")
    assert success1 is True
    
    # Try concurrent updates
    success2, _ = password_manager.update_password(user_id, "NewSecureP@ssw0rd456")
    success3, _ = password_manager.update_password(user_id, "AnotherP@ssw0rd789")
    
    # Check history integrity
    history = password_manager.get_password_history(user_id)
    assert len(history) <= password_manager.policy.history_size 