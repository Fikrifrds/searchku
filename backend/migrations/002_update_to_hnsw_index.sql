-- Migration to update vector index from IVFFlat to HNSW for better performance
-- Drop the existing IVFFlat index
DROP INDEX IF EXISTS idx_pages_embedding_vector;

-- Create HNSW index for better vector search performance
-- HNSW provides better recall and performance for similarity search
CREATE INDEX idx_pages_embedding_vector_hnsw ON pages 
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Update any existing search functions to ensure they work with HNSW
-- The search functionality should automatically benefit from the new index