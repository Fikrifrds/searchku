from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.page import Page
from ..models.book import Book
from ..schemas.page import PageCreate, PageResponse, PageUpdate
from ..services.embedding_service import embedding_service

router = APIRouter()

@router.post("/books/{book_id}/pages", response_model=PageResponse)
async def create_page(
    book_id: int,
    page_data: PageCreate,
    db: Session = Depends(get_db)
):
    """Create a new page for a book with embedding generation."""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if page number already exists for this book
    existing_page = db.query(Page).filter(
        Page.book_id == book_id,
        Page.page_number == page_data.page_number
    ).first()
    if existing_page:
        raise HTTPException(status_code=400, detail="Page number already exists for this book")
    
    # Generate embedding for the original text
    embedding_vector = None
    if page_data.original_text:
        embedding_vector = await embedding_service.generate_embedding(page_data.original_text)
    
    db_page = Page(
        book_id=book_id,
        page_number=page_data.page_number,
        original_text=page_data.original_text,
        embedding_model=embedding_service.model_name,
        embedding_vector=embedding_vector
    )
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

@router.get("/books/{book_id}/pages", response_model=List[PageResponse])
async def get_book_pages(book_id: int, db: Session = Depends(get_db)):
    """Get all pages for a specific book."""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    pages = db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number).all()
    return pages

@router.get("/books/{book_id}/pages/{page_number}", response_model=PageResponse)
async def get_page(
    book_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Get a specific page by book ID and page number."""
    page = db.query(Page).filter(
        Page.book_id == book_id,
        Page.page_number == page_number
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

@router.patch("/books/{book_id}/pages/{page_number}", response_model=PageResponse)
async def update_page_translations(
    book_id: int,
    page_number: int,
    page_update: PageUpdate,
    db: Session = Depends(get_db)
):
    """Update translations for a specific page."""
    page = db.query(Page).filter(
        Page.book_id == book_id,
        Page.page_number == page_number
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if page_update.en_translation is not None:
        page.en_translation = page_update.en_translation
    if page_update.id_translation is not None:
        page.id_translation = page_update.id_translation
    
    db.commit()
    db.refresh(page)
    return page

@router.put("/books/{book_id}/pages/{page_number}", response_model=PageResponse)
async def update_page(
    book_id: int,
    page_number: int,
    page_data: PageUpdate,
    db: Session = Depends(get_db)
):
    """Update a page's content and regenerate embedding if text changes."""
    page = db.query(Page).filter(
        Page.book_id == book_id,
        Page.page_number == page_number
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # Update fields if provided
    if page_data.original_text is not None:
        page.original_text = page_data.original_text
        # Regenerate embedding when original_text changes
        if page_data.original_text:
            embedding_vector = await embedding_service.generate_embedding(page_data.original_text)
            page.embedding_vector = embedding_vector
            page.embedding_model = embedding_service.model_name
        else:
            page.embedding_vector = None
    
    if page_data.en_translation is not None:
        page.en_translation = page_data.en_translation
    
    if page_data.id_translation is not None:
        page.id_translation = page_data.id_translation
    
    try:
        db.commit()
        db.refresh(page)
        return page
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update page: {str(e)}")

@router.delete("/books/{book_id}/pages/{page_number}")
async def delete_page(
    book_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Delete a specific page."""
    page = db.query(Page).filter(
        Page.book_id == book_id,
        Page.page_number == page_number
    ).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    db.delete(page)
    db.commit()
    return {"message": "Page deleted successfully"}