from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import routers
from .routers import books, pages, search, translation
from .database import engine
from .models import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    # Create database tables
    # Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    print("Shutting down...")

app = FastAPI(
    title="Digital Book Processing & Translation System",
    description="A system to digitize, process, and manage books with semantic search and translation support",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(books.router, prefix="/api/books", tags=["books"])
app.include_router(pages.router, prefix="/api", tags=["pages"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(translation.router, prefix="/api", tags=["translation"])

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Digital Book Processing System is running"}

@app.get("/")
async def root():
    return {"message": "Digital Book Processing & Translation System API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)