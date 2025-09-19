-- Initialize SearchKu Database
-- This script creates the database schema with pgvector extension for semantic search

-- Enable pgvector extension for vector operations
CREATE EXTENSION IF NOT EXISTS vector;

-- Create books table
CREATE TABLE IF NOT EXISTS books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255) NOT NULL,
    description TEXT,
    cover_image_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create pages table with vector column for embeddings
CREATE TABLE IF NOT EXISTS pages (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    en_translation TEXT,
    id_translation TEXT,
    embedding_vector vector(1536), -- OpenAI text-embedding-3-small dimension
    embedding_model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(book_id, page_number)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pages_book_id ON pages(book_id);
CREATE INDEX IF NOT EXISTS idx_pages_page_number ON pages(page_number);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);

-- Create vector similarity index for semantic search using HNSW for better performance
CREATE INDEX IF NOT EXISTS idx_pages_embedding_vector ON pages 
USING hnsw (embedding_vector vector_cosine_ops) WITH (m = 16, ef_construction = 64);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_books_updated_at BEFORE UPDATE ON books
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pages_updated_at BEFORE UPDATE ON pages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO books (title, author, description) VALUES 
('The Great Gatsby', 'F. Scott Fitzgerald', 'A classic American novel set in the Jazz Age'),
('To Kill a Mockingbird', 'Harper Lee', 'A gripping tale of racial injustice and childhood innocence'),
('1984', 'George Orwell', 'A dystopian social science fiction novel')
ON CONFLICT DO NOTHING;

-- Insert sample pages
INSERT INTO pages (book_id, page_number, original_text) VALUES 
(1, 1, 'In my younger and more vulnerable years my father gave me some advice that I have carried with me ever since.'),
(1, 2, 'Whenever you feel like criticizing anyone, he told me, just remember that all the people in this world have not had the advantages that you have had.'),
(2, 1, 'When I was almost six years old, I heard my parents talking about something that happened in Maycomb.'),
(2, 2, 'They said a man named Tom Robinson had been accused of something terrible.'),
(3, 1, 'It was a bright cold day in April, and the clocks were striking thirteen.'),
(3, 2, 'Winston Smith, his chin nuzzled into his breast in an effort to escape the vile wind, slipped quickly through the glass doors of Victory Mansions.')
ON CONFLICT (book_id, page_number) DO NOTHING;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;

PRINT 'Database initialization completed successfully!';