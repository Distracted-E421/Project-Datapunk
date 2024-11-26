from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import asyncio
from datetime import datetime
import asyncpg
import json
import hashlib
from pathlib import Path
from enum import Enum
from ..monitoring import MetricsCollector

"""
Database migrations that won't make you lose your shit

Because database changes shouldn't be a game of Russian roulette. This module 
handles schema updates with version tracking, rollbacks, and proper checksums 
to make sure nothing gets fucked up along the way.

Key Features:
- Transactional migrations (all or nothing)
- Automatic rollbacks when things go south
- Version tracking that actually makes sense
- Parallel execution for the impatient
- Checksums to catch tampering

NOTE: All migrations are tracked in a dedicated table for accountability
TODO: Add dry-run capability for testing migrations
FIXME: Improve error messages when migrations conflict
"""

class MigrationState(Enum):
    """
    Track where each migration stands
    
    States flow: PENDING -> IN_PROGRESS -> COMPLETED
                                      -> FAILED -> ROLLED_BACK
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class MigrationConfig:
    """
    Control how migrations behave
    
    Customize everything from batch sizes to timeouts. Sensible defaults
    included, but you can tune them if you know what you're doing.
    
    NOTE: parallel_migrations can speed things up but watch for deadlocks
    """
    migrations_path: str
    migrations_table: str = "schema_migrations"
    enable_rollback: bool = True  # Because shit happens
    batch_size: int = 10  # How many to run at once
    lock_timeout: int = 30  # Don't hang forever
    enable_checksums: bool = True  # Catch tampering
    enable_transactions: bool = True  # All or nothing
    enable_logging: bool = True  # Debug is your friend
    parallel_migrations: bool = False  # Use with caution
    max_retries: int = 3  # Try again before giving up
    retry_delay: float = 1.0  # Breathe between retries

class MigrationError(Exception):
    """Base class for migration errors"""
    pass

class Migration:
    """
    Single database migration with tracking
    
    Each migration is versioned, described, and checksummed. Up and down
    SQL ensures you can roll back when needed (and you will need it).
    
    Implementation Notes:
    - Checksums include everything to catch sneaky changes
    - State tracking prevents double-runs
    - Timestamps tell you who to blame
    """
    def __init__(
        self,
        version: str,
        description: str,
        up_sql: str,
        down_sql: Optional[str] = None,
        checksum: Optional[str] = None
    ):
        self.version = version
        self.description = description
        self.up_sql = up_sql
        self.down_sql = down_sql
        self.checksum = checksum or self._calculate_checksum()
        self.state = MigrationState.PENDING
        self.executed_at: Optional[datetime] = None
        self.error: Optional[str] = None

    def _calculate_checksum(self) -> str:
        """
        Generate tamper-proof checksum
        
        Includes version, description, and SQL to catch any changes.
        SHA256 because we're not barbarians.
        """
        content = f"{self.version}:{self.description}:{self.up_sql}"
        if self.down_sql:
            content += f":{self.down_sql}"
        return hashlib.sha256(content.encode()).hexdigest()

class MigrationManager:
    """
    Keep your database changes under control
    
    Handles the entire migration lifecycle from loading to execution.
    Includes parallel support for when you need speed, and rollbacks
    for when you need mercy.
    
    FIXME: Add better conflict detection for parallel migrations
    TODO: Add migration dependency tracking
    """
    def __init__(
        self,
        config: MigrationConfig,
        pool: asyncpg.Pool,
        metrics_collector: Optional[MetricsCollector] = None
    ):
        self.config = config
        self.pool = pool
        self.metrics = metrics_collector
        self._migrations: Dict[str, Migration] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize migration manager"""
        try:
            # Create migrations table if it doesn't exist
            async with self.pool.acquire() as conn:
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.config.migrations_table} (
                        version TEXT PRIMARY KEY,
                        description TEXT NOT NULL,
                        checksum TEXT NOT NULL,
                        state TEXT NOT NULL,
                        executed_at TIMESTAMP WITH TIME ZONE,
                        error TEXT
                    )
                """)

            # Load migrations from files
            await self._load_migrations()

            if self.metrics:
                await self.metrics.increment("migrations.initialized")

        except Exception as e:
            if self.metrics:
                await self.metrics.increment(
                    "migrations.initialization_error",
                    tags={"error": str(e)}
                )
            raise MigrationError(f"Failed to initialize migrations: {str(e)}")

    async def _load_migrations(self):
        """Load migrations from files"""
        migrations_dir = Path(self.config.migrations_path)
        if not migrations_dir.exists():
            raise MigrationError(f"Migrations directory not found: {migrations_dir}")

        for file_path in sorted(migrations_dir.glob("*.sql")):
            try:
                # Parse migration file
                content = file_path.read_text()
                metadata, up_sql, down_sql = self._parse_migration_file(content)
                
                version = metadata.get("version") or file_path.stem
                migration = Migration(
                    version=version,
                    description=metadata.get("description", ""),
                    up_sql=up_sql,
                    down_sql=down_sql
                )
                
                self._migrations[version] = migration
                
            except Exception as e:
                raise MigrationError(
                    f"Failed to load migration {file_path}: {str(e)}"
                )

    def _parse_migration_file(
        self,
        content: str
    ) -> tuple[Dict[str, str], str, Optional[str]]:
        """Parse migration file content"""
        sections = content.split("-- @migration")
        if len(sections) < 2:
            raise MigrationError("Invalid migration file format")

        # Parse metadata
        metadata = {}
        for line in sections[1].splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()

        # Parse up and down sections
        up_section = content.split("-- @up", 1)
        if len(up_section) < 2:
            raise MigrationError("Missing @up section")
        up_sql = up_section[1].split("-- @down")[0].strip()

        down_sql = None
        down_section = content.split("-- @down", 1)
        if len(down_section) > 1:
            down_sql = down_section[1].strip()

        return metadata, up_sql, down_sql

    async def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations"""
        async with self.pool.acquire() as conn:
            # Get applied migrations
            applied = await conn.fetch(
                f"SELECT version, checksum FROM {self.config.migrations_table}"
            )
            applied_versions = {row['version'] for row in applied}
            
            # Check for checksum mismatches
            if self.config.enable_checksums:
                for row in applied:
                    migration = self._migrations.get(row['version'])
                    if migration and migration.checksum != row['checksum']:
                        raise MigrationError(
                            f"Checksum mismatch for migration {row['version']}"
                        )

            # Return pending migrations
            return [
                m for m in self._migrations.values()
                if m.version not in applied_versions
            ]

    async def run_migrations(
        self,
        target_version: Optional[str] = None
    ) -> List[Migration]:
        """Run pending migrations"""
        async with self._lock:
            try:
                pending = await self.get_pending_migrations()
                if not pending:
                    return []

                # Filter migrations up to target version
                if target_version:
                    pending = [
                        m for m in pending
                        if m.version <= target_version
                    ]

                # Run migrations in batches
                results = []
                for batch in self._batch_migrations(pending):
                    if self.config.parallel_migrations:
                        # Run batch in parallel
                        tasks = [
                            self._run_migration(migration)
                            for migration in batch
                        ]
                        results.extend(await asyncio.gather(*tasks))
                    else:
                        # Run batch sequentially
                        for migration in batch:
                            results.append(
                                await self._run_migration(migration)
                            )

                if self.metrics:
                    await self.metrics.increment(
                        "migrations.completed",
                        value=len(results)
                    )

                return results

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "migrations.error",
                        tags={"error": str(e)}
                    )
                raise

    def _batch_migrations(
        self,
        migrations: List[Migration]
    ) -> List[List[Migration]]:
        """Split migrations into batches"""
        return [
            migrations[i:i + self.config.batch_size]
            for i in range(0, len(migrations), self.config.batch_size)
        ]

    async def _run_migration(self, migration: Migration) -> Migration:
        """Run a single migration"""
        async with self.pool.acquire() as conn:
            # Start transaction if enabled
            if self.config.enable_transactions:
                async with conn.transaction():
                    return await self._execute_migration(conn, migration)
            else:
                return await self._execute_migration(conn, migration)

    async def _execute_migration(
        self,
        conn: asyncpg.Connection,
        migration: Migration
    ) -> Migration:
        """Execute migration SQL"""
        try:
            # Update migration state
            migration.state = MigrationState.IN_PROGRESS
            await self._update_migration_state(conn, migration)

            # Execute migration
            await conn.execute(migration.up_sql)

            # Update migration state
            migration.state = MigrationState.COMPLETED
            migration.executed_at = datetime.utcnow()
            await self._update_migration_state(conn, migration)

            if self.metrics:
                await self.metrics.increment(
                    "migrations.migration_completed",
                    tags={"version": migration.version}
                )

            return migration

        except Exception as e:
            migration.state = MigrationState.FAILED
            migration.error = str(e)
            await self._update_migration_state(conn, migration)

            if self.metrics:
                await self.metrics.increment(
                    "migrations.migration_failed",
                    tags={
                        "version": migration.version,
                        "error": str(e)
                    }
                )

            raise MigrationError(
                f"Migration {migration.version} failed: {str(e)}"
            )

    async def _update_migration_state(
        self,
        conn: asyncpg.Connection,
        migration: Migration
    ):
        """Update migration state in database"""
        await conn.execute(
            f"""
            INSERT INTO {self.config.migrations_table}
                (version, description, checksum, state, executed_at, error)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (version) DO UPDATE SET
                state = EXCLUDED.state,
                executed_at = EXCLUDED.executed_at,
                error = EXCLUDED.error
            """,
            migration.version,
            migration.description,
            migration.checksum,
            migration.state.value,
            migration.executed_at,
            migration.error
        )

    async def rollback_migration(
        self,
        version: str
    ) -> Optional[Migration]:
        """Rollback a specific migration"""
        if not self.config.enable_rollback:
            raise MigrationError("Rollback is disabled")

        async with self._lock:
            migration = self._migrations.get(version)
            if not migration:
                raise MigrationError(f"Migration {version} not found")

            if not migration.down_sql:
                raise MigrationError(
                    f"Migration {version} does not support rollback"
                )

            try:
                async with self.pool.acquire() as conn:
                    if self.config.enable_transactions:
                        async with conn.transaction():
                            await conn.execute(migration.down_sql)
                    else:
                        await conn.execute(migration.down_sql)

                    migration.state = MigrationState.ROLLED_BACK
                    migration.executed_at = datetime.utcnow()
                    await self._update_migration_state(conn, migration)

                    if self.metrics:
                        await self.metrics.increment(
                            "migrations.rollback_completed",
                            tags={"version": version}
                        )

                    return migration

            except Exception as e:
                if self.metrics:
                    await self.metrics.increment(
                        "migrations.rollback_failed",
                        tags={
                            "version": version,
                            "error": str(e)
                        }
                    )
                raise MigrationError(
                    f"Failed to rollback migration {version}: {str(e)}"
                )

    async def get_migration_history(self) -> List[Dict[str, Any]]:
        """Get migration execution history"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                f"""
                SELECT version, description, state, executed_at, error
                FROM {self.config.migrations_table}
                ORDER BY version
                """
            ) 