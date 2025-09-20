-- Create migration tracking table
-- This table keeps track of which migrations have been applied

CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    checksum VARCHAR(64),
    description TEXT
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_migration_history_name ON migration_history(migration_name);
CREATE INDEX IF NOT EXISTS idx_migration_history_executed_at ON migration_history(executed_at);

-- Insert this migration into the history
INSERT INTO migration_history (migration_name, description, execution_time_ms)
VALUES ('000_create_migration_table.sql', 'Create migration tracking table', 0)
ON CONFLICT (migration_name) DO NOTHING;