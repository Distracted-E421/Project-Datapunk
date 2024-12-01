from typing import Dict, Any, List, Optional, Union, Callable, Set
from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
import importlib.util
import sys
import jsonschema
from enum import Enum
import copy

logger = logging.getLogger(__name__)

class MigrationEvent(Enum):
    """Migration lifecycle events."""
    BEFORE_UPGRADE = "before_upgrade"
    AFTER_UPGRADE = "after_upgrade"
    BEFORE_DOWNGRADE = "before_downgrade"
    AFTER_DOWNGRADE = "after_downgrade"
    VALIDATION_START = "validation_start"
    VALIDATION_END = "validation_end"

@dataclass
class MigrationHistory:
    """Record of a migration execution."""
    version: str
    direction: str  # "upgrade" or "downgrade"
    timestamp: datetime
    duration_ms: float
    success: bool
    error: Optional[str] = None

@dataclass
class MigrationInfo:
    """Information about a data migration."""
    version: str
    description: str
    timestamp: datetime
    changes: List[str]
    backward_compatible: bool
    dependencies: List[str]
    schema: Optional[Dict[str, Any]] = None

class Migration:
    """Base class for data migrations."""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.changes: List[str] = []
        self.backward_compatible = True
        self.dependencies: List[str] = []
        self.schema: Optional[Dict[str, Any]] = None
        self.hooks: Dict[MigrationEvent, List[Callable]] = {
            event: [] for event in MigrationEvent
        }
        
    def upgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade data to this version."""
        raise NotImplementedError
        
    def downgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Downgrade data from this version."""
        raise NotImplementedError
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data format."""
        if self.schema:
            try:
                jsonschema.validate(data, self.schema)
                return True
            except jsonschema.exceptions.ValidationError:
                return False
        return True
        
    def add_hook(self, event: MigrationEvent, callback: Callable):
        """Add a hook for a migration event."""
        self.hooks[event].append(callback)
        
    def remove_hook(self, event: MigrationEvent, callback: Callable):
        """Remove a hook for a migration event."""
        if callback in self.hooks[event]:
            self.hooks[event].remove(callback)
            
    def _trigger_hooks(self, event: MigrationEvent, data: Dict[str, Any]):
        """Trigger hooks for an event."""
        for hook in self.hooks[event]:
            try:
                hook(data)
            except Exception as e:
                logger.error(f"Hook error for {event.value}: {e}")

class MigrationManager:
    """Manages data migrations for incremental exports."""
    
    def __init__(
        self,
        migrations_dir: Union[str, Path],
        current_version: str = "1.0.0",
        history_file: Optional[Union[str, Path]] = None
    ):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self.current_version = current_version
        self.migrations: Dict[str, Migration] = {}
        self.history: List[MigrationHistory] = []
        self.history_file = Path(history_file) if history_file else self.migrations_dir / "migration_history.json"
        self._load_migrations()
        self._load_history()
        
    def _load_history(self):
        """Load migration history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    history_data = json.load(f)
                    self.history = [
                        MigrationHistory(
                            version=h["version"],
                            direction=h["direction"],
                            timestamp=datetime.fromisoformat(h["timestamp"]),
                            duration_ms=h["duration_ms"],
                            success=h["success"],
                            error=h.get("error")
                        )
                        for h in history_data
                    ]
            except Exception as e:
                logger.error(f"Failed to load history: {e}")
                
    def _save_history(self):
        """Save migration history to file."""
        try:
            history_data = [
                {
                    "version": h.version,
                    "direction": h.direction,
                    "timestamp": h.timestamp.isoformat(),
                    "duration_ms": h.duration_ms,
                    "success": h.success,
                    "error": h.error
                }
                for h in self.history
            ]
            
            with open(self.history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            
    def dry_run(
        self,
        data: Dict[str, Any],
        target_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Simulate migration without modifying data."""
        # Create deep copy of data
        data_copy = copy.deepcopy(data)
        
        try:
            # Simulate migration
            return self.migrate(
                data_copy,
                target_version,
                validate=True,
                dry_run=True
            )
        except Exception as e:
            logger.error(f"Dry run failed: {e}")
            raise
            
    def migrate(
        self,
        data: Dict[str, Any],
        target_version: Optional[str] = None,
        validate: bool = True,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Migrate data to target version."""
        current_version = data.get("version", "1.0.0")
        target_version = target_version or self.current_version
        
        if current_version == target_version:
            return data
            
        # Determine migration path
        path = self._get_migration_path(current_version, target_version)
        if not path:
            raise ValueError(
                f"No migration path from {current_version} to {target_version}"
            )
            
        # Check dependencies
        self._verify_dependencies(path)
        
        # Apply migrations
        migrated_data = data.copy() if dry_run else data
        for version in path:
            migration = self.migrations[version]
            start_time = datetime.now()
            success = True
            error = None
            
            try:
                if validate:
                    migration._trigger_hooks(MigrationEvent.VALIDATION_START, migrated_data)
                    if not migration.validate(migrated_data):
                        raise ValueError(
                            f"Data validation failed for version {version}"
                        )
                    migration._trigger_hooks(MigrationEvent.VALIDATION_END, migrated_data)
                    
                if version > current_version:
                    migration._trigger_hooks(MigrationEvent.BEFORE_UPGRADE, migrated_data)
                    migrated_data = migration.upgrade(migrated_data)
                    migration._trigger_hooks(MigrationEvent.AFTER_UPGRADE, migrated_data)
                    direction = "upgrade"
                else:
                    migration._trigger_hooks(MigrationEvent.BEFORE_DOWNGRADE, migrated_data)
                    migrated_data = migration.downgrade(migrated_data)
                    migration._trigger_hooks(MigrationEvent.AFTER_DOWNGRADE, migrated_data)
                    direction = "downgrade"
                    
                migrated_data["version"] = version
                logger.info(f"Migrated data to version {version}")
                
            except Exception as e:
                logger.error(f"Migration to {version} failed: {e}")
                success = False
                error = str(e)
                raise
                
            finally:
                if not dry_run:
                    # Record migration history
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    self.history.append(
                        MigrationHistory(
                            version=version,
                            direction=direction,
                            timestamp=start_time,
                            duration_ms=duration,
                            success=success,
                            error=error
                        )
                    )
                    self._save_history()
                    
        return migrated_data
        
    def _verify_dependencies(self, versions: List[str]):
        """Verify all migration dependencies are satisfied."""
        available = set(self.migrations.keys())
        for version in versions:
            migration = self.migrations[version]
            missing = set(migration.dependencies) - available
            if missing:
                raise ValueError(
                    f"Missing dependencies for {version}: {missing}"
                )
                
    def get_migration_history(
        self,
        version: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[MigrationHistory]:
        """Get migration history, optionally filtered by version."""
        history = self.history
        if version:
            history = [h for h in history if h.version == version]
        if limit:
            history = history[-limit:]
        return history
        
    def clear_history(self):
        """Clear migration history."""
        self.history = []
        self._save_history()
        
    def register_global_hook(
        self,
        event: MigrationEvent,
        callback: Callable
    ):
        """Register a hook for all migrations."""
        for migration in self.migrations.values():
            migration.add_hook(event, callback)
            
    def set_schema(
        self,
        version: str,
        schema: Dict[str, Any]
    ):
        """Set JSON schema for a migration version."""
        if version in self.migrations:
            self.migrations[version].schema = schema

    def _load_migrations(self):
        """Load migration scripts from directory."""
        sys.path.append(str(self.migrations_dir))
        
        for file in self.migrations_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue
                
            try:
                # Import migration module
                spec = importlib.util.spec_from_file_location(
                    file.stem,
                    str(file)
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Get migration class
                    migration_class = getattr(module, "Migration", None)
                    if migration_class and issubclass(migration_class, Migration):
                        migration = migration_class()
                        self.migrations[migration.version] = migration
                        logger.info(f"Loaded migration {migration.version}")
                        
            except Exception as e:
                logger.error(f"Failed to load migration {file}: {e}")
                
        sys.path.remove(str(self.migrations_dir))
        
    def create_migration(
        self,
        version: str,
        description: str,
        template: Optional[str] = None
    ) -> Path:
        """Create a new migration script."""
        if version in self.migrations:
            raise ValueError(f"Migration {version} already exists")
            
        file_path = self.migrations_dir / f"migration_{version}.py"
        
        if template:
            template_path = Path(template)
            if template_path.exists():
                with open(template_path, 'r') as f:
                    content = f.read()
            else:
                content = template
        else:
            content = f'''
from typing import Dict, Any
from ..migration import Migration

class Migration(Migration):
    def __init__(self):
        super().__init__(
            version="{version}",
            description="{description}"
        )
        
    def upgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade data to version {version}."""
        # TODO: Implement upgrade logic
        return data
        
    def downgrade(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Downgrade data from version {version}."""
        # TODO: Implement downgrade logic
        return data
        
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data format for version {version}."""
        # TODO: Implement validation logic
        return True
'''
        
        with open(file_path, 'w') as f:
            f.write(content)
            
        return file_path
        
    def _get_migration_path(
        self,
        from_version: str,
        to_version: str
    ) -> Optional[List[str]]:
        """Find path between versions."""
        if from_version == to_version:
            return []
            
        # Simple BFS to find shortest path
        queue = [(from_version, [from_version])]
        visited = {from_version}
        
        while queue:
            current, path = queue.pop(0)
            
            # Find adjacent versions
            adjacent = set()
            for version in self.migrations:
                if version not in visited:
                    # Check if direct migration is possible
                    if self._can_migrate(current, version):
                        adjacent.add(version)
                        
            for version in adjacent:
                if version == to_version:
                    return path + [version]
                    
                visited.add(version)
                queue.append((version, path + [version]))
                
        return None
        
    def _can_migrate(self, from_version: str, to_version: str) -> bool:
        """Check if direct migration between versions is possible."""
        if from_version == to_version:
            return True
            
        # Check if migration exists
        if to_version not in self.migrations:
            return False
            
        # Check version compatibility
        try:
            from packaging import version
            v1 = version.parse(from_version)
            v2 = version.parse(to_version)
            
            # Only allow migrations between adjacent versions
            # or backward compatible versions
            if v2 > v1:
                return (
                    v2.release[:-1] == v1.release[:-1] or
                    self.migrations[to_version].backward_compatible
                )
            else:
                return (
                    v1.release[:-1] == v2.release[:-1] or
                    self.migrations[from_version].backward_compatible
                )
                
        except Exception:
            # If version parsing fails, only allow explicit migrations
            return to_version in self.migrations
            
    def get_migration_info(self, version: str) -> Optional[MigrationInfo]:
        """Get information about a migration."""
        migration = self.migrations.get(version)
        if not migration:
            return None
            
        return MigrationInfo(
            version=migration.version,
            description=migration.description,
            timestamp=datetime.now(),  # TODO: Store actual timestamp
            changes=migration.changes,
            backward_compatible=migration.backward_compatible,
            dependencies=migration.dependencies,
            schema=migration.schema
        )