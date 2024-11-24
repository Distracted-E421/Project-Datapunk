"""Utilities for type validation and conversion."""
from typing import Dict, Any, Optional, Type, TypeVar, Union, List, Set, Callable
from datetime import datetime, timedelta, timezone
import structlog
from enum import Enum
from dataclasses import dataclass, asdict
import json
import yaml
import msgpack
import base64
import uuid
import re
import xml.etree.ElementTree as ET
from decimal import Decimal

from .types import (
    ResourceType, AccessLevel, AuthStatus,
    AccessContext, AccessResult, AuthContext, AuthResult
)
from ..types import Result, Metadata
from .exceptions import ValidationError

logger = structlog.get_logger()

T = TypeVar('T')

@dataclass
class TypeValidationResult:
    """Result of type validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    converted_value: Optional[Any] = None

class TypeValidator:
    """Validates and converts types."""
    
    @staticmethod
    def validate_enum(value: Any,
                     enum_class: Type[Enum]) -> TypeValidationResult:
        """Validate enum value."""
        errors = []
        warnings = []
        converted = None
        
        try:
            # Handle string values
            if isinstance(value, str):
                try:
                    converted = enum_class[value.upper()]
                except KeyError:
                    try:
                        converted = enum_class(value.lower())
                    except ValueError:
                        errors.append(
                            f"Invalid value '{value}' for {enum_class.__name__}"
                        )
            # Handle enum values
            elif isinstance(value, enum_class):
                converted = value
            else:
                errors.append(
                    f"Expected str or {enum_class.__name__}, got {type(value)}"
                )
            
            return TypeValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                converted_value=converted
            )
            
        except Exception as e:
            return TypeValidationResult(
                valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                converted_value=None
            )
    
    @staticmethod
    def validate_context(context: Dict[str, Any],
                        required_fields: Set[str],
                        optional_fields: Optional[Set[str]] = None) -> TypeValidationResult:
        """Validate context dictionary."""
        errors = []
        warnings = []
        
        # Check required fields
        missing = required_fields - set(context.keys())
        if missing:
            errors.append(f"Missing required fields: {missing}")
        
        # Check for unknown fields
        allowed = required_fields | (optional_fields or set())
        unknown = set(context.keys()) - allowed
        if unknown:
            warnings.append(f"Unknown fields present: {unknown}")
        
        return TypeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            converted_value=context if len(errors) == 0 else None
        )
    
    @staticmethod
    def validate_metadata(metadata: Optional[Dict[str, Any]]) -> TypeValidationResult:
        """Validate metadata dictionary."""
        errors = []
        warnings = []
        
        if metadata is not None:
            if not isinstance(metadata, dict):
                errors.append(f"Metadata must be dict, got {type(metadata)}")
            else:
                # Check for non-string keys
                invalid_keys = [k for k in metadata.keys() if not isinstance(k, str)]
                if invalid_keys:
                    errors.append(f"Metadata keys must be strings: {invalid_keys}")
                
                # Check for nested dicts (warning)
                nested = any(isinstance(v, dict) for v in metadata.values())
                if nested:
                    warnings.append("Nested dictionaries in metadata may impact performance")
        
        return TypeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            converted_value=metadata if len(errors) == 0 else None
        )
    
    @staticmethod
    def validate_uuid(value: Any) -> TypeValidationResult:
        """Validate UUID value."""
        errors = []
        warnings = []
        converted = None
        
        try:
            if isinstance(value, uuid.UUID):
                converted = value
            elif isinstance(value, str):
                try:
                    converted = uuid.UUID(value)
                except ValueError:
                    errors.append(f"Invalid UUID format: {value}")
            else:
                errors.append(f"Expected UUID or string, got {type(value)}")
            
            return TypeValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                converted_value=converted
            )
            
        except Exception as e:
            return TypeValidationResult(
                valid=False,
                errors=[f"Validation failed: {str(e)}"],
                warnings=[],
                converted_value=None
            )
    
    @staticmethod
    def validate_email(value: str) -> TypeValidationResult:
        """Validate email address."""
        errors = []
        warnings = []
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            errors.append(f"Invalid email format: {value}")
        
        if len(value) > 254:  # RFC 5321
            warnings.append("Email length exceeds recommended maximum")
        
        return TypeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            converted_value=value.lower() if not errors else None
        )
    
    @staticmethod
    def validate_ip_address(value: str) -> TypeValidationResult:
        """Validate IP address."""
        errors = []
        warnings = []
        
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
        
        if not (re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value)):
            errors.append(f"Invalid IP address format: {value}")
        
        if re.match(ipv4_pattern, value):
            # Validate IPv4 octets
            octets = [int(o) for o in value.split('.')]
            if any(o > 255 for o in octets):
                errors.append("IPv4 octet exceeds 255")
        
        return TypeValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            converted_value=value if not errors else None
        )

class TypeConverter:
    """Converts between different type representations."""
    
    @staticmethod
    def to_datetime(value: Union[str, datetime, float, int]) -> datetime:
        """Convert value to datetime."""
        if isinstance(value, datetime):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                raise ValidationError(f"Invalid datetime string: {value}")
        elif isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except ValueError:
                raise ValidationError(f"Invalid timestamp: {value}")
        else:
            raise ValidationError(f"Cannot convert {type(value)} to datetime")
    
    @staticmethod
    def to_timedelta(value: Union[str, timedelta, int]) -> timedelta:
        """Convert value to timedelta."""
        if isinstance(value, timedelta):
            return value
        elif isinstance(value, str):
            # Parse string format like "1d", "2h", "30m", "45s"
            try:
                num = int(value[:-1])
                unit = value[-1].lower()
                if unit == 'd':
                    return timedelta(days=num)
                elif unit == 'h':
                    return timedelta(hours=num)
                elif unit == 'm':
                    return timedelta(minutes=num)
                elif unit == 's':
                    return timedelta(seconds=num)
                else:
                    raise ValidationError(f"Invalid time unit: {unit}")
            except (IndexError, ValueError):
                raise ValidationError(f"Invalid timedelta string: {value}")
        elif isinstance(value, int):
            return timedelta(seconds=value)
        else:
            raise ValidationError(f"Cannot convert {type(value)} to timedelta")
    
    @staticmethod
    def to_set(value: Union[str, List, Set, tuple]) -> Set:
        """Convert value to set."""
        if isinstance(value, set):
            return value
        elif isinstance(value, (list, tuple)):
            return set(value)
        elif isinstance(value, str):
            # Handle comma-separated string
            return {v.strip() for v in value.split(',')}
        else:
            raise ValidationError(f"Cannot convert {type(value)} to set")
    
    @staticmethod
    def to_decimal(value: Union[str, float, int, Decimal]) -> Decimal:
        """Convert value to Decimal."""
        if isinstance(value, Decimal):
            return value
        elif isinstance(value, (int, float)):
            return Decimal(str(value))
        elif isinstance(value, str):
            try:
                return Decimal(value)
            except:
                raise ValidationError(f"Invalid decimal string: {value}")
        else:
            raise ValidationError(f"Cannot convert {type(value)} to Decimal")
    
    @staticmethod
    def to_bool(value: Union[str, bool, int]) -> bool:
        """Convert value to boolean."""
        if isinstance(value, bool):
            return value
        elif isinstance(value, int):
            return bool(value)
        elif isinstance(value, str):
            value = value.lower()
            if value in ('true', '1', 'yes', 'on'):
                return True
            elif value in ('false', '0', 'no', 'off'):
                return False
            raise ValidationError(f"Invalid boolean string: {value}")
        else:
            raise ValidationError(f"Cannot convert {type(value)} to bool")
    
    @staticmethod
    def to_list(value: Union[str, List, Set, tuple], 
                item_type: Optional[Type] = None,
                separator: str = ',') -> List:
        """Convert value to list with optional type conversion."""
        if isinstance(value, list):
            items = value
        elif isinstance(value, (set, tuple)):
            items = list(value)
        elif isinstance(value, str):
            items = [item.strip() for item in value.split(separator)]
        else:
            raise ValidationError(f"Cannot convert {type(value)} to list")
        
        if item_type:
            try:
                items = [item_type(item) for item in items]
            except Exception as e:
                raise ValidationError(f"Failed to convert items to {item_type}: {str(e)}")
        
        return items

class TypeSerializer:
    """Serializes types to/from various formats."""
    
    @staticmethod
    def serialize_datetime(dt: datetime) -> str:
        """Serialize datetime to ISO format string."""
        return dt.isoformat()
    
    @staticmethod
    def deserialize_datetime(value: str) -> datetime:
        """Deserialize datetime from ISO format string."""
        return TypeConverter.to_datetime(value)
    
    @staticmethod
    def serialize_enum(enum_value: Enum) -> str:
        """Serialize enum to string."""
        return enum_value.value
    
    @staticmethod
    def deserialize_enum(value: str, enum_class: Type[Enum]) -> Enum:
        """Deserialize enum from string."""
        result = TypeValidator.validate_enum(value, enum_class)
        if not result.valid:
            raise ValidationError(result.errors[0])
        return result.converted_value
    
    @staticmethod
    def serialize_context(context: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize context to JSON-compatible dict."""
        result = {}
        for key, value in context.items():
            if isinstance(value, datetime):
                result[key] = TypeSerializer.serialize_datetime(value)
            elif isinstance(value, Enum):
                result[key] = TypeSerializer.serialize_enum(value)
            elif isinstance(value, (list, set)):
                result[key] = list(value)
            else:
                result[key] = value
        return result
    
    @staticmethod
    def deserialize_context(data: Dict[str, Any],
                          datetime_fields: Optional[Set[str]] = None,
                          enum_fields: Optional[Dict[str, Type[Enum]]] = None) -> Dict[str, Any]:
        """Deserialize context from JSON-compatible dict."""
        result = {}
        for key, value in data.items():
            if datetime_fields and key in datetime_fields:
                result[key] = TypeSerializer.deserialize_datetime(value)
            elif enum_fields and key in enum_fields:
                result[key] = TypeSerializer.deserialize_enum(value, enum_fields[key])
            else:
                result[key] = value
        return result
    
    @staticmethod
    def to_json(obj: Any, 
                pretty: bool = False,
                ensure_ascii: bool = False) -> str:
        """Serialize to JSON."""
        try:
            if pretty:
                return json.dumps(obj, indent=2, ensure_ascii=ensure_ascii)
            return json.dumps(obj, ensure_ascii=ensure_ascii)
        except Exception as e:
            raise ValidationError(f"JSON serialization failed: {str(e)}")
    
    @staticmethod
    def from_json(data: str) -> Any:
        """Deserialize from JSON."""
        try:
            return json.loads(data)
        except Exception as e:
            raise ValidationError(f"JSON deserialization failed: {str(e)}")
    
    @staticmethod
    def to_yaml(obj: Any) -> str:
        """Serialize to YAML."""
        try:
            return yaml.dump(obj, allow_unicode=True)
        except Exception as e:
            raise ValidationError(f"YAML serialization failed: {str(e)}")
    
    @staticmethod
    def from_yaml(data: str) -> Any:
        """Deserialize from YAML."""
        try:
            return yaml.safe_load(data)
        except Exception as e:
            raise ValidationError(f"YAML deserialization failed: {str(e)}")
    
    @staticmethod
    def to_msgpack(obj: Any) -> bytes:
        """Serialize to MessagePack."""
        try:
            return msgpack.packb(obj)
        except Exception as e:
            raise ValidationError(f"MessagePack serialization failed: {str(e)}")
    
    @staticmethod
    def from_msgpack(data: bytes) -> Any:
        """Deserialize from MessagePack."""
        try:
            return msgpack.unpackb(data)
        except Exception as e:
            raise ValidationError(f"MessagePack deserialization failed: {str(e)}")
    
    @staticmethod
    def to_xml(obj: Dict) -> str:
        """Serialize dictionary to XML."""
        try:
            def dict_to_xml(data: Dict, root: ET.Element) -> None:
                for key, value in data.items():
                    child = ET.SubElement(root, str(key))
                    if isinstance(value, dict):
                        dict_to_xml(value, child)
                    else:
                        child.text = str(value)
            
            root = ET.Element("root")
            dict_to_xml(obj, root)
            return ET.tostring(root, encoding='unicode')
            
        except Exception as e:
            raise ValidationError(f"XML serialization failed: {str(e)}")
    
    @staticmethod
    def from_xml(data: str) -> Dict:
        """Deserialize XML to dictionary."""
        try:
            def xml_to_dict(element: ET.Element) -> Dict:
                result = {}
                for child in element:
                    if len(child) > 0:
                        result[child.tag] = xml_to_dict(child)
                    else:
                        result[child.tag] = child.text or ''
                return result
            
            root = ET.fromstring(data)
            return xml_to_dict(root)
            
        except Exception as e:
            raise ValidationError(f"XML deserialization failed: {str(e)}")
    
    @staticmethod
    def to_base64(data: Union[str, bytes]) -> str:
        """Convert to base64 string."""
        try:
            if isinstance(data, str):
                data = data.encode()
            return base64.b64encode(data).decode()
        except Exception as e:
            raise ValidationError(f"Base64 encoding failed: {str(e)}")
    
    @staticmethod
    def from_base64(data: str) -> bytes:
        """Convert from base64 string."""
        try:
            return base64.b64decode(data)
        except Exception as e:
            raise ValidationError(f"Base64 decoding failed: {str(e)}")