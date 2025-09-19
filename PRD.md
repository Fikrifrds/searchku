📘 Product Requirements Document (PRD)

Product Name: Digital Book Processing & Translation System
Version: v1.0
Owner: lcdt
Date: Sept 2025

1. Overview

A system to digitize, process, and manage books with support for:

Storing book metadata & cover (first page as image).

Storing book pages with original text, embeddings, optional translations (EN & ID).

Search & semantic analysis using embeddings.

Extensible to multiple embedding models.

API-based separation between backend & frontend, but developed in one monorepo.

2. Goals & Non-Goals
Goals

Enable structured storage of books, pages, and metadata.

Support multilingual (Arabic source, English/Indonesian translations).

Support embeddings for semantic search.

Provide a clean frontend for viewing, searching, and managing books.

Store embedding model metadata (since models can change later).

Non-Goals

No OCR support (assume input text is already digitized).

No real-time translation engine in v1 (translations optional, filled later).

No offline desktop app (only web).

3. System Architecture

Monorepo with /backend and /frontend.

Backend: REST API (Python FastAPI / Node NestJS — TBD).

Frontend: React + Tailwind (API-based, no DB access).

Database: PostgreSQL (with pgvector for embeddings).

Storage: Object storage (S3-compatible) for cover images.

Embeddings: OpenAI or local (pluggable).

Deployment: Docker + Docker Compose, easy migration to Kubernetes later.

4. Backend Requirements
4.1 Entities & Schema
Books

id (UUID, PK)

title (string, required)

author (string, optional)

language (string, e.g., "ar")

cover_image_url (string, S3 path)

created_at (timestamp)

updated_at (timestamp)

Pages

id (UUID, PK)

book_id (FK → books.id)

page_number (int, required)

original_text (text, required)

embedding_vector (vector, pgvector)

embedding_model (string, required → e.g., text-embedding-3-small)

en_translation (text, optional)

id_translation (text, optional)

created_at (timestamp)

updated_at (timestamp)

4.2 API Endpoints
Books

POST /books → create book (metadata + cover upload).

GET /books → list all books.

GET /books/:id → fetch book details + cover.

DELETE /books/:id → delete book (cascade pages).

Pages

POST /books/:id/pages → upload page text (auto-generate embedding).

GET /books/:id/pages → list all pages with optional translations.

GET /books/:id/pages/:page_number → fetch specific page.

PATCH /books/:id/pages/:page_number → update translations.

DELETE /books/:id/pages/:page_number → delete page.

Search

POST /search → semantic search across pages (query → embedding → similarity search).

4.3 Services

Embedding Service: abstracted to allow different models later.

Storage Service: handles book cover images.

Search Service: semantic search with pgvector.

5. Frontend Requirements
5.1 Roles

Admin/User (same in v1)

5.2 Features
Books Management

Upload book metadata (title, author, language).

Upload cover (first page image).

View book list with covers.

Delete book.

Pages Management

Upload new pages (with text).

View pages with original text + optional translations.

Edit/add EN & ID translations later.

Show which embedding model was used.

Search

Search across pages (semantic search).

Show result with snippet & highlight.

5.3 UI Components

Books Page

Grid/list of books (cover + title).

“Add New Book” form.

Book Detail Page

Cover + metadata.

Pages list (sortable by page number).

Add/edit translation.

Page Detail Modal

Original text.

EN translation (editable).

ID translation (editable).

Embedding model used (readonly).

Search Page

Search bar.

Result list (page snippet + link to book/page).

6. Infra & DevOps

Monorepo:

/backend
/frontend
/shared (optional utils/types)
/docs
docker-compose.yml


CI/CD: GitHub Actions (tests + deploy).

Deployment: Docker Compose (local), Kubernetes (production-ready).

Monitoring: basic logging + error tracking (Sentry).

7. Future Considerations

Role-based access (multi-user).

OCR pipeline for scanned books.

More translation languages.

Fine-tuned local embedding models (for cost reduction).

Mobile-friendly PWA frontend.

✅ With this PRD, you can start implementing both backend and frontend in one monorepo, while keeping the separation clean through APIs.