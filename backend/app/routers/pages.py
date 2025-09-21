from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models.page import Page
from ..models.book import Book
from ..schemas.page import PageCreate, PageResponse, PageUpdate
from ..services.embedding_service import embedding_service
from ..services.file_service import file_service
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        embedding_vector = await embedding_service.generate_embedding(page_data.original_text, task_type="RETRIEVAL_DOCUMENT")

    # Ensure embedding_vector is properly formatted for pgvector
    formatted_embedding = None
    if embedding_vector is not None:
        if isinstance(embedding_vector, (list, tuple)):
            # Convert to list of floats to ensure proper format
            try:
                formatted_embedding = [float(x) for x in embedding_vector]
                logger.info(f"Converted embedding vector to list of {len(formatted_embedding)} floats")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert embedding vector to floats: {str(e)}")
                formatted_embedding = None
        else:
            logger.error(f"Embedding vector is not a list/tuple: {type(embedding_vector)} - {embedding_vector}")
            formatted_embedding = None

    db_page = Page(
        book_id=book_id,
        page_number=page_data.page_number,
        original_text=page_data.original_text,
        embedding_model=embedding_service.model,
        embedding_vector=formatted_embedding
    )
    db.add(db_page)
    db.commit()
    db.refresh(db_page)

    # Set as book cover if this is the first page and book doesn't have a cover
    if db_page.page_number == 1 and not book.cover_image_url and db_page.page_image_url:
        book.cover_image_url = db_page.page_image_url
        db.commit()
        logger.info(f"Set book cover image from first page: {db_page.page_image_url}")

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
            embedding_vector = await embedding_service.generate_embedding(page_data.original_text, task_type="RETRIEVAL_DOCUMENT")
            # Ensure embedding_vector is properly formatted for pgvector
            formatted_embedding = None
            if embedding_vector is not None:
                if isinstance(embedding_vector, (list, tuple)):
                    # Convert to list of floats to ensure proper format
                    try:
                        formatted_embedding = [float(x) for x in embedding_vector]
                        logger.info(f"Converted embedding vector to list of {len(formatted_embedding)} floats")
                    except (ValueError, TypeError) as e:
                        logger.error(f"Failed to convert embedding vector to floats: {str(e)}")
                        formatted_embedding = None
                else:
                    logger.error(f"Embedding vector is not a list/tuple: {type(embedding_vector)} - {embedding_vector}")
                    formatted_embedding = None
            page.embedding_vector = formatted_embedding
            page.embedding_model = embedding_service.model
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

@router.post("/books/{book_id}/upload-files")
async def upload_files_bulk(
    book_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process multiple files (PDF, DOC, DOCX) for a book.

    This endpoint:
    1. Validates the book exists
    2. Processes each uploaded file to extract text
    3. Automatically detects which pages need OCR (image-only pages)
    4. Uses text extraction for pages with extractable text
    5. Uses OCR for image-only pages
    6. Splits content into pages
    7. Generates embeddings for each page
    8. Stores pages with embeddings in the database

    Args:
        book_id: ID of the book to add pages to
        files: List of files to upload and process
    """
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    results = []
    
    for file in files:
        try:
            logger.info(f"Processing file: {file.filename}")
            logger.info(f"File size: {file.size if hasattr(file, 'size') else 'unknown'} bytes")
            logger.info(f"Content type: {file.content_type}")
            
            # Validate file type
            allowed_types = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                           'text/plain']
            
            if file.content_type not in allowed_types:
                logger.warning(f"Unsupported file type: {file.content_type} for file: {file.filename}")
                results.append({
                    "filename": file.filename,
                    "status": "error",
                    "message": f"Unsupported file type: {file.content_type}"
                })
                continue
            
            # Read file content
            file_content = await file.read()
            logger.info(f"File content read successfully, size: {len(file_content)} bytes")
            
            # Process file using file service with automatic OCR detection
            logger.info(f"Starting intelligent text extraction for: {file.filename}")
            page_data_list = await file_service.process_bulk_text_upload(
                file_content, file.filename, book_id
            )
            logger.info(f"Text extraction completed. Pages found: {len(page_data_list)}")
            
            # Log extracted page data
            for i, page_data in enumerate(page_data_list):
                text_length = len(page_data.get('text', '')) if page_data.get('text') else 0
                logger.info(f"Page {i+1}: text_length={text_length}")
                if text_length > 0:
                    logger.info(f"Page {i+1} preview: {page_data.get('text', '')[:100]}...")
            
            # Get the current highest page number for this book
            last_page = db.query(Page).filter(Page.book_id == book_id).order_by(Page.page_number.desc()).first()
            next_page_number = (last_page.page_number + 1) if last_page else 1
            logger.info(f"Starting page creation from page number: {next_page_number}")
            
            pages_created = []
            
            for i, page_data in enumerate(page_data_list):
                current_page_number = next_page_number + i
                logger.info(f"Creating page {current_page_number} for book {book_id}")
                
                # Generate embedding for the page text
                embedding_vector = None
                if page_data.get('text'):
                    logger.info(f"Generating embedding for page {current_page_number}")
                    try:
                        embedding_vector = await embedding_service.generate_embedding(page_data['text'], task_type="RETRIEVAL_DOCUMENT")
                        logger.info(f"Embedding generated successfully for page {current_page_number}")
                        logger.debug(f"Embedding type: {type(embedding_vector)}, length: {len(embedding_vector) if embedding_vector else 'None'}")
                        if embedding_vector and len(embedding_vector) > 0:
                            logger.debug(f"First few elements: {embedding_vector[:3] if len(embedding_vector) >= 3 else embedding_vector}")
                    except Exception as e:
                        logger.error(f"Failed to generate embedding for page {current_page_number}: {str(e)}")
                        raise e
                else:
                    logger.warning(f"No text found for page {current_page_number}, skipping embedding")
                
                # Create page in database
                logger.info(f"Saving page {current_page_number} to database")

                # Ensure embedding_vector is properly formatted for pgvector
                formatted_embedding = None
                if embedding_vector is not None:
                    logger.debug(f"Processing embedding vector of type: {type(embedding_vector)}")

                    # Handle string representations
                    if isinstance(embedding_vector, str):
                        logger.warning(f"Embedding vector is a string, attempting to parse: {embedding_vector[:100]}...")
                        try:
                            import json
                            embedding_vector = json.loads(embedding_vector)
                            logger.info("Successfully parsed string embedding to list")
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse string embedding: {str(e)}")
                            formatted_embedding = None

                    if isinstance(embedding_vector, (list, tuple)):
                        # Convert to list of floats to ensure proper format
                        try:
                            formatted_embedding = [float(x) for x in embedding_vector]
                            logger.info(f"Converted embedding vector to list of {len(formatted_embedding)} floats")
                            logger.debug(f"Sample values: {formatted_embedding[:3] if len(formatted_embedding) >= 3 else formatted_embedding}")
                        except (ValueError, TypeError) as e:
                            logger.error(f"Failed to convert embedding vector to floats: {str(e)}")
                            logger.error(f"Problematic data: {embedding_vector[:5] if hasattr(embedding_vector, '__getitem__') else embedding_vector}")
                            formatted_embedding = None
                    else:
                        logger.error(f"Embedding vector is not a list/tuple/string: {type(embedding_vector)}")
                        logger.error(f"Value: {str(embedding_vector)[:200]}...")
                        formatted_embedding = None

                db_page = Page(
                    book_id=book_id,
                    page_number=current_page_number,
                    original_text=page_data.get('text', ''),
                    embedding_model=embedding_service.model,
                    embedding_vector=formatted_embedding,
                    page_image_url=page_data.get('page_image_url')
                )

                db.add(db_page)
                pages_created.append({
                    "page_number": current_page_number,
                    "text_length": len(page_data.get('text', ''))
                })
                logger.info(f"Page {current_page_number} added to session")
            
            logger.info(f"Committing {len(pages_created)} pages to database")
            try:
                db.commit()
                logger.info(f"Successfully committed {len(pages_created)} pages to database")

                # Set the first page image as book cover if book doesn't have a cover yet
                if pages_created and not book.cover_image_url:
                    first_page = db.query(Page).filter(
                        Page.book_id == book_id,
                        Page.page_number == next_page_number
                    ).first()

                    if first_page and first_page.page_image_url:
                        book.cover_image_url = first_page.page_image_url
                        db.commit()
                        logger.info(f"Set book cover image from first page: {first_page.page_image_url}")

            except Exception as commit_error:
                logger.error(f"Error committing pages to database: {str(commit_error)}")
                logger.error(f"Commit error type: {type(commit_error).__name__}")
                db.rollback()
                raise commit_error
            
            results.append({
                "filename": file.filename,
                "status": "success",
                "pages_created": len(pages_created),
                "pages": pages_created
            })
            logger.info(f"Successfully processed file: {file.filename}, created {len(pages_created)} pages")
            
        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            db.rollback()
            results.append({
                "filename": file.filename,
                "status": "error",
                "message": str(e)
            })
    
    logger.info(f"Upload processing completed. Total files processed: {len(files)}")
    logger.info(f"Results summary: {results}")
    return {
        "message": "File upload processing completed",
        "results": results
    }