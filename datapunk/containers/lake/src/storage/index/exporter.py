from typing import Dict, Any, List, Optional, Union, TextIO
from dataclasses import asdict, dataclass
from datetime import datetime
import json
import csv
import yaml
import zipfile
import io
import os
from pathlib import Path
from enum import Enum

from .stats import (
    IndexStats,
    IndexUsageStats,
    IndexSizeStats,
    IndexConditionStats,
    IndexMaintenanceStats,
    StatisticsStore
)

class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    YAML = "yaml"
    PARQUET = "parquet"

@dataclass
class ExportMetadata:
    """Metadata for exported statistics."""
    version: str = "1.0"
    exported_at: datetime = datetime.now()
    index_count: int = 0
    record_count: int = 0
    format: ExportFormat = ExportFormat.JSON
    compression: bool = False
    checksum: Optional[str] = None

class StatisticsExporter:
    """Exports and imports index statistics."""
    
    def __init__(self, store: StatisticsStore):
        self.store = store
        
    def export_stats(
        self,
        output_path: Union[str, Path, TextIO],
        format: ExportFormat = ExportFormat.JSON,
        index_names: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        compress: bool = False,
        include_snapshots: bool = True
    ) -> ExportMetadata:
        """Export statistics to file."""
        # Get statistics
        if index_names:
            stats_list = []
            for name in index_names:
                stats = self.store.get_stats_history(name, start_time, end_time)
                stats_list.extend(stats)
        else:
            stats_list = self.store.get_stats_history("*", start_time, end_time)
            
        # Get snapshots if requested
        snapshots = []
        if include_snapshots:
            for stats in stats_list:
                snaps = self.store.get_snapshots(
                    stats.index_name,
                    "*"  # All snapshot types
                )
                snapshots.extend(snaps)
                
        # Create export data
        export_data = {
            "metadata": {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "index_count": len(set(s.index_name for s in stats_list)),
                "record_count": len(stats_list),
                "format": format.value,
                "compression": compress
            },
            "statistics": [self._serialize_stats(s) for s in stats_list],
            "snapshots": snapshots if include_snapshots else []
        }
        
        # Export based on format
        if format == ExportFormat.JSON:
            self._export_json(export_data, output_path, compress)
        elif format == ExportFormat.CSV:
            self._export_csv(export_data, output_path, compress)
        elif format == ExportFormat.YAML:
            self._export_yaml(export_data, output_path, compress)
        elif format == ExportFormat.PARQUET:
            self._export_parquet(export_data, output_path)
            
        return ExportMetadata(
            version="1.0",
            exported_at=datetime.now(),
            index_count=len(set(s.index_name for s in stats_list)),
            record_count=len(stats_list),
            format=format,
            compression=compress,
            checksum=self._calculate_checksum(output_path)
        )
        
    def import_stats(
        self,
        input_path: Union[str, Path, TextIO],
        format: Optional[ExportFormat] = None,
        validate: bool = True
    ) -> ExportMetadata:
        """Import statistics from file."""
        # Detect format if not specified
        if not format:
            format = self._detect_format(input_path)
            
        # Import based on format
        if format == ExportFormat.JSON:
            data = self._import_json(input_path)
        elif format == ExportFormat.CSV:
            data = self._import_csv(input_path)
        elif format == ExportFormat.YAML:
            data = self._import_yaml(input_path)
        elif format == ExportFormat.PARQUET:
            data = self._import_parquet(input_path)
            
        # Validate if requested
        if validate:
            self._validate_import(data)
            
        # Import statistics
        for stat_data in data["statistics"]:
            stats = self._deserialize_stats(stat_data)
            self.store.save_stats(stats)
            
        # Import snapshots
        if "snapshots" in data:
            for snapshot in data["snapshots"]:
                self.store.save_snapshot(
                    snapshot["index_name"],
                    snapshot["snapshot_type"],
                    snapshot["snapshot_data"]
                )
                
        return ExportMetadata(**data["metadata"])
        
    def _serialize_stats(self, stats: IndexStats) -> Dict[str, Any]:
        """Convert statistics to serializable format."""
        data = asdict(stats)
        
        # Convert datetime objects
        data["created_at"] = stats.created_at.isoformat()
        if stats.usage.last_used:
            data["usage"]["last_used"] = stats.usage.last_used.isoformat()
        if stats.size.last_compacted:
            data["size"]["last_compacted"] = stats.size.last_compacted.isoformat()
        if stats.condition and stats.condition.last_optimized:
            data["condition"]["last_optimized"] = stats.condition.last_optimized.isoformat()
            
        return data
        
    def _deserialize_stats(self, data: Dict[str, Any]) -> IndexStats:
        """Convert serialized data back to statistics objects."""
        # Convert datetime strings
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        if data["usage"].get("last_used"):
            data["usage"]["last_used"] = datetime.fromisoformat(
                data["usage"]["last_used"]
            )
        if data["size"].get("last_compacted"):
            data["size"]["last_compacted"] = datetime.fromisoformat(
                data["size"]["last_compacted"]
            )
        if data.get("condition", {}).get("last_optimized"):
            data["condition"]["last_optimized"] = datetime.fromisoformat(
                data["condition"]["last_optimized"]
            )
            
        # Create objects
        usage = IndexUsageStats(**data["usage"])
        size = IndexSizeStats(**data["size"])
        condition = (
            IndexConditionStats(**data["condition"])
            if data.get("condition")
            else None
        )
        maintenance = IndexMaintenanceStats(**data.get("maintenance", {}))
        
        return IndexStats(
            index_name=data["index_name"],
            table_name=data["table_name"],
            index_type=data["index_type"],
            created_at=data["created_at"],
            usage=usage,
            size=size,
            condition=condition,
            maintenance=maintenance
        )
        
    def _export_json(
        self,
        data: Dict[str, Any],
        output_path: Union[str, Path, TextIO],
        compress: bool
    ):
        """Export data in JSON format."""
        if compress:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    'stats.json',
                    json.dumps(data, indent=2)
                )
        else:
            if isinstance(output_path, (str, Path)):
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
            else:
                json.dump(data, output_path, indent=2)
                
    def _export_csv(
        self,
        data: Dict[str, Any],
        output_path: Union[str, Path, TextIO],
        compress: bool
    ):
        """Export data in CSV format."""
        # Flatten statistics for CSV format
        flat_stats = []
        for stat in data["statistics"]:
            flat_stat = {
                "index_name": stat["index_name"],
                "table_name": stat["table_name"],
                "index_type": stat["index_type"],
                "created_at": stat["created_at"]
            }
            # Flatten nested structures
            for key, value in stat["usage"].items():
                flat_stat[f"usage_{key}"] = value
            for key, value in stat["size"].items():
                flat_stat[f"size_{key}"] = value
            if stat.get("condition"):
                for key, value in stat["condition"].items():
                    flat_stat[f"condition_{key}"] = value
            flat_stats.append(flat_stat)
            
        if compress:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                with io.StringIO() as buffer:
                    writer = csv.DictWriter(buffer, fieldnames=flat_stats[0].keys())
                    writer.writeheader()
                    writer.writerows(flat_stats)
                    zf.writestr('stats.csv', buffer.getvalue())
        else:
            if isinstance(output_path, (str, Path)):
                with open(output_path, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=flat_stats[0].keys())
                    writer.writeheader()
                    writer.writerows(flat_stats)
            else:
                writer = csv.DictWriter(output_path, fieldnames=flat_stats[0].keys())
                writer.writeheader()
                writer.writerows(flat_stats)
                
    def _export_yaml(
        self,
        data: Dict[str, Any],
        output_path: Union[str, Path, TextIO],
        compress: bool
    ):
        """Export data in YAML format."""
        if compress:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    'stats.yaml',
                    yaml.dump(data, default_flow_style=False)
                )
        else:
            if isinstance(output_path, (str, Path)):
                with open(output_path, 'w') as f:
                    yaml.dump(data, f, default_flow_style=False)
            else:
                yaml.dump(data, output_path, default_flow_style=False)
                
    def _export_parquet(
        self,
        data: Dict[str, Any],
        output_path: Union[str, Path]
    ):
        """Export data in Parquet format."""
        import pandas as pd
        
        # Convert to DataFrame
        df = pd.DataFrame([
            self._flatten_dict(self._serialize_stats(s))
            for s in data["statistics"]
        ])
        
        # Save to Parquet
        df.to_parquet(output_path, compression='snappy')
        
    def _import_json(
        self,
        input_path: Union[str, Path, TextIO]
    ) -> Dict[str, Any]:
        """Import data from JSON format."""
        if isinstance(input_path, (str, Path)):
            if zipfile.is_zipfile(input_path):
                with zipfile.ZipFile(input_path, 'r') as zf:
                    with zf.open('stats.json') as f:
                        return json.load(io.TextIOWrapper(f))
            else:
                with open(input_path, 'r') as f:
                    return json.load(f)
        else:
            return json.load(input_path)
            
    def _import_csv(
        self,
        input_path: Union[str, Path, TextIO]
    ) -> Dict[str, Any]:
        """Import data from CSV format."""
        if isinstance(input_path, (str, Path)):
            if zipfile.is_zipfile(input_path):
                with zipfile.ZipFile(input_path, 'r') as zf:
                    with zf.open('stats.csv') as f:
                        reader = csv.DictReader(io.TextIOWrapper(f))
                        flat_stats = list(reader)
            else:
                with open(input_path, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    flat_stats = list(reader)
        else:
            reader = csv.DictReader(input_path)
            flat_stats = list(reader)
            
        # Unflatten statistics
        stats = []
        for flat_stat in flat_stats:
            stat = {
                "index_name": flat_stat["index_name"],
                "table_name": flat_stat["table_name"],
                "index_type": flat_stat["index_type"],
                "created_at": flat_stat["created_at"],
                "usage": {},
                "size": {},
                "condition": {}
            }
            
            for key, value in flat_stat.items():
                if key.startswith("usage_"):
                    stat["usage"][key[6:]] = value
                elif key.startswith("size_"):
                    stat["size"][key[5:]] = value
                elif key.startswith("condition_"):
                    stat["condition"][key[10:]] = value
                    
            stats.append(stat)
            
        return {
            "metadata": {
                "version": "1.0",
                "imported_at": datetime.now().isoformat(),
                "format": "csv"
            },
            "statistics": stats
        }
        
    def _import_yaml(
        self,
        input_path: Union[str, Path, TextIO]
    ) -> Dict[str, Any]:
        """Import data from YAML format."""
        if isinstance(input_path, (str, Path)):
            if zipfile.is_zipfile(input_path):
                with zipfile.ZipFile(input_path, 'r') as zf:
                    with zf.open('stats.yaml') as f:
                        return yaml.safe_load(io.TextIOWrapper(f))
            else:
                with open(input_path, 'r') as f:
                    return yaml.safe_load(f)
        else:
            return yaml.safe_load(input_path)
            
    def _import_parquet(
        self,
        input_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """Import data from Parquet format."""
        import pandas as pd
        
        # Read DataFrame
        df = pd.read_parquet(input_path)
        
        # Convert to dictionary format
        stats = []
        for _, row in df.iterrows():
            stats.append(self._unflatten_dict(row.to_dict()))
            
        return {
            "metadata": {
                "version": "1.0",
                "imported_at": datetime.now().isoformat(),
                "format": "parquet"
            },
            "statistics": stats
        }
        
    def _detect_format(
        self,
        input_path: Union[str, Path, TextIO]
    ) -> ExportFormat:
        """Detect the format of input file."""
        if isinstance(input_path, (str, Path)):
            ext = os.path.splitext(str(input_path))[1].lower()
            if ext == '.json':
                return ExportFormat.JSON
            elif ext == '.csv':
                return ExportFormat.CSV
            elif ext in ('.yml', '.yaml'):
                return ExportFormat.YAML
            elif ext == '.parquet':
                return ExportFormat.PARQUET
        raise ValueError("Could not detect format")
        
    def _validate_import(self, data: Dict[str, Any]):
        """Validate imported data."""
        required_fields = ["metadata", "statistics"]
        if not all(field in data for field in required_fields):
            raise ValueError("Missing required fields in import data")
            
        for stat in data["statistics"]:
            required_stat_fields = [
                "index_name", "table_name", "index_type",
                "created_at", "usage", "size"
            ]
            if not all(field in stat for field in required_stat_fields):
                raise ValueError(f"Missing required fields in stat: {stat}")
                
    def _calculate_checksum(
        self,
        path: Union[str, Path, TextIO]
    ) -> Optional[str]:
        """Calculate checksum of exported file."""
        import hashlib
        
        if isinstance(path, (str, Path)):
            with open(path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        return None
        
    def _flatten_dict(
        self,
        d: Dict[str, Any],
        parent_key: str = '',
        sep: str = '_'
    ) -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(
                    self._flatten_dict(v, new_key, sep=sep).items()
                )
            else:
                items.append((new_key, v))
        return dict(items)
        
    def _unflatten_dict(
        self,
        d: Dict[str, Any],
        sep: str = '_'
    ) -> Dict[str, Any]:
        """Unflatten dictionary with separated keys."""
        result = {}
        
        for key, value in d.items():
            parts = key.split(sep)
            target = result
            for part in parts[:-1]:
                target = target.setdefault(part, {})
            target[parts[-1]] = value
            
        return result 