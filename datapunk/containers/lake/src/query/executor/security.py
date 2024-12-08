from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Callable
from abc import ABC, abstractmethod
import time
import hashlib
import logging
from datetime import datetime, timedelta
from enum import Enum, auto
from .query_exec_core import ExecutionOperator, ExecutionContext
from ..parser.query_parser_core import QueryNode, QueryPlan

class AccessLevel(Enum):
    """Possible access levels for data."""
    PUBLIC = auto()
    INTERNAL = auto()
    CONFIDENTIAL = auto()
    RESTRICTED = auto()

class SecurityPolicy:
    """Container for security policies."""
    
    def __init__(self):
        self.column_access_levels: Dict[str, AccessLevel] = {}
        self.table_access_levels: Dict[str, AccessLevel] = {}
        self.required_roles: Dict[str, Set[str]] = {}
        self.encryption_required: Set[str] = set()
        self.audit_required: Set[str] = set()
        
    def add_column_policy(self, column: str, 
                         level: AccessLevel) -> None:
        """Add access level policy for a column."""
        self.column_access_levels[column] = level
        
    def add_table_policy(self, table: str, 
                        level: AccessLevel) -> None:
        """Add access level policy for a table."""
        self.table_access_levels[table] = level
        
    def add_required_roles(self, resource: str, 
                          roles: Set[str]) -> None:
        """Add required roles for accessing a resource."""
        self.required_roles[resource] = roles
        
    def require_encryption(self, resource: str) -> None:
        """Mark a resource as requiring encryption."""
        self.encryption_required.add(resource)
        
    def require_audit(self, resource: str) -> None:
        """Mark a resource as requiring audit logging."""
        self.audit_required.add(resource)

class SecurityContext:
    """Container for security context."""
    
    def __init__(self, user_id: str, roles: Set[str],
                 access_level: AccessLevel = AccessLevel.PUBLIC):
        self.user_id = user_id
        self.roles = roles
        self.access_level = access_level
        self.session_id = hashlib.sha256(
            f"{user_id}:{time.time()}".encode()).hexdigest()

class AuditLog:
    """Manages security audit logging."""
    
    def __init__(self):
        self.logger = logging.getLogger("security_audit")
        
    def log_access(self, security_context: SecurityContext,
                  resource: str, operation: str) -> None:
        """Log an access attempt."""
        self.logger.info(
            f"Access: user={security_context.user_id} "
            f"session={security_context.session_id} "
            f"resource={resource} operation={operation}"
        )
        
    def log_violation(self, security_context: SecurityContext,
                     resource: str, operation: str,
                     reason: str) -> None:
        """Log a security violation."""
        self.logger.warning(
            f"Violation: user={security_context.user_id} "
            f"session={security_context.session_id} "
            f"resource={resource} operation={operation} "
            f"reason={reason}"
        )

class SecurityManager:
    """Manages query execution security."""
    
    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.audit_log = AuditLog()
        
    def check_access(self, security_context: SecurityContext,
                    resource: str) -> bool:
        """Check if access is allowed to a resource."""
        # Check access level
        if resource in self.policy.table_access_levels:
            required_level = self.policy.table_access_levels[resource]
            if security_context.access_level.value < required_level.value:
                self.audit_log.log_violation(
                    security_context,
                    resource,
                    "access",
                    f"Insufficient access level: {security_context.access_level}"
                )
                return False
                
        # Check roles
        if resource in self.policy.required_roles:
            required_roles = self.policy.required_roles[resource]
            if not required_roles.intersection(security_context.roles):
                self.audit_log.log_violation(
                    security_context,
                    resource,
                    "access",
                    f"Missing required roles: {required_roles}"
                )
                return False
                
        self.audit_log.log_access(
            security_context,
            resource,
            "access"
        )
        return True
        
    def filter_columns(self, security_context: SecurityContext,
                      columns: List[str]) -> List[str]:
        """Filter columns based on access level."""
        allowed_columns = []
        
        for column in columns:
            if column in self.policy.column_access_levels:
                required_level = self.policy.column_access_levels[column]
                if security_context.access_level.value >= required_level.value:
                    allowed_columns.append(column)
            else:
                allowed_columns.append(column)
                
        return allowed_columns

class SecureContext(ExecutionContext):
    """Extended context with security support."""
    
    def __init__(self, security_context: SecurityContext,
                 policy: SecurityPolicy):
        super().__init__()
        self.security_context = security_context
        self.security_manager = SecurityManager(policy)

class SecureOperator(ExecutionOperator):
    """Base operator with security controls."""
    
    def __init__(self, node: QueryNode, context: SecureContext):
        super().__init__(node, context)
        self.context = context  # Type hint for IDE
        self.operator_id = str(id(self))
        
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with security controls."""
        # Check table access if applicable
        if hasattr(self.node, 'table_name'):
            if not self.context.security_manager.check_access(
                self.context.security_context,
                self.node.table_name
            ):
                raise PermissionError(
                    f"Access denied to table {self.node.table_name}"
                )
                
        # Filter columns if applicable
        if hasattr(self.node, 'columns'):
            self.node.columns = self.context.security_manager.filter_columns(
                self.context.security_context,
                self.node.columns
            )
            
        # Execute with filtered access
        yield from super().execute()

class SecureTableScan(SecureOperator):
    """Secure implementation of table scan."""
    
    def execute(self) -> Iterator[Dict[str, Any]]:
        """Execute with row-level security."""
        for row in super().execute():
            # Apply row-level security if defined
            if self._check_row_access(row):
                # Filter sensitive columns
                filtered_row = self._filter_sensitive_data(row)
                yield filtered_row
                
    def _check_row_access(self, row: Dict[str, Any]) -> bool:
        """Check if user has access to this row."""
        # Implement row-level security checks
        return True
        
    def _filter_sensitive_data(self, 
                             row: Dict[str, Any]) -> Dict[str, Any]:
        """Filter or mask sensitive data."""
        filtered = {}
        for column, value in row.items():
            if column in self.context.security_manager.policy.column_access_levels:
                level = self.context.security_manager.policy.column_access_levels[column]
                if self.context.security_context.access_level.value >= level.value:
                    filtered[column] = value
                else:
                    filtered[column] = self._mask_sensitive_value(value)
            else:
                filtered[column] = value
        return filtered
        
    def _mask_sensitive_value(self, value: Any) -> str:
        """Mask sensitive values."""
        if isinstance(value, str):
            return '*' * len(value)
        return '****'

class SecureExecutionEngine:
    """Execution engine with security controls."""
    
    def __init__(self, security_context: SecurityContext,
                 policy: SecurityPolicy):
        self.context = SecureContext(security_context, policy)
        
    def execute_plan(self, plan: QueryPlan) -> Iterator[Dict[str, Any]]:
        """Execute a query plan with security controls."""
        # Validate query plan against security policy
        self._validate_plan(plan)
        
        # Build and execute secure tree
        root_operator = self._build_secure_tree(plan.root)
        yield from root_operator.execute()
        
    def _validate_plan(self, plan: QueryPlan) -> None:
        """Validate query plan against security policy."""
        def validate_node(node: QueryNode) -> None:
            # Check table access
            if hasattr(node, 'table_name'):
                if not self.context.security_manager.check_access(
                    self.context.security_context,
                    node.table_name
                ):
                    raise PermissionError(
                        f"Access denied to table {node.table_name}"
                    )
                    
            # Check column access
            if hasattr(node, 'columns'):
                filtered_columns = self.context.security_manager.filter_columns(
                    self.context.security_context,
                    node.columns
                )
                if len(filtered_columns) < len(node.columns):
                    raise PermissionError(
                        "Access denied to one or more columns"
                    )
                    
            # Recursively validate children
            for child in node.children:
                validate_node(child)
                
        validate_node(plan.root)
        
    def _build_secure_tree(self, node: QueryNode) -> SecureOperator:
        """Build a secure execution tree."""
        if node.operation == 'table_scan':
            operator = SecureTableScan(node, self.context)
        else:
            operator = SecureOperator(node, self.context)
            
        # Recursively build children
        for child in node.children:
            child_operator = self._build_secure_tree(child)
            operator.add_child(child_operator)
            
        return operator 