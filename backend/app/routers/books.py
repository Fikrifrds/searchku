from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.book import Book
from ..schemas.book import BookCreate, BookResponse
from ..services.file_service import file_service

router = APIRouter()

@router.post("/", response_model=BookResponse)
async def create_book(
    book: BookCreate,
    db: Session = Depends(get_db)
):
    """Create a new book."""
    try:
        db_book = Book(
            title=book.title,
            author=book.author,
            language=book.language,
            description=book.description,
            cover_image_url=book.cover_image_url
        )
        
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        
        return db_book
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create book: {str(e)}")

@router.post("/{book_id}/cover", response_model=dict)
async def upload_book_cover(
    book_id: int,
    cover_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a cover image for a book."""
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Upload the cover image
        cover_url = await file_service.upload_cover_image(book_id, cover_image)
        
        # Update book with cover URL
        book.cover_image_url = cover_url
        db.commit()
        
        return {
            "message": "Cover image uploaded successfully",
            "cover_url": cover_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload cover image: {str(e)}")

@router.delete("/{book_id}/cover", response_model=dict)
async def delete_book_cover(
    book_id: int,
    db: Session = Depends(get_db)
):
    """Delete a book's cover image."""
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        if book.cover_image_url:
            # Delete the cover image file
            await file_service.delete_cover_image(book_id)
            
            # Remove cover URL from book
            book.cover_image_url = None
            db.commit()
        
        return {"message": "Cover image deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete cover image: {str(e)}")

@router.get("/", response_model=List[BookResponse])
async def get_books(db: Session = Depends(get_db)):
    """Get all books."""
    books = db.query(Book).all()
    return books

@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book by ID."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.delete("/{book_id}")
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book and all its pages."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully"}