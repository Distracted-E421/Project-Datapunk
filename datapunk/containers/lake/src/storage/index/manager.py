from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass

from .core import Index, IndexType, IndexStats, IndexMetadata
from .btree import BTreeIndex
from .hash import HashIndex
from .bitmap import BitmapIndex
from .advisor import IndexAdvisor
from .maintenance import IndexMaintenance
from .rtree import RTreeIndex
from .gist import GiSTIndex
from .strategies.trigram import create_trigram_index
from .strategies.regex import create_regex_index
from .partial import Condition, create_partial_index

@dataclass
class IndexCreationRequest:
    """Request to create a new index."""
    name: str
    table_name: str
    columns: List[str]
    index_type: IndexType
    is_unique: bool = False
    is_primary: bool = False
    properties: Dict[str, Any] = None

class IndexManager:
    """Manages index lifecycle and operations."""
    
    def __init__(
        self,
        max_workers: int = 4,
        enable_auto_maintenance: bool = True,
        enable_advisor: bool = True
    ):
        self.indexes: Dict[str, Index] = {}
        self.advisor = IndexAdvisor() if enable_advisor else None
        self.maintenance = IndexMaintenance() if enable_auto_maintenance else None
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Register index implementations
        self._index_implementations = {
            IndexType.BTREE: BTreeIndex,
            IndexType.HASH: HashIndex,
            IndexType.BITMAP: BitmapIndex,
            IndexType.RTREE: RTreeIndex,
            IndexType.GIST: GiSTIndex
        }
        
        # Register specialized index creators
        self._specialized_creators = {
            "trigram": create_trigram_index,
            "regex": create_regex_index
        }
        
        if enable_auto_maintenance:
            self._start_maintenance_thread()

    def create_index(self, request: IndexCreationRequest) -> Index:
        """Creates a new index based on the request."""
        with self.lock:
            if request.name in self.indexes:
                raise ValueError(f"Index {request.name} already exists")
                
            index_class = self._index_implementations.get(request.index_type)
            if not index_class:
                raise ValueError(f"Unsupported index type: {request.index_type}")
            
            # Create the index
            index = index_class(
                name=request.name,
                table_name=request.table_name,
                columns=request.columns,
                is_unique=request.is_unique,
                is_primary=request.is_primary,
                properties=request.properties or {}
            )
            
            self.indexes[request.name] = index
            self.logger.info(f"Created index {request.name} of type {request.index_type}")
            
            # Schedule initial statistics collection
            self.executor.submit(self._collect_stats, index)
            
            return index

    def drop_index(self, name: str) -> bool:
        """Drops an existing index."""
        with self.lock:
            if name not in self.indexes:
                return False
            
            index = self.indexes[name]
            try:
                # Cleanup index resources
                index.cleanup()
                del self.indexes[name]
                self.logger.info(f"Dropped index {name}")
                return True
            except Exception as e:
                self.logger.error(f"Error dropping index {name}: {e}")
                raise

    def get_index(self, name: str) -> Optional[Index]:
        """Retrieves an index by name."""
        return self.indexes.get(name)

    def list_indexes(self, table_name: Optional[str] = None) -> List[IndexMetadata]:
        """Lists all indexes or indexes for a specific table."""
        indexes = self.indexes.values()
        if table_name:
            indexes = [idx for idx in indexes if idx.table_name == table_name]
        return [idx.get_metadata() for idx in indexes]

    def rebuild_index(self, name: str) -> bool:
        """Rebuilds an existing index."""
        with self.lock:
            index = self.indexes.get(name)
            if not index:
                return False
            
            try:
                index.rebuild()
                self.logger.info(f"Rebuilt index {name}")
                return True
            except Exception as e:
                self.logger.error(f"Error rebuilding index {name}: {e}")
                raise

    def analyze_index_usage(self, table_name: str) -> Dict[str, Any]:
        """Analyzes index usage for a table."""
        if not self.advisor:
            raise RuntimeError("Index advisor is not enabled")
            
        table_indexes = [
            idx for idx in self.indexes.values()
            if idx.table_name == table_name
        ]
        
        return self.advisor.analyze_indexes(table_indexes)

    def get_index_statistics(self, name: str) -> Optional[IndexStats]:
        """Gets statistics for an index."""
        index = self.indexes.get(name)
        return index.get_statistics() if index else None

    def optimize_indexes(self, table_name: str) -> List[str]:
        """Optimizes indexes for a table based on usage patterns."""
        if not self.advisor:
            raise RuntimeError("Index advisor is not enabled")
            
        recommendations = self.advisor.get_recommendations(table_name)
        applied_changes = []
        
        for rec in recommendations:
            try:
                if rec["action"] == "create":
                    self.create_index(IndexCreationRequest(**rec["params"]))
                    applied_changes.append(f"Created index {rec['params']['name']}")
                elif rec["action"] == "drop":
                    self.drop_index(rec["index_name"])
                    applied_changes.append(f"Dropped index {rec['index_name']}")
                elif rec["action"] == "rebuild":
                    self.rebuild_index(rec["index_name"])
                    applied_changes.append(f"Rebuilt index {rec['index_name']}")
            except Exception as e:
                self.logger.error(f"Error applying recommendation: {e}")
                
        return applied_changes

    def _start_maintenance_thread(self):
        """Starts the background maintenance thread."""
        if not self.maintenance:
            return
            
        def maintenance_worker():
            while True:
                try:
                    # Get indexes that need maintenance
                    for index in self.indexes.values():
                        if self.maintenance.needs_maintenance(index):
                            self.executor.submit(self.maintenance.perform_maintenance, index)
                except Exception as e:
                    self.logger.error(f"Error in maintenance worker: {e}")
                finally:
                    # Sleep for maintenance interval
                    threading.Event().wait(300)  # 5 minutes
        
        maintenance_thread = threading.Thread(
            target=maintenance_worker,
            name="IndexMaintenance",
            daemon=True
        )
        maintenance_thread.start()

    def _collect_stats(self, index: Index):
        """Collects statistics for an index."""
        try:
            stats = index.get_statistics()
            if self.advisor:
                self.advisor.update_stats(index.name, stats)
        except Exception as e:
            self.logger.error(f"Error collecting stats for index {index.name}: {e}")

    def cleanup(self):
        """Cleans up resources used by the index manager."""
        self.executor.shutdown(wait=True)
        for index in self.indexes.values():
            try:
                index.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up index {index.name}: {e}")
        self.indexes.clear()

    def create_specialized_index(
        self,
        index_type: str,
        name: str,
        table_name: str,
        column: str,
        **kwargs
    ) -> Index:
        """Creates a specialized index type (e.g., trigram index)."""
        creator = self._specialized_creators.get(index_type)
        if not creator:
            raise ValueError(f"Unsupported specialized index type: {index_type}")
            
        index = creator(name=name, table_name=table_name, column=column, **kwargs)
        self.indexes[name] = index
        
        # Schedule initial statistics collection
        self.executor.submit(self._collect_stats, index)
        
        return index

    def create_partial_index(
        self,
        name: str,
        table_name: str,
        columns: List[str],
        condition: Condition,
        base_index_type: IndexType = IndexType.BTREE,
        **kwargs
    ) -> PartialIndex:
        """Create a new partial index."""
        if name in self.indexes:
            raise ValueError(f"Index {name} already exists")
            
        index = create_partial_index(
            name=name,
            table_name=table_name,
            columns=columns,
            condition=condition,
            base_index_type=base_index_type,
            **kwargs
        )
        
        self.indexes[name] = index
        return index
        
    def get_partial_metadata(self, name: str) -> PartialIndexMetadata:
        """Get metadata for a partial index."""
        index = self.indexes.get(name)
        if not index:
            raise ValueError(f"Index {name} does not exist")
            
        if not isinstance(index, PartialIndex):
            raise ValueError(f"Index {name} is not a partial index")
            
        return index.get_partial_metadata()
        
    def analyze_partial_indexes(self) -> Dict[str, PartialIndexMetadata]:
        """Analyze all partial indexes and return their metadata."""
        results = {}
        for name, index in self.indexes.items():
            if isinstance(index, PartialIndex):
                results[name] = index.get_partial_metadata()
        return results
  