-- Migration to update vector index from IVFFlat to HNSW for better performance

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM migration_history WHERE migration_name = '003_update_to_hnsw_index.sql') THEN
        RAISE NOTICE 'Migration 003_update_to_hnsw_index.sql already applied, skipping...';
        RETURN;
    END IF;
END $$;

-- Drop the existing IVFFlat index
DROP INDEX IF EXISTS idx_pages_embedding_vector;

-- Create HNSW index for better vector search performance
-- HNSW provides better recall and performance for similarity search
CREATE INDEX idx_pages_embedding_vector_hnsw ON pages
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Update any existing search functions to ensure they work with HNSW
-- The search functionality should automatically benefit from the new index

-- Record this migration
INSERT INTO migration_history (migration_name, description)
VALUES ('003_update_to_hnsw_index.sql', 'Upgrade vector index from IVFFlat to HNSW for better performance')
ON CONFLICT (migration_name) DO NOTHING;