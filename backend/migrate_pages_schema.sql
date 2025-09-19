-- Migration script to update pages table schema
-- This script updates the existing pages table to match the Page model

-- Drop the old translated_text column if it exists
ALTER TABLE pages DROP COLUMN IF EXISTS translated_text;

-- Add the new translation columns
ALTER TABLE pages ADD COLUMN IF NOT EXISTS en_translation TEXT;
ALTER TABLE pages ADD COLUMN IF NOT EXISTS id_translation TEXT;

-- Update existing rows to have the default embedding_model if NULL
UPDATE pages SET embedding_model = 'text-embedding-3-small' WHERE embedding_model IS NULL;

-- Update embedding_model column to match the model definition
ALTER TABLE pages ALTER COLUMN embedding_model SET NOT NULL;
ALTER TABLE pages ALTER COLUMN embedding_model SET DEFAULT 'text-embedding-3-small';

-- Migration completed
SELECT 'Pages table schema migration completed successfully!' as result;