import pytest
from datapunk_shared.exceptions import (
    # Base exception
    DatapunkError,
    # Service mesh errors
    MeshError, ServiceDiscoveryError, LoadBalancerError, CircuitBreakerError, RetryError,
    # Cache errors
    CacheError, CacheConnectionError, CacheWriteError,
    # Auth errors
    AuthError, TokenError, PermissionError,
    # Database errors
    DatabaseError, ConnectionError, QueryError,
    # Validation errors
    ValidationError, SchemaError, InputError,
    # Resource errors
    ResourceError, ResourceNotFoundError, ResourceExhaustedError,
    # Config errors
    ConfigError
)

def test_base_exception_creation():
    """Test base DatapunkError creation and attributes"""
    message = "Test error message"
    code = "TEST_ERROR"
    details = {"key": "value"}
    
    error = DatapunkError(message, code=code, details=details)
    
    assert str(error) == message
    assert error.code == code
    assert error.details == details

def test_base_exception_default_code():
    """Test default error code generation from class name"""
    error = DatapunkError("Test message")
    assert error.code == "DatapunkError"

def test_base_exception_default_details():
    """Test default empty details dictionary"""
    error = DatapunkError("Test message")
    assert error.details == {}

def test_mesh_error_hierarchy():
    """Test service mesh error hierarchy and inheritance"""
    # Test inheritance
    assert issubclass(MeshError, DatapunkError)
    assert issubclass(ServiceDiscoveryError, MeshError)
    assert issubclass(LoadBalancerError, MeshError)
    assert issubclass(CircuitBreakerError, MeshError)
    assert issubclass(RetryError, MeshError)
    
    # Test error creation
    error = ServiceDiscoveryError("Service not found")
    assert isinstance(error, (ServiceDiscoveryError, MeshError, DatapunkError))

def test_cache_error_hierarchy():
    """Test cache error hierarchy and inheritance"""
    assert issubclass(CacheError, DatapunkError)
    assert issubclass(CacheConnectionError, CacheError)
    assert issubclass(CacheWriteError, CacheError)
    
    error = CacheConnectionError("Redis connection failed")
    assert isinstance(error, (CacheConnectionError, CacheError, DatapunkError))

def test_auth_error_hierarchy():
    """Test authentication error hierarchy and inheritance"""
    assert issubclass(AuthError, DatapunkError)
    assert issubclass(TokenError, AuthError)
    assert issubclass(PermissionError, AuthError)
    
    error = TokenError("Invalid token")
    assert isinstance(error, (TokenError, AuthError, DatapunkError))

def test_database_error_hierarchy():
    """Test database error hierarchy and inheritance"""
    assert issubclass(DatabaseError, DatapunkError)
    assert issubclass(ConnectionError, DatabaseError)
    assert issubclass(QueryError, DatabaseError)
    
    error = QueryError("Invalid SQL syntax")
    assert isinstance(error, (QueryError, DatabaseError, DatapunkError))

def test_validation_error_hierarchy():
    """Test validation error hierarchy and inheritance"""
    assert issubclass(ValidationError, DatapunkError)
    assert issubclass(SchemaError, ValidationError)
    assert issubclass(InputError, ValidationError)
    
    error = SchemaError("Missing required field")
    assert isinstance(error, (SchemaError, ValidationError, DatapunkError))

def test_resource_error_hierarchy():
    """Test resource error hierarchy and inheritance"""
    assert issubclass(ResourceError, DatapunkError)
    assert issubclass(ResourceNotFoundError, ResourceError)
    assert issubclass(ResourceExhaustedError, ResourceError)
    
    error = ResourceNotFoundError("User not found")
    assert isinstance(error, (ResourceNotFoundError, ResourceError, DatapunkError))

def test_config_error_hierarchy():
    """Test configuration error hierarchy"""
    assert issubclass(ConfigError, DatapunkError)
    
    error = ConfigError("Invalid configuration")
    assert isinstance(error, (ConfigError, DatapunkError))

def test_error_with_details():
    """Test error creation with detailed context"""
    details = {
        "service": "auth",
        "operation": "token_validation",
        "token_id": "123",
        "error_time": "2023-01-01T00:00:00Z"
    }
    
    error = TokenError(
        message="Token validation failed",
        code="INVALID_TOKEN",
        details=details
    )
    
    assert error.code == "INVALID_TOKEN"
    assert error.details == details
    assert "Token validation failed" in str(error)

def test_error_code_inheritance():
    """Test error code inheritance and overriding"""
    # Default code from class name
    error1 = QueryError("Query failed")
    assert error1.code == "QueryError"
    
    # Override with custom code
    error2 = QueryError("Query failed", code="SQL_ERROR")
    assert error2.code == "SQL_ERROR"

def test_error_details_immutability():
    """Test that error details are not shared between instances"""
    details1 = {"key": "value1"}
    details2 = {"key": "value2"}
    
    error1 = DatapunkError("Error 1", details=details1)
    error2 = DatapunkError("Error 2", details=details2)
    
    assert error1.details != error2.details
    
    # Modifying one error's details should not affect the other
    error1.details["new_key"] = "new_value"
    assert "new_key" not in error2.details

def test_error_str_representation():
    """Test string representation of errors"""
    message = "Test error message"
    code = "TEST_ERROR"
    details = {"key": "value"}
    
    error = DatapunkError(message, code=code, details=details)
    
    # Error message should be used as string representation
    assert str(error) == message
    
    # Repr should contain class name
    assert "DatapunkError" in repr(error)

def test_nested_error_hierarchy():
    """Test deeply nested error hierarchy relationships"""
    # Create a chain of errors
    try:
        try:
            try:
                raise QueryError("Database query failed")
            except QueryError as e:
                raise DatabaseError("Database operation failed") from e
        except DatabaseError as e:
            raise DatapunkError("Service operation failed") from e
    except DatapunkError as e:
        # Verify the error chain
        assert isinstance(e.__cause__, DatabaseError)
        assert isinstance(e.__cause__.__cause__, QueryError) 