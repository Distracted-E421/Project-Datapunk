from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass
from enum import Enum, auto
from .query_parser_core import QueryNode, QueryPlan
from .query_parser_nosql import NoSQLParser

class AggregationStage(Enum):
    """MongoDB-style aggregation pipeline stages."""
    MATCH = '$match'
    GROUP = '$group'
    SORT = '$sort'
    LIMIT = '$limit'
    SKIP = '$skip'
    PROJECT = '$project'
    UNWIND = '$unwind'
    LOOKUP = '$lookup'
    GRAPH_LOOKUP = '$graphLookup'
    GEO_NEAR = '$geoNear'
    TEXT = '$text'
    FACET = '$facet'

@dataclass
class GeoPoint:
    """Geographic point specification."""
    longitude: float
    latitude: float
    type: str = "Point"

@dataclass
class GeoShape:
    """Geographic shape specification."""
    coordinates: List[Any]
    type: str

class AdvancedNoSQLParser(NoSQLParser):
    """Enhanced NoSQL parser with support for advanced features."""
    
    def parse_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse an advanced NoSQL query."""
        # Check for aggregation pipeline
        if self._is_aggregation_pipeline(query):
            return self._parse_aggregation(query)
            
        # Check for graph traversal
        if self._is_graph_query(query):
            return self._parse_graph_query(query)
            
        # Check for geospatial query
        if self._is_geo_query(query):
            return self._parse_geo_query(query)
            
        # Check for text search
        if self._is_text_search(query):
            return self._parse_text_search(query)
            
        return super().parse_query(query)
        
    def _parse_aggregation(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse an aggregation pipeline."""
        pipeline = query['pipeline']
        current_node = None
        
        for stage in pipeline:
            stage_type = list(stage.keys())[0]
            stage_spec = stage[stage_type]
            
            # Create node for this stage
            node = self._create_aggregation_node(stage_type, stage_spec)
            
            if current_node:
                node.children = [current_node]
            current_node = node
            
        return QueryPlan(current_node)
        
    def _parse_graph_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse a graph traversal query."""
        start_node = query['start']
        traversal = query['traversal']
        
        # Create initial node lookup
        root = QueryNode(
            operation='graph_lookup',
            collection=start_node['collection'],
            conditions=start_node.get('conditions', {})
        )
        
        current_node = root
        for step in traversal:
            # Create node for each traversal step
            node = QueryNode(
                operation='graph_traverse',
                edge_collection=step['edge_collection'],
                direction=step.get('direction', 'outbound'),
                conditions=step.get('conditions', {}),
                depth=step.get('depth', 1)
            )
            
            current_node.children = [node]
            current_node = node
            
        return QueryPlan(root)
        
    def _parse_geo_query(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse a geospatial query."""
        geo_op = list(query['geometry'].keys())[0]
        geo_spec = query['geometry'][geo_op]
        
        if geo_op == '$near':
            return self._parse_geo_near(geo_spec)
        elif geo_op == '$within':
            return self._parse_geo_within(geo_spec)
        elif geo_op == '$intersects':
            return self._parse_geo_intersects(geo_spec)
            
        raise ValueError(f"Unsupported geo operation: {geo_op}")
        
    def _parse_text_search(self, query: Dict[str, Any]) -> QueryPlan:
        """Parse a text search query."""
        text_query = query['$text']
        
        root = QueryNode(
            operation='text_search',
            search_text=text_query['$search'],
            language=text_query.get('$language', 'english'),
            case_sensitive=text_query.get('$caseSensitive', False),
            diacritics_sensitive=text_query.get('$diacriticSensitive', False)
        )
        
        return QueryPlan(root)
        
    def _create_aggregation_node(self, stage_type: str, 
                               spec: Dict[str, Any]) -> QueryNode:
        """Create a node for an aggregation stage."""
        stage = AggregationStage(stage_type)
        
        if stage == AggregationStage.MATCH:
            return QueryNode(
                operation='filter',
                conditions=spec
            )
            
        elif stage == AggregationStage.GROUP:
            return QueryNode(
                operation='aggregate',
                group_by=spec['_id'],
                aggregates=self._parse_group_operators(spec)
            )
            
        elif stage == AggregationStage.SORT:
            return QueryNode(
                operation='sort',
                sort_keys=[(k, v) for k, v in spec.items()]
            )
            
        elif stage == AggregationStage.LIMIT:
            return QueryNode(
                operation='limit',
                limit=spec
            )
            
        elif stage == AggregationStage.SKIP:
            return QueryNode(
                operation='skip',
                skip=spec
            )
            
        elif stage == AggregationStage.PROJECT:
            return QueryNode(
                operation='project',
                projections=spec
            )
            
        elif stage == AggregationStage.UNWIND:
            return QueryNode(
                operation='unwind',
                array_path=spec['path'] if isinstance(spec, dict) else spec
            )
            
        elif stage == AggregationStage.LOOKUP:
            return QueryNode(
                operation='lookup',
                from_collection=spec['from'],
                local_field=spec['localField'],
                foreign_field=spec['foreignField'],
                as_field=spec['as']
            )
            
        elif stage == AggregationStage.GRAPH_LOOKUP:
            return QueryNode(
                operation='graph_lookup',
                from_collection=spec['from'],
                start_with=spec['startWith'],
                connect_from_field=spec['connectFromField'],
                connect_to_field=spec['connectToField'],
                as_field=spec['as'],
                max_depth=spec.get('maxDepth'),
                depth_field=spec.get('depthField')
            )
            
        elif stage == AggregationStage.GEO_NEAR:
            return QueryNode(
                operation='geo_near',
                near=self._parse_geo_point(spec['near']),
                distance_field=spec['distanceField'],
                max_distance=spec.get('maxDistance'),
                min_distance=spec.get('minDistance'),
                spherical=spec.get('spherical', False)
            )
            
        elif stage == AggregationStage.TEXT:
            return QueryNode(
                operation='text_search',
                search_text=spec['$search'],
                language=spec.get('$language', 'english'),
                case_sensitive=spec.get('$caseSensitive', False)
            )
            
        elif stage == AggregationStage.FACET:
            return QueryNode(
                operation='facet',
                facets={
                    name: self._parse_sub_pipeline(pipeline)
                    for name, pipeline in spec.items()
                }
            )
            
        raise ValueError(f"Unsupported aggregation stage: {stage_type}")
        
    def _parse_group_operators(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse group stage operators."""
        aggregates = []
        
        for field, operator in spec.items():
            if field == '_id':
                continue
                
            if isinstance(operator, dict):
                op_type = list(operator.keys())[0]
                op_field = operator[op_type]
                
                aggregates.append({
                    'function': op_type.lstrip('$'),
                    'field': op_field,
                    'alias': field
                })
                
        return aggregates
        
    def _parse_sub_pipeline(self, pipeline: List[Dict[str, Any]]) -> QueryNode:
        """Parse a sub-pipeline for faceted queries."""
        sub_query = {'pipeline': pipeline}
        return self._parse_aggregation(sub_query).root
        
    def _parse_geo_point(self, point_spec: Union[List[float], Dict[str, Any]]) -> GeoPoint:
        """Parse a geographic point specification."""
        if isinstance(point_spec, list):
            return GeoPoint(
                longitude=point_spec[0],
                latitude=point_spec[1]
            )
            
        if isinstance(point_spec, dict):
            coords = point_spec['coordinates']
            return GeoPoint(
                longitude=coords[0],
                latitude=coords[1],
                type=point_spec['type']
            )
            
        raise ValueError(f"Invalid point specification: {point_spec}")
        
    def _parse_geo_shape(self, shape_spec: Dict[str, Any]) -> GeoShape:
        """Parse a geographic shape specification."""
        return GeoShape(
            coordinates=shape_spec['coordinates'],
            type=shape_spec['type']
        )
        
    def _parse_geo_near(self, spec: Dict[str, Any]) -> QueryPlan:
        """Parse a $near query."""
        root = QueryNode(
            operation='geo_near',
            near=self._parse_geo_point(spec['$geometry']),
            max_distance=spec.get('$maxDistance'),
            min_distance=spec.get('$minDistance')
        )
        
        return QueryPlan(root)
        
    def _parse_geo_within(self, spec: Dict[str, Any]) -> QueryPlan:
        """Parse a $within query."""
        root = QueryNode(
            operation='geo_within',
            shape=self._parse_geo_shape(spec['$geometry'])
        )
        
        return QueryPlan(root)
        
    def _parse_geo_intersects(self, spec: Dict[str, Any]) -> QueryPlan:
        """Parse a $geoIntersects query."""
        root = QueryNode(
            operation='geo_intersects',
            shape=self._parse_geo_shape(spec['$geometry'])
        )
        
        return QueryPlan(root)
        
    def _is_aggregation_pipeline(self, query: Dict[str, Any]) -> bool:
        """Check if query is an aggregation pipeline."""
        return 'pipeline' in query
        
    def _is_graph_query(self, query: Dict[str, Any]) -> bool:
        """Check if query is a graph traversal."""
        return 'start' in query and 'traversal' in query
        
    def _is_geo_query(self, query: Dict[str, Any]) -> bool:
        """Check if query is a geospatial query."""
        return 'geometry' in query
        
    def _is_text_search(self, query: Dict[str, Any]) -> bool:
        """Check if query is a text search."""
        return '$text' in query 