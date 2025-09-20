-- Initial database schema
-- Creates the core tables for the SearchKu application

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Books table
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    language VARCHAR(10) DEFAULT 'ar',
    description TEXT,
    cover_image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pages table
CREATE TABLE IF NOT EXISTS pages (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    en_translation TEXT,
    id_translation TEXT,
    embedding_vector VECTOR(1536), -- Default to 1536 dimensions for pgvector compatibility
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-large',
    page_image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Foreign key constraint
ALTER TABLE pages
ADD CONSTRAINT fk_pages_book_id
FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE;

-- Unique constraint for page numbers within books
ALTER TABLE pages
ADD CONSTRAINT unique_book_page_number
UNIQUE (book_id, page_number);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_language ON books(language);
CREATE INDEX IF NOT EXISTS idx_books_created_at ON books(created_at);

CREATE INDEX IF NOT EXISTS idx_pages_book_id ON pages(book_id);
CREATE INDEX IF NOT EXISTS idx_pages_page_number ON pages(page_number);
CREATE INDEX IF NOT EXISTS idx_pages_embedding_model ON pages(embedding_model);
CREATE INDEX IF NOT EXISTS idx_pages_created_at ON pages(created_at);
CREATE INDEX IF NOT EXISTS idx_pages_page_image_url ON pages(page_image_url);

-- Basic vector index (will be upgraded to HNSW in next migration)
CREATE INDEX IF NOT EXISTS idx_pages_embedding_vector ON pages
USING ivfflat (embedding_vector vector_cosine_ops)
WITH (lists = 100);

-- Insert migration record
INSERT INTO migration_history (migration_name, description)
VALUES ('001_initial_schema.sql', 'Create initial database schema with books and pages tables')
ON CONFLICT (migration_name) DO NOTHING;