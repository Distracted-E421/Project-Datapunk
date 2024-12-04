from typing import Any, Dict, List, Optional, Union, Callable
import re
import json
import numpy as np
from datetime import datetime, timezone
import structlog
from ..validation import ValidationRule, ValidationLevel
from ..exceptions import TransformationError

logger = structlog.get_logger()

"""
Data Transformation Utilities for Datapunk

A comprehensive collection of data transformation utilities designed to handle
various data cleaning, normalization, and standardization tasks. Provides
consistent data handling across the platform.

Key Features:
- String cleaning and normalization
- Datetime standardization
- Numeric value handling
- Boolean normalization
- JSON data processing
- Array handling

Design Philosophy:
- Consistent data handling
- Flexible configuration
- Robust error handling
- Clear validation rules

NOTE: All transformers are async for consistency with ETL pipeline
TODO: Add support for custom transformation rules
"""

class DataTransformer:
    """
    Collection of data transformation utilities.
    
    Key Capabilities:
    - String normalization
    - Date/time standardization
    - Numeric value processing
    - Boolean value handling
    - JSON data management
    - Array processing
    
    FIXME: Consider adding caching for expensive transformations
    """
    
    @staticmethod
    async def clean_string(value: str, **kwargs) -> str:
        """
        Cleans and normalizes string values with configurable options.
        
        Design Considerations:
        - Handles empty/null values gracefully
        - Supports multiple cleaning options
        - Maintains string integrity
        
        WARNING: May modify string length/content
        """
        if not value:
            return value
            
        # Apply base transformations
        value = value.strip()
        
        # Apply optional transformations based on configuration
        if kwargs.get("lowercase", False):
            value = value.lower()
        if kwargs.get("uppercase", False):
            value = value.upper()
        if kwargs.get("remove_whitespace", False):
            value = re.sub(r'\s+', '', value)
        if kwargs.get("normalize_spaces", False):
            value = re.sub(r'\s+', ' ', value)
            
        return value
    
    @staticmethod
    async def normalize_datetime(
        value: Union[str, datetime],
        input_format: Optional[str] = None,
        output_format: Optional[str] = None,
        timezone_name: Optional[str] = None
    ) -> str:
        """
        Normalizes datetime values to consistent format.
        
        Implementation Notes:
        - Handles multiple input formats
        - Supports timezone conversion
        - Provides flexible output formatting
        
        TODO: Add support for custom format detection
        """
        try:
            # Convert string to datetime if needed
            if isinstance(value, str):
                if input_format:
                    dt = datetime.strptime(value, input_format)
                else:
                    # Try common formats for flexibility
                    formats = [
                        "%Y-%m-%dT%H:%M:%S.%fZ",
                        "%Y-%m-%dT%H:%M:%SZ",
                        "%Y-%m-%d %H:%M:%S",
                        "%Y-%m-%d"
                    ]
                    for fmt in formats:
                        try:
                            dt = datetime.strptime(value, fmt)
                            break
                        except ValueError:
                            continue
                    else:
                        raise ValueError(f"Could not parse datetime: {value}")
            else:
                dt = value
            
            # Handle timezone conversion if specified
            if timezone_name:
                import pytz
                timezone = pytz.timezone(timezone_name)
                dt = dt.astimezone(timezone)
            
            # Format output as requested
            if output_format:
                return dt.strftime(output_format)
            return dt.isoformat()
            
        except Exception as e:
            logger.error("datetime_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize datetime: {str(e)}")
    
    @staticmethod
    async def normalize_numeric(
        value: Union[str, int, float],
        data_type: str = "float",
        precision: Optional[int] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Union[int, float]:
        """
        Normalizes numeric values with validation.
        
        Design Considerations:
        - Handles string-to-number conversion
        - Supports precision control
        - Validates value ranges
        - Maintains numeric type integrity
        
        WARNING: May raise error for invalid ranges
        """
        try:
            # Convert strings to numbers
            if isinstance(value, str):
                value = value.strip().replace(',', '')
                value = float(value)
            
            # Convert to specified type
            if data_type == "int":
                value = int(round(float(value)))
            else:
                value = float(value)
            
            # Apply precision if specified
            if precision is not None:
                value = round(value, precision)
            
            # Validate range if specified
            if min_value is not None and value < min_value:
                raise ValueError(f"Value {value} below minimum {min_value}")
            if max_value is not None and value > max_value:
                raise ValueError(f"Value {value} above maximum {max_value}")
            
            return value
            
        except Exception as e:
            logger.error("numeric_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize numeric value: {str(e)}")
    
    @staticmethod
    async def normalize_boolean(
        value: Any,
        true_values: Optional[List[Any]] = None,
        false_values: Optional[List[Any]] = None
    ) -> bool:
        """Normalize boolean values."""
        if true_values is None:
            true_values = [True, 1, '1', 'true', 'yes', 'y', 'on']
        if false_values is None:
            false_values = [False, 0, '0', 'false', 'no', 'n', 'off']
            
        # Convert to lowercase if string
        if isinstance(value, str):
            value = value.lower().strip()
        
        if value in true_values:
            return True
        if value in false_values:
            return False
            
        raise TransformationError(f"Could not convert value to boolean: {value}")
    
    @staticmethod
    async def normalize_json(
        value: Union[str, Dict, List],
        schema: Optional[Dict] = None
    ) -> Dict:
        """Normalize JSON data."""
        try:
            # Parse if string
            if isinstance(value, str):
                value = json.loads(value)
            
            # Validate against schema if provided
            if schema:
                from jsonschema import validate
                validate(instance=value, schema=schema)
            
            return value
            
        except Exception as e:
            logger.error("json_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize JSON: {str(e)}")
    
    @staticmethod
    async def normalize_array(
        value: Union[str, List],
        item_type: Optional[str] = None,
        separator: str = ",",
        unique: bool = False,
        sort: bool = False
    ) -> List:
        """Normalize array values."""
        try:
            # Convert to list if string
            if isinstance(value, str):
                value = [v.strip() for v in value.split(separator)]
            
            # Convert item types if specified
            if item_type:
                type_map = {
                    "int": int,
                    "float": float,
                    "str": str,
                    "bool": lambda x: DataTransformer.normalize_boolean(x)
                }
                converter = type_map.get(item_type)
                if converter:
                    value = [converter(item) for item in value]
            
            # Make unique if requested
            if unique:
                value = list(dict.fromkeys(value))
            
            # Sort if requested
            if sort:
                value.sort()
            
            return value
            
        except Exception as e:
            logger.error("array_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize array: {str(e)}")
    
    @staticmethod
    async def apply_transformations(
        data: Dict,
        transformations: Dict[str, List[Dict]]
    ) -> Dict:
        """Apply multiple transformations to data fields."""
        result = data.copy()
        
        for field, transforms in transformations.items():
            if field not in data:
                continue
                
            value = data[field]
            for transform in transforms:
                func_name = transform.get("type")
                params = transform.get("params", {})
                
                # Get transformation function
                func = getattr(DataTransformer, f"normalize_{func_name}", None)
                if not func:
                    logger.warning("unknown_transformation",
                                 transform=func_name)
                    continue
                
                try:
                    value = await func(value, **params)
                except Exception as e:
                    logger.error("transformation_failed",
                                field=field,
                                transform=func_name,
                                error=str(e))
                    raise TransformationError(
                        f"Failed to apply transformation {func_name} to field {field}: {str(e)}"
                    )
                
            result[field] = value
        
        return result 

    @staticmethod
    async def normalize_address(
        value: Dict[str, str],
        country_code: Optional[str] = None,
        format_type: str = "standard"
    ) -> Dict[str, str]:
        """Normalize address data."""
        try:
            # Basic validation
            required_fields = ["street", "city", "postal_code"]
            if not all(field in value for field in required_fields):
                raise ValueError("Missing required address fields")
            
            result = {}
            
            # Normalize street address
            street = value["street"].strip()
            street = re.sub(r'\s+', ' ', street)  # Normalize spaces
            result["street"] = street.title()
            
            # Normalize city
            result["city"] = value["city"].strip().title()
            
            # Normalize postal code based on country
            postal_code = value["postal_code"].strip().upper()
            if country_code:
                # Add country-specific postal code validation
                if country_code == "US":
                    if not re.match(r'^\d{5}(-\d{4})?$', postal_code):
                        raise ValueError("Invalid US postal code")
                elif country_code == "UK":
                    if not re.match(r'^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$', postal_code):
                        raise ValueError("Invalid UK postal code")
            result["postal_code"] = postal_code
            
            # Add optional fields
            if "state" in value:
                result["state"] = value["state"].strip().upper()
            if "country" in value:
                result["country"] = value["country"].strip().upper()
            
            return result
            
        except Exception as e:
            logger.error("address_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize address: {str(e)}")

    @staticmethod
    async def normalize_phone(
        value: str,
        country_code: Optional[str] = None,
        format_type: str = "e164"
    ) -> str:
        """Normalize phone numbers."""
        try:
            # Remove all non-numeric characters
            numbers_only = re.sub(r'\D', '', value)
            
            if not numbers_only:
                raise ValueError("No numeric characters in phone number")
            
            # Handle country code
            if country_code:
                if not numbers_only.startswith(country_code):
                    numbers_only = f"{country_code}{numbers_only}"
            
            # Format based on type
            if format_type == "e164":
                return f"+{numbers_only}"
            elif format_type == "national":
                # Example for US numbers
                if numbers_only.startswith("1") and len(numbers_only) == 11:
                    area = numbers_only[1:4]
                    prefix = numbers_only[4:7]
                    line = numbers_only[7:]
                    return f"({area}) {prefix}-{line}"
            
            return numbers_only
            
        except Exception as e:
            logger.error("phone_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize phone: {str(e)}")

    @staticmethod
    async def normalize_email(
        value: str,
        lowercase: bool = True,
        validate: bool = True
    ) -> str:
        """Normalize email addresses."""
        try:
            # Basic cleaning
            email = value.strip()
            if lowercase:
                email = email.lower()
            
            # Validation
            if validate:
                # Basic email validation
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    raise ValueError("Invalid email format")
                
                # Additional checks
                if len(email) > 254:  # RFC 5321
                    raise ValueError("Email too long")
                
                local_part, domain = email.split('@')
                if len(local_part) > 64:  # RFC 5321
                    raise ValueError("Local part too long")
                
                if domain.endswith('.'):
                    email = email[:-1]
            
            return email
            
        except Exception as e:
            logger.error("email_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize email: {str(e)}")

    @staticmethod
    async def normalize_currency(
        value: Union[str, float, int],
        source_currency: str,
        target_currency: str = "USD",
        exchange_rates: Optional[Dict[str, float]] = None
    ) -> float:
        """Normalize currency values."""
        try:
            # Convert string to number if needed
            if isinstance(value, str):
                # Remove currency symbols and separators
                cleaned = re.sub(r'[^\d.-]', '', value)
                amount = float(cleaned)
            else:
                amount = float(value)
            
            # Perform currency conversion if needed
            if source_currency != target_currency:
                if not exchange_rates:
                    raise ValueError("Exchange rates required for currency conversion")
                
                rate = exchange_rates.get(f"{source_currency}_{target_currency}")
                if not rate:
                    raise ValueError(f"No exchange rate found for {source_currency} to {target_currency}")
                
                amount *= rate
            
            # Round to 2 decimal places
            return round(amount, 2)
            
        except Exception as e:
            logger.error("currency_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize currency: {str(e)}")

    @staticmethod
    async def normalize_name(
        value: str,
        format_type: str = "full",
        title_case: bool = True
    ) -> Union[str, Dict[str, str]]:
        """Normalize person names."""
        try:
            # Basic cleaning
            name = value.strip()
            name = re.sub(r'\s+', ' ', name)
            
            if format_type == "full":
                if title_case:
                    return name.title()
                return name
            
            # Split into parts
            parts = name.split()
            result = {}
            
            if format_type == "parts":
                if len(parts) == 1:
                    result["first_name"] = parts[0]
                elif len(parts) == 2:
                    result["first_name"] = parts[0]
                    result["last_name"] = parts[1]
                else:
                    result["first_name"] = parts[0]
                    result["middle_name"] = " ".join(parts[1:-1])
                    result["last_name"] = parts[-1]
                
                if title_case:
                    result = {k: v.title() for k, v in result.items()}
                
                return result
            
            raise ValueError(f"Unknown format type: {format_type}")
            
        except Exception as e:
            logger.error("name_normalization_failed",
                        value=str(value),
                        error=str(e))
            raise TransformationError(f"Failed to normalize name: {str(e)}")