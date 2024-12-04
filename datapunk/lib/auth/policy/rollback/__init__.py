"""
Purpose: Provides a comprehensive rollback system for authentication policy changes,
allowing safe reversal of policy modifications with validation and risk assessment.

Context: Part of the authentication subsystem, this module helps maintain system 
stability by providing mechanisms to safely roll back policy changes that may have 
unintended consequences.

Design Details:
- Implements a point-in-time rollback system with validation
- Supports risk assessment before executing rollbacks
- Integrates with metrics and cache systems for monitoring and state management
"""

from typing import TYPE_CHECKING

# Core rollback functionality
from .manager import RollbackManager, RollbackPoint
from .validation import RollbackValidator, RollbackValidationResult, RollbackRisk

# Conditional imports for type checking only
if TYPE_CHECKING:
    from ....monitoring import MetricsClient  # For tracking rollback operations
    from ....cache import CacheClient         # For maintaining rollback state

# Public API surface - explicitly define what should be imported when using `from rollback import *`
__all__ = [
    'RollbackManager',      # Handles rollback operations and state management
    'RollbackPoint',        # Represents a specific point in time for rollback
    'RollbackValidator',    # Validates whether a rollback operation is safe
    'RollbackValidationResult',  # Result of rollback validation checks
    'RollbackRisk'         # Represents potential risks associated with rollback
] 