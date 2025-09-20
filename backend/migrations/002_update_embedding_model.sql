-- Update default embedding model to text-embedding-3-large

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM migration_history WHERE migration_name = '002_update_embedding_model.sql') THEN
        RAISE NOTICE 'Migration 002_update_embedding_model.sql already applied, skipping...';
        RETURN;
    END IF;
END $$;

-- Update the default value for embedding_model column
ALTER TABLE pages
ALTER COLUMN embedding_model SET DEFAULT 'text-embedding-3-large';

-- Optionally update existing NULL values to the new default
UPDATE pages
SET embedding_model = 'text-embedding-3-large'
WHERE embedding_model IS NULL;

-- Record this migration
INSERT INTO migration_history (migration_name, description)
VALUES ('002_update_embedding_model.sql', 'Update default embedding model to text-embedding-3-large')
ON CONFLICT (migration_name) DO NOTHING;