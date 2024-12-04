from typing import Dict, Set, Optional, Union
from datetime import datetime

# Type aliases for API key components
# KeyID: Unique identifier for the API key
# KeyHash: Stored hash of the API key for verification
# KeySecret: The actual API key value (only shown once at creation)
KeyID = str
KeyHash = str
KeySecret = str

# Access control and security patterns
# PathPattern: URL pattern for endpoint access control (e.g., "/api/v1/*")
# IPAddress: Client IP address for IP-based restrictions
# HTTPMethod: Allowed HTTP methods (GET, POST, etc.)
PathPattern = str
IPAddress = str
HTTPMethod = str

# Rate limiting and quota configuration types
# TimeWindow: Configuration for time-based restrictions
#   Example: {"unit": "hour", "value": 24}
TimeWindow = Dict[str, Union[str, int]]

# QuotaLimit: Defines usage limits within a period
#   Example: {"max_requests": 1000}
QuotaLimit = Dict[str, int]

# RateLimit: Defines request rate thresholds
#   Example: {"requests_per_second": 10.5}
RateLimit = Dict[str, Union[int, float]]

# Operation result types
# KeyValidationResult: Results from key validation operations
#   Contains validation status and any validation errors
KeyValidationResult = Dict[str, Union[bool, list]]

# KeyCreationResult: Results from key creation operations
#   Contains new key details and associated metadata
KeyCreationResult = Dict[str, Union[str, dict]]

# KeyRotationResult: Results from key rotation operations
#   Contains both old and new key information
KeyRotationResult = Dict[str, Union[bool, str, dict]]

# Context types for operations
# KeyContext: Metadata and settings associated with an API key
#   Includes creation time, last used, permissions, etc.
KeyContext = Dict[str, Union[str, int, dict]]

# ValidationContext: Additional context for key validation
#   Includes request details, client info, etc.
ValidationContext = Dict[str, Union[str, dict]] 