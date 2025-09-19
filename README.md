# SearchKu - Digital Book Processing and Semantic Search Platform

SearchKu is an intelligent digital book processing and search platform that enables users to upload, manage, and semantically search through their digital book collections using advanced AI-powered embeddings.

## Features

### 🔍 **Semantic Search**
- AI-powered semantic search using OpenAI embeddings
- Find content by meaning, not just keywords
- Fallback to traditional text search
- Search across all books or within specific books

### 📚 **Book Management**
- Create and organize digital books
- Upload cover images
- Add book metadata (title, author, description)
- View book details and pages

### 📄 **Page Management**
- Add individual pages to books
- Bulk text processing and upload
- Automatic embedding generation for semantic search
- Translation support (original and translated text)

### 🎨 **Modern UI**
- Clean, responsive React interface
- Tailwind CSS styling
- Mobile-friendly design
- Real-time search results

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database with pgvector extension
- **SQLAlchemy** - ORM for database operations
- **OpenAI API** - For generating text embeddings
- **Pydantic** - Data validation and serialization

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Zustand** - State management
- **Lucide React** - Icon library

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **pgvector** - PostgreSQL extension for vector similarity search

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (for semantic search)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd searchku
```

### 2. Configure Environment
```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit backend/.env and add your OpenAI API key
# Replace 'your_openai_api_key_here' with your actual API key
```

### 3. Start the Application
```bash
# Use the startup script (recommended)
./start.sh

# Or manually with Docker Compose
docker-compose up -d
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Manual Setup (Development)

### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Start the server
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Database Setup
```bash
# Start PostgreSQL with pgvector
docker run -d \
  --name searchku_postgres \
  -e POSTGRES_DB=searchku \
  -e POSTGRES_USER=searchku_user \
  -e POSTGRES_PASSWORD=searchku_password \
  -p 5432:5432 \
  -v $(pwd)/backend/init_db.sql:/docker-entrypoint-initdb.d/init_db.sql \
  pgvector/pgvector:pg15
```

## API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Books
- `GET /api/books` - List all books
- `POST /api/books` - Create a new book
- `GET /api/books/{id}` - Get book details
- `PUT /api/books/{id}` - Update book
- `DELETE /api/books/{id}` - Delete book
- `POST /api/books/{id}/cover` - Upload cover image

#### Pages
- `GET /api/books/{book_id}/pages` - List book pages
- `POST /api/books/{book_id}/pages` - Create a new page
- `PUT /api/books/{book_id}/pages/{page_number}` - Update page
- `DELETE /api/books/{book_id}/pages/{page_number}` - Delete page

#### Search
- `GET /api/search/semantic` - Semantic search
- `GET /api/search/text` - Text search
- `GET /api/search/similar/{page_id}` - Find similar pages

## Usage Guide

### 1. Create Your First Book
1. Navigate to the Books page
2. Click "Create New Book"
3. Fill in the book details (title, author, description)
4. Optionally upload a cover image

### 2. Add Pages
1. Open the book detail page
2. Click "Add New Page"
3. Enter the page content
4. The system will automatically generate embeddings for semantic search

### 3. Bulk Upload
1. Go to the Upload page
2. Select a book or create a new one
3. Upload text files or paste content
4. The system will split content into pages and process embeddings

### 4. Search Content
1. Use the Search page
2. Choose between semantic or text search
3. Optionally filter by specific books
4. View results with highlighted snippets

## Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL=postgresql://searchku_user:searchku_password@localhost:5432/searchku

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Application
DEBUG=True
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000
```

## Development

### Project Structure
```
searchku/
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── lib/            # Utilities and API client
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

### Adding New Features

1. **Backend**: Add new endpoints in `backend/app/routers/`
2. **Frontend**: Create new pages in `frontend/src/pages/`
3. **Database**: Update models in `backend/app/models/`
4. **Services**: Add business logic in `backend/app/services/`

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Troubleshooting

### Common Issues

1. **OpenAI API Key Error**
   - Ensure your API key is correctly set in `backend/.env`
   - Check that you have sufficient OpenAI credits

2. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in environment variables

3. **Frontend Can't Connect to Backend**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend configuration

4. **Docker Issues**
   - Run `docker-compose down` and `docker-compose up -d` to restart
   - Check logs with `docker-compose logs -f`

### Useful Commands

```bash
# View application logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Access database
docker-compose exec postgres psql -U searchku_user -d searchku

# Rebuild containers
docker-compose build --no-cache
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the API documentation at http://localhost:8000/docs
- Review the troubleshooting section above
- Open an issue on the repository

---

**Happy searching with SearchKu! 🔍📚**