from typing import Dict, List, Set, Any, Optional
import json
from .query_validation_core import (
    ValidationRule,
    ValidationResult,
    ValidationLevel,
    ValidationCategory,
    TableExistsRule,
    ColumnExistsRule,
    TypeCompatibilityRule,
    ResourceLimitRule,
    SecurityRule
)

class NoSQLCollectionExistsRule(TableExistsRule):
    """NoSQL-specific collection existence validation."""
    
    def _extract_tables(self, query: Dict[str, Any]) -> Set[str]:
        """Extract collection names from NoSQL query."""
        try:
            collections = set()
            
            # Extract from collection field
            if 'collection' in query:
                collections.add(query['collection'])
            
            # Extract from aggregation pipeline
            if 'pipeline' in query:
                for stage in query['pipeline']:
                    if '$lookup' in stage:
                        collections.add(stage['$lookup']['from'])
                    elif '$merge' in stage:
                        collections.add(stage['$merge']['into'])
                    elif '$out' in stage:
                        collections.add(stage['$out'])
            
            return collections
        except Exception as e:
            self.logger.error(f"Error extracting collections: {e}")
            return set()

class NoSQLFieldExistsRule(ColumnExistsRule):
    """NoSQL-specific field existence validation."""
    
    def _extract_columns(self, query: Dict[str, Any]) -> Dict[str, Set[str]]:
        """Extract field references by collection."""
        try:
            fields = {}
            collection = query.get('collection', '')
            
            if collection:
                fields[collection] = set()
                
                # Extract from projection
                if 'projection' in query:
                    fields[collection].update(
                        self._extract_fields_from_projection(
                            query['projection']
                        )
                    )
                
                # Extract from filter
                if 'filter' in query:
                    fields[collection].update(
                        self._extract_fields_from_filter(
                            query['filter']
                        )
                    )
                
                # Extract from sort
                if 'sort' in query:
                    fields[collection].update(
                        self._extract_fields_from_sort(
                            query['sort']
                        )
                    )
                
                # Extract from update
                if 'update' in query:
                    fields[collection].update(
                        self._extract_fields_from_update(
                            query['update']
                        )
                    )
            
            return fields
        except Exception as e:
            self.logger.error(f"Error extracting fields: {e}")
            return {}
    
    def _extract_fields_from_projection(self,
                                      projection: Dict[str, Any]) -> Set[str]:
        """Extract fields from projection."""
        fields = set()
        for field in projection:
            if not field.startswith('$'):
                fields.add(field.split('.')[0])
        return fields
    
    def _extract_fields_from_filter(self,
                                  filter_doc: Dict[str, Any]) -> Set[str]:
        """Extract fields from filter."""
        fields = set()
        
        def extract_fields(doc):
            for key, value in doc.items():
                if not key.startswith('$'):
                    fields.add(key.split('.')[0])
                elif isinstance(value, dict):
                    extract_fields(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            extract_fields(item)
        
        extract_fields(filter_doc)
        return fields
    
    def _extract_fields_from_sort(self,
                                sort_doc: Dict[str, Any]) -> Set[str]:
        """Extract fields from sort."""
        return {field.split('.')[0] for field in sort_doc.keys()}
    
    def _extract_fields_from_update(self,
                                  update_doc: Dict[str, Any]) -> Set[str]:
        """Extract fields from update."""
        fields = set()
        
        for operator, value in update_doc.items():
            if operator.startswith('$'):
                if isinstance(value, dict):
                    fields.update(
                        field.split('.')[0]
                        for field in value.keys()
                    )
        
        return fields

class NoSQLTypeCompatibilityRule(TypeCompatibilityRule):
    """NoSQL-specific type compatibility validation."""
    
    def _extract_operations(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from NoSQL query."""
        try:
            operations = []
            
            # Extract from filter operations
            if 'filter' in query:
                operations.extend(
                    self._extract_filter_operations(query['filter'])
                )
            
            # Extract from update operations
            if 'update' in query:
                operations.extend(
                    self._extract_update_operations(query['update'])
                )
            
            # Extract from pipeline operations
            if 'pipeline' in query:
                operations.extend(
                    self._extract_pipeline_operations(query['pipeline'])
                )
            
            return operations
        except Exception as e:
            self.logger.error(f"Error extracting operations: {e}")
            return []
    
    def _extract_filter_operations(self,
                                 filter_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from filter document."""
        operations = []
        
        def extract_ops(doc, path=''):
            for key, value in doc.items():
                if key.startswith('$'):
                    if key in ['$eq', '$gt', '$lt', '$gte', '$lte', '$ne']:
                        operations.append({
                            'type': 'comparison',
                            'operator': key,
                            'field': path,
                            'value': value
                        })
                    elif key in ['$in', '$nin']:
                        operations.append({
                            'type': 'array_comparison',
                            'operator': key,
                            'field': path,
                            'values': value
                        })
                elif isinstance(value, dict):
                    extract_ops(value, key)
        
        extract_ops(filter_doc)
        return operations
    
    def _extract_update_operations(self,
                                 update_doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from update document."""
        operations = []
        
        for operator, value in update_doc.items():
            if operator.startswith('$'):
                if isinstance(value, dict):
                    for field, field_value in value.items():
                        operations.append({
                            'type': 'update',
                            'operator': operator,
                            'field': field,
                            'value': field_value
                        })
        
        return operations
    
    def _extract_pipeline_operations(self,
                                   pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract operations from aggregation pipeline."""
        operations = []
        
        for stage in pipeline:
            for operator, value in stage.items():
                if operator in ['$project', '$group']:
                    operations.extend(
                        self._extract_expression_operations(value)
                    )
        
        return operations
    
    def _extract_expression_operations(self,
                                    expr: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract operations from expressions."""
        operations = []
        
        for field, value in expr.items():
            if isinstance(value, dict):
                for op, op_value in value.items():
                    if op.startswith('$'):
                        operations.append({
                            'type': 'expression',
                            'operator': op,
                            'field': field,
                            'value': op_value
                        })
        
        return operations
    
    def _check_compatibility(self,
                           operation: Dict[str, Any],
                           schema: Dict[str, Any]) -> bool:
        """Check type compatibility of NoSQL operation."""
        try:
            if operation['type'] == 'comparison':
                return self._check_comparison_compatibility(
                    operation,
                    schema
                )
            elif operation['type'] == 'array_comparison':
                return self._check_array_compatibility(
                    operation,
                    schema
                )
            elif operation['type'] == 'update':
                return self._check_update_compatibility(
                    operation,
                    schema
                )
            elif operation['type'] == 'expression':
                return self._check_expression_compatibility(
                    operation,
                    schema
                )
            return True
        except Exception as e:
            self.logger.error(f"Error checking compatibility: {e}")
            return False
    
    def _check_comparison_compatibility(self,
                                      operation: Dict[str, Any],
                                      schema: Dict[str, Any]) -> bool:
        """Check comparison operation compatibility."""
        field_type = self._get_field_type(operation['field'], schema)
        value_type = self._get_value_type(operation['value'])
        
        return self._are_types_compatible(field_type, value_type)
    
    def _check_array_compatibility(self,
                                 operation: Dict[str, Any],
                                 schema: Dict[str, Any]) -> bool:
        """Check array operation compatibility."""
        field_type = self._get_field_type(operation['field'], schema)
        if not field_type.startswith('array'):
            return False
        
        element_type = field_type.split('<')[1].rstrip('>')
        for value in operation['values']:
            value_type = self._get_value_type(value)
            if not self._are_types_compatible(element_type, value_type):
                return False
        
        return True
    
    def _check_update_compatibility(self,
                                  operation: Dict[str, Any],
                                  schema: Dict[str, Any]) -> bool:
        """Check update operation compatibility."""
        field_type = self._get_field_type(operation['field'], schema)
        value_type = self._get_value_type(operation['value'])
        
        if operation['operator'] in ['$inc', '$mul']:
            return field_type in ['number', 'integer', 'float']
        elif operation['operator'] in ['$min', '$max']:
            return self._are_types_compatible(field_type, value_type)
        elif operation['operator'] in ['$push', '$addToSet']:
            return field_type.startswith('array')
        
        return self._are_types_compatible(field_type, value_type)
    
    def _check_expression_compatibility(self,
                                      operation: Dict[str, Any],
                                      schema: Dict[str, Any]) -> bool:
        """Check expression operation compatibility."""
        if operation['operator'] in ['$sum', '$avg', '$multiply', '$divide']:
            return all(
                self._get_value_type(v) in ['number', 'integer', 'float']
                for v in operation['value']
            )
        elif operation['operator'] in ['$concat', '$substr']:
            return all(
                self._get_value_type(v) == 'string'
                for v in operation['value']
            )
        
        return True
    
    def _get_field_type(self,
                       field: str,
                       schema: Dict[str, Any]) -> str:
        """Get field type from schema."""
        parts = field.split('.')
        current = schema
        
        for part in parts:
            if part not in current:
                return 'unknown'
            current = current[part]
        
        return current.get('type', 'unknown')
    
    def _get_value_type(self, value: Any) -> str:
        """Get type of value."""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            return 'string'
        elif isinstance(value, list):
            return f"array<{self._get_value_type(value[0]) if value else 'any'}>"
        elif isinstance(value, dict):
            return 'object'
        elif value is None:
            return 'null'
        return 'unknown'
    
    def _are_types_compatible(self,
                            type1: str,
                            type2: str) -> bool:
        """Check if types are compatible."""
        if type1 == type2:
            return True
        elif type1 in ['number', 'integer', 'float'] and type2 in ['number', 'integer', 'float']:
            return True
        elif type1.startswith('array') and type2.startswith('array'):
            return self._are_types_compatible(
                type1.split('<')[1].rstrip('>'),
                type2.split('<')[1].rstrip('>')
            )
        return False

class NoSQLResourceLimitRule(ResourceLimitRule):
    """NoSQL-specific resource limit validation."""
    
    def _analyze_query(self, query: Dict[str, Any]) -> Dict[str, int]:
        """Analyze NoSQL query for resource metrics."""
        try:
            metrics = {
                'tables': 0,
                'joins': 0,
                'subqueries': 0
            }
            
            # Count collections
            if 'collection' in query:
                metrics['tables'] += 1
            
            # Count pipeline stages
            if 'pipeline' in query:
                for stage in query['pipeline']:
                    # Count lookups as joins
                    if '$lookup' in stage:
                        metrics['joins'] += 1
                        metrics['tables'] += 1
                    
                    # Count subpipelines as subqueries
                    if any(key.endswith('Pipeline') for key in stage.keys()):
                        metrics['subqueries'] += 1
            
            return metrics
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return {'tables': 0, 'joins': 0, 'subqueries': 0}

class NoSQLSecurityRule(SecurityRule):
    """NoSQL-specific security validation."""
    
    def _extract_required_permissions(self, query: Dict[str, Any]) -> Set[str]:
        """Extract required permissions from NoSQL query."""
        try:
            permissions = set()
            
            # Basic operation permissions
            if 'filter' in query:
                permissions.add('FIND')
            if 'update' in query:
                permissions.add('UPDATE')
            if 'delete' in query:
                permissions.add('DELETE')
            if 'insert' in query:
                permissions.add('INSERT')
            
            # Aggregation permissions
            if 'pipeline' in query:
                permissions.add('AGGREGATE')
                
                for stage in query['pipeline']:
                    if '$lookup' in stage:
                        permissions.add('LOOKUP')
                    if '$merge' in stage:
                        permissions.add('MERGE')
                    if '$out' in stage:
                        permissions.add('OUT')
            
            return permissions
        except Exception as e:
            self.logger.error(f"Error extracting permissions: {e}")
            return set() 