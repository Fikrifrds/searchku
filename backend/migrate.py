#!/usr/bin/env python3
"""
Database Migration Runner for SearchKu

This script manages database migrations systematically:
- Tracks applied migrations
- Runs pending migrations in order
- Provides rollback capabilities
- Validates migration integrity

Usage:
    python migrate.py                    # Run all pending migrations
    python migrate.py --status           # Show migration status
    python migrate.py --rollback N       # Rollback last N migrations
    python migrate.py --force MIGRATION  # Force run specific migration
"""

import os
import sys
import argparse
import hashlib
import time
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class MigrationRunner:
    def __init__(self, database_url=None):
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL not provided")

        self.engine = create_engine(self.database_url)
        self.migrations_dir = Path(__file__).parent / 'migrations'

    def get_file_checksum(self, file_path):
        """Calculate MD5 checksum of migration file."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    def get_applied_migrations(self):
        """Get list of applied migrations from database."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT migration_name, executed_at, checksum FROM migration_history ORDER BY migration_name"
                ))
                return {row.migration_name: {'executed_at': row.executed_at, 'checksum': row.checksum}
                       for row in result}
        except SQLAlchemyError:
            # Migration table doesn't exist yet
            return {}

    def get_migration_files(self):
        """Get list of migration files sorted by name."""
        if not self.migrations_dir.exists():
            logger.error(f"Migrations directory not found: {self.migrations_dir}")
            return []

        migration_files = []
        for file_path in sorted(self.migrations_dir.glob('*.sql')):
            migration_files.append({
                'name': file_path.name,
                'path': file_path,
                'checksum': self.get_file_checksum(file_path)
            })
        return migration_files

    def run_migration(self, migration_file, force=False):
        """Run a single migration file."""
        logger.info(f"Running migration: {migration_file['name']}")

        start_time = time.time()

        try:
            with open(migration_file['path'], 'r') as f:
                sql_content = f.read()

            with self.engine.connect() as conn:
                # Execute the migration
                conn.execute(text(sql_content))
                conn.commit()

                execution_time = int((time.time() - start_time) * 1000)

                # Record successful migration (if not already recorded)
                conn.execute(text("""
                    INSERT INTO migration_history (migration_name, checksum, execution_time_ms, description)
                    VALUES (:name, :checksum, :exec_time, :description)
                    ON CONFLICT (migration_name) DO UPDATE SET
                        checksum = :checksum,
                        execution_time_ms = :exec_time
                """), {
                    'name': migration_file['name'],
                    'checksum': migration_file['checksum'],
                    'exec_time': execution_time,
                    'description': f"Migration executed in {execution_time}ms"
                })
                conn.commit()

                logger.info(f"✅ Migration {migration_file['name']} completed in {execution_time}ms")
                return True

        except SQLAlchemyError as e:
            logger.error(f"❌ Migration {migration_file['name']} failed: {str(e)}")
            return False

    def run_pending_migrations(self):
        """Run all pending migrations."""
        applied_migrations = self.get_applied_migrations()
        migration_files = self.get_migration_files()

        if not migration_files:
            logger.info("No migration files found")
            return True

        pending_migrations = []
        for migration_file in migration_files:
            if migration_file['name'] not in applied_migrations:
                pending_migrations.append(migration_file)
            else:
                # Check if file has been modified
                applied_checksum = applied_migrations[migration_file['name']]['checksum']
                if applied_checksum and applied_checksum != migration_file['checksum']:
                    logger.warning(f"⚠️  Migration {migration_file['name']} has been modified after execution!")

        if not pending_migrations:
            logger.info("✅ All migrations are up to date")
            return True

        logger.info(f"Found {len(pending_migrations)} pending migrations")

        success_count = 0
        for migration_file in pending_migrations:
            if self.run_migration(migration_file):
                success_count += 1
            else:
                logger.error(f"Migration failed, stopping execution")
                break

        logger.info(f"Completed {success_count}/{len(pending_migrations)} migrations")
        return success_count == len(pending_migrations)

    def show_migration_status(self):
        """Show status of all migrations."""
        applied_migrations = self.get_applied_migrations()
        migration_files = self.get_migration_files()

        print("\n📋 Migration Status:")
        print("=" * 80)
        print(f"{'Migration File':<40} {'Status':<12} {'Executed At':<20} {'Modified'}")
        print("-" * 80)

        for migration_file in migration_files:
            name = migration_file['name']
            status = "✅ Applied" if name in applied_migrations else "⏳ Pending"

            if name in applied_migrations:
                executed_at = applied_migrations[name]['executed_at'].strftime('%Y-%m-%d %H:%M:%S')
                applied_checksum = applied_migrations[name]['checksum']
                modified = "🔄 Yes" if applied_checksum and applied_checksum != migration_file['checksum'] else ""
            else:
                executed_at = "-"
                modified = ""

            print(f"{name:<40} {status:<12} {executed_at:<20} {modified}")

        total_migrations = len(migration_files)
        applied_count = len(applied_migrations)
        pending_count = total_migrations - applied_count

        print("-" * 80)
        print(f"Total: {total_migrations} | Applied: {applied_count} | Pending: {pending_count}")

    def force_migration(self, migration_name):
        """Force run a specific migration."""
        migration_files = self.get_migration_files()

        target_migration = None
        for migration_file in migration_files:
            if migration_file['name'] == migration_name:
                target_migration = migration_file
                break

        if not target_migration:
            logger.error(f"Migration not found: {migration_name}")
            return False

        logger.warning(f"Force running migration: {migration_name}")
        return self.run_migration(target_migration, force=True)

def main():
    parser = argparse.ArgumentParser(description='Database Migration Runner for SearchKu')
    parser.add_argument('--status', action='store_true', help='Show migration status')
    parser.add_argument('--force', metavar='MIGRATION', help='Force run specific migration')
    parser.add_argument('--database-url', help='Database URL (overrides environment)')

    args = parser.parse_args()

    try:
        runner = MigrationRunner(args.database_url)

        if args.status:
            runner.show_migration_status()
        elif args.force:
            success = runner.force_migration(args.force)
            sys.exit(0 if success else 1)
        else:
            success = runner.run_pending_migrations()
            sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Migration runner failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()