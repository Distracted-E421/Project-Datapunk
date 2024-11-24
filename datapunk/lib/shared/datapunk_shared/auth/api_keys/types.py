from typing import Dict, Set, Optional, Union
from datetime import datetime

# Key identifiers
KeyID = str
KeyHash = str
KeySecret = str

# Policy types
PathPattern = str
IPAddress = str
HTTPMethod = str

# Restriction types
TimeWindow = Dict[str, Union[str, int]]
QuotaLimit = Dict[str, int]
RateLimit = Dict[str, Union[int, float]]

# Result types
KeyValidationResult = Dict[str, Union[bool, list]]
KeyCreationResult = Dict[str, Union[str, dict]]
KeyRotationResult = Dict[str, Union[bool, str, dict]]

# Context types
KeyContext = Dict[str, Union[str, int, dict]]
ValidationContext = Dict[str, Union[str, dict]] 