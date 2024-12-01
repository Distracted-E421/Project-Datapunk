from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import json
import os
import sqlite3
from pathlib import Path
import threading
from contextlib import contextmanager

@dataclass
class IndexUsageStats:
    """Statistics about index usage."""
    total_reads: int = 0
    total_writes: int = 0
    avg_read_time_ms: float = 0.0
    avg_write_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_used: Optional[datetime] = None
    
@dataclass
class IndexSizeStats:
    """Statistics about index size."""
    total_entries: int = 0
    depth: int = 0
    size_bytes: int = 0
    fragmentation_ratio: float = 0.0
    last_compacted: Optional[datetime] = None
    
@dataclass
class IndexConditionStats:
    """Statistics about index conditions."""
    condition_string: str
    selectivity: float = 1.0
    false_positive_rate: float = 0.0
    evaluation_time_ms: float = 0.0
    last_optimized: Optional[datetime] = None

@dataclass
class IndexMaintenanceStats:
    """Statistics about index maintenance."""
    last_reindex: Optional[datetime] = None
    last_analyze: Optional[datetime] = None
    last_vacuum: Optional[datetime] = None
    rebuild_count: int = 0
    error_count: int = 0

@dataclass
class IndexStats:
    """Complete index statistics."""
    index_name: str
    table_name: str
    index_type: str
    created_at: datetime
    usage: IndexUsageStats
    size: IndexSizeStats
    condition: Optional[IndexConditionStats] = None
    maintenance: IndexMaintenanceStats = IndexMaintenanceStats()

class StatisticsStore:
    """Persistent storage for index statistics."""
    
    def __init__(self, db_path: str = "index_stats.db"):
        self.db_path = db_path
        self._local = threading.local()
        self._ensure_db()
        
    @contextmanager
    def _get_connection(self):
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection"):
            self._local.connection = sqlite3.connect(self.db_path)
            self._local.connection.row_factory = sqlite3.Row
            
        try:
            yield self._local.connection
        except Exception as e:
            self._local.connection.rollback()
            raise e
            
    def _ensure_db(self):
        """Ensure database and tables exist."""
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS index_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    index_type TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    stats_json TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS index_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    index_name TEXT NOT NULL,
                    snapshot_type TEXT NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_stats_index_name 
                ON index_stats(index_name);
                
                CREATE INDEX IF NOT EXISTS idx_stats_timestamp 
                ON index_stats(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_snapshots_index_name 
                ON index_snapshots(index_name);
            """)
            
    def save_stats(self, stats: IndexStats):
        """Save current index statistics."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO index_stats (
                    index_name, table_name, index_type, created_at, stats_json
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    stats.index_name,
                    stats.table_name,
                    stats.index_type,
                    stats.created_at.isoformat(),
                    json.dumps(asdict(stats))
                )
            )
            conn.commit()
            
    def save_snapshot(
        self,
        index_name: str,
        snapshot_type: str,
        data: Dict[str, Any]
    ):
        """Save a point-in-time snapshot of specific metrics."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO index_snapshots (
                    index_name, snapshot_type, snapshot_data
                ) VALUES (?, ?, ?)
                """,
                (index_name, snapshot_type, json.dumps(data))
            )
            conn.commit()
            
    def get_latest_stats(self, index_name: str) -> Optional[IndexStats]:
        """Get the most recent statistics for an index."""
        with self._get_connection() as conn:
            row = conn.execute(
                """
                SELECT stats_json 
                FROM index_stats 
                WHERE index_name = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
                """,
                (index_name,)
            ).fetchone()
            
            if row:
                return self._deserialize_stats(json.loads(row[0]))
            return None
            
    def get_stats_history(
        self,
        index_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[IndexStats]:
        """Get historical statistics for an index."""
        query = "SELECT stats_json FROM index_stats WHERE index_name = ?"
        params = [index_name]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
            
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
            
        query += " ORDER BY timestamp ASC"
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [
                self._deserialize_stats(json.loads(row[0]))
                for row in rows
            ]
            
    def get_snapshots(
        self,
        index_name: str,
        snapshot_type: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recent snapshots of a specific type."""
        with self._get_connection() as conn:
            rows = conn.execute(
                """
                SELECT snapshot_data, timestamp 
                FROM index_snapshots 
                WHERE index_name = ? AND snapshot_type = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
                """,
                (index_name, snapshot_type, limit)
            ).fetchall()
            
            return [
                {
                    "data": json.loads(row[0]),
                    "timestamp": datetime.fromisoformat(row[1])
                }
                for row in rows
            ]
            
    def cleanup_old_stats(self, days_to_keep: int = 30):
        """Remove statistics older than specified days."""
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM index_stats WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            conn.execute(
                "DELETE FROM index_snapshots WHERE timestamp < ?",
                (cutoff.isoformat(),)
            )
            conn.commit()
            
    def _deserialize_stats(self, data: Dict[str, Any]) -> IndexStats:
        """Convert JSON data back to IndexStats object."""
        return IndexStats(
            index_name=data["index_name"],
            table_name=data["table_name"],
            index_type=data["index_type"],
            created_at=datetime.fromisoformat(data["created_at"]),
            usage=IndexUsageStats(**data["usage"]),
            size=IndexSizeStats(**data["size"]),
            condition=IndexConditionStats(**data["condition"])
            if data.get("condition")
            else None,
            maintenance=IndexMaintenanceStats(**data["maintenance"])
        )

class StatisticsManager:
    """Manages collection and analysis of index statistics."""
    
    def __init__(self, store: StatisticsStore):
        self.store = store
        self._snapshot_interval = timedelta(hours=1)
        self._last_snapshot: Dict[str, datetime] = {}
        
    def update_stats(self, stats: IndexStats):
        """Update statistics for an index."""
        self.store.save_stats(stats)
        
        # Check if we need to take a snapshot
        last_snapshot = self._last_snapshot.get(stats.index_name)
        if (not last_snapshot or 
            datetime.now() - last_snapshot >= self._snapshot_interval):
            self._take_snapshot(stats)
            
    def _take_snapshot(self, stats: IndexStats):
        """Take a snapshot of current metrics."""
        # Size snapshot
        self.store.save_snapshot(
            stats.index_name,
            "size",
            {
                "total_entries": stats.size.total_entries,
                "size_bytes": stats.size.size_bytes,
                "fragmentation": stats.size.fragmentation_ratio
            }
        )
        
        # Performance snapshot
        self.store.save_snapshot(
            stats.index_name,
            "performance",
            {
                "avg_read_time": stats.usage.avg_read_time_ms,
                "avg_write_time": stats.usage.avg_write_time_ms,
                "cache_hit_ratio": (
                    stats.usage.cache_hits /
                    (stats.usage.cache_hits + stats.usage.cache_misses)
                    if stats.usage.cache_hits + stats.usage.cache_misses > 0
                    else 0
                )
            }
        )
        
        # Condition snapshot (if applicable)
        if stats.condition:
            self.store.save_snapshot(
                stats.index_name,
                "condition",
                {
                    "selectivity": stats.condition.selectivity,
                    "false_positive_rate": stats.condition.false_positive_rate,
                    "evaluation_time": stats.condition.evaluation_time_ms
                }
            )
            
        self._last_snapshot[stats.index_name] = datetime.now()
        
    def analyze_trends(
        self,
        index_name: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Analyze index performance trends."""
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        history = self.store.get_stats_history(
            index_name,
            start_time,
            end_time
        )
        
        if not history:
            return {}
            
        # Analyze growth
        size_trend = [stats.size.total_entries for stats in history]
        growth_rate = (
            (size_trend[-1] - size_trend[0]) / len(size_trend)
            if len(size_trend) > 1
            else 0
        )
        
        # Analyze performance
        read_times = [stats.usage.avg_read_time_ms for stats in history]
        write_times = [stats.usage.avg_write_time_ms for stats in history]
        
        # Analyze maintenance
        maintenance_events = sum(
            1 for stats in history
            if stats.maintenance.last_reindex or
            stats.maintenance.last_analyze or
            stats.maintenance.last_vacuum
        )
        
        return {
            "growth_rate_per_day": growth_rate * 24,
            "avg_read_time_trend": sum(read_times) / len(read_times),
            "avg_write_time_trend": sum(write_times) / len(write_times),
            "maintenance_frequency": maintenance_events / days,
            "needs_optimization": self._needs_optimization(history[-1])
        }
        
    def _needs_optimization(self, stats: IndexStats) -> bool:
        """Determine if index needs optimization."""
        return any([
            stats.size.fragmentation_ratio > 0.3,
            stats.usage.avg_read_time_ms > 100,
            stats.condition and stats.condition.false_positive_rate > 0.2
        ]) 