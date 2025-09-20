# Database Migration Management

This document describes the database migration system for SearchKu.

## Overview

The migration system provides:
- **Sequential Migration Tracking**: Each migration is numbered and tracked
- **Idempotent Operations**: Migrations can be run multiple times safely
- **Rollback Protection**: Tracks migration integrity with checksums
- **Production Ready**: Designed for safe deployment to production

## Migration Files

All migration files are stored in the `migrations/` directory and follow this naming convention:
```
XXX_description.sql
```

Where:
- `XXX` = 3-digit sequential number (001, 002, etc.)
- `description` = Brief description using underscores

### Current Migrations

| File | Description | Status |
|------|-------------|---------|
| `000_create_migration_table.sql` | Creates migration tracking table | ✅ System |
| `001_initial_schema.sql` | Complete initial database schema with all features | ✅ Core |
| `002_update_embedding_model.sql` | Update default embedding model to text-embedding-3-large | ✅ Enhancement |
| `003_update_to_hnsw_index.sql` | Upgrade vector index from IVFFlat to HNSW | ✅ Performance |

## Migration Runner

### Basic Usage

```bash
# Run all pending migrations
python migrate.py

# Show migration status
python migrate.py --status

# Force run a specific migration
python migrate.py --force 001_initial_schema.sql
```

### Production Deployment

For production deployment:

1. **Backup Database First**:
   ```bash
   pg_dump -U username -h hostname searchku > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run Migrations**:
   ```bash
   python migrate.py --status  # Check current status
   python migrate.py           # Run pending migrations
   ```

3. **Verify Results**:
   ```bash
   python migrate.py --status  # Confirm all applied
   ```

## Creating New Migrations

### Step 1: Create Migration File

Create a new file with the next sequential number:
```sql
-- 004_add_new_feature.sql

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM migration_history WHERE migration_name = '004_add_new_feature.sql') THEN
        RAISE NOTICE 'Migration 004_add_new_feature.sql already applied, skipping...';
        RETURN;
    END IF;
END $$;

-- Your migration code here
ALTER TABLE books ADD COLUMN new_field VARCHAR(255);

-- Record this migration
INSERT INTO migration_history (migration_name, description)
VALUES ('004_add_new_feature.sql', 'Add new field to books table')
ON CONFLICT (migration_name) DO NOTHING;
```

### Step 2: Test Migration

```bash
# Test on development database
python migrate.py --status
python migrate.py
```

### Step 3: Migration Best Practices

#### ✅ DO:
- **Use IF NOT EXISTS** for creating tables/columns
- **Check migration_history** before applying changes
- **Add proper indexes** for new columns
- **Include descriptive comments**
- **Test on development first**
- **Use transactions** for complex operations

#### ❌ DON'T:
- **Delete or modify** existing migration files
- **Skip sequence numbers** (001, 002, 003...)
- **Make breaking changes** without coordination
- **Run migrations directly** in production without testing

## Migration Patterns

### Adding a Column
```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'books' AND column_name = 'new_field') THEN
        ALTER TABLE books ADD COLUMN new_field VARCHAR(255);
        RAISE NOTICE 'Added new_field column to books table';
    END IF;
END $$;
```

### Adding an Index
```sql
CREATE INDEX IF NOT EXISTS idx_books_new_field ON books(new_field);
```

### Complex Operations
```sql
DO $$
BEGIN
    -- Check if operation is needed
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'unique_constraint_name') THEN
        -- Perform operation
        ALTER TABLE books ADD CONSTRAINT unique_constraint_name UNIQUE (field1, field2);
        RAISE NOTICE 'Added unique constraint';
    END IF;
END $$;
```

## Troubleshooting

### Migration Failed
1. Check the error message in logs
2. Fix the issue in the migration file
3. Update the checksum or use `--force` if needed
4. Re-run the migration

### Migration Already Applied But Modified
```bash
# Force re-run if needed (be careful!)
python migrate.py --force 002_update_to_hnsw_index.sql
```

### Check Migration Status
```sql
-- Connect to database and check
SELECT * FROM migration_history ORDER BY executed_at;
```

## Environment Variables

Required environment variables:
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

## Production Checklist

Before deploying to production:

- [ ] ✅ All migrations tested in development
- [ ] ✅ Database backup created
- [ ] ✅ Migration runner tested
- [ ] ✅ Rollback plan prepared
- [ ] ✅ Application compatibility verified
- [ ] ✅ Performance impact assessed
- [ ] ✅ Team notified of deployment

## Security Notes

- **Never commit** production database URLs
- **Use environment variables** for credentials
- **Limit database permissions** for migration user
- **Audit migration changes** before production
- **Monitor migration execution** in production