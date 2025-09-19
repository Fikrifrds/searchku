import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import Optional
from pathlib import Path
import logging
from PIL import Image
import io
from PyPDF2 import PdfReader
from docx import Document

logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.covers_dir = self.upload_dir / "covers"
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_image_types = {"image/jpeg", "image/png", "image/webp"}
        
        # Create directories if they don't exist
        self.covers_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_cover_image(self, file: UploadFile, book_id: str) -> Optional[str]:
        """
        Upload and process a book cover image.
        
        Args:
            file: The uploaded file
            book_id: The book ID to associate with the cover
            
        Returns:
            The file path/URL of the uploaded cover, or None if failed
        """
        try:
            # Validate file type
            if file.content_type not in self.allowed_image_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type. Allowed types: {', '.join(self.allowed_image_types)}"
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                )
            
            # Validate image
            try:
                image = Image.open(io.BytesIO(content))
                image.verify()  # Verify it's a valid image
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid image file"
                )
            
            # Generate unique filename
            file_extension = self._get_file_extension(file.content_type)
            filename = f"{book_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            file_path = self.covers_dir / filename
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            # Return relative path for URL generation
            return f"uploads/covers/{filename}"
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading cover image: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to upload cover image"
            )
    
    async def delete_cover_image(self, file_path: str) -> bool:
        """
        Delete a cover image file.
        
        Args:
            file_path: The file path to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if file_path and file_path.startswith("uploads/covers/"):
                full_path = Path(file_path)
                if full_path.exists():
                    full_path.unlink()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error deleting cover image {file_path}: {str(e)}")
            return False
    
    def _get_file_extension(self, content_type: str) -> str:
        """
        Get file extension based on content type.
        
        Args:
            content_type: The MIME type of the file
            
        Returns:
            File extension with dot
        """
        extensions = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp"
        }
        return extensions.get(content_type, ".jpg")
    
    def get_file_url(self, file_path: str, base_url: str = "http://localhost:8000") -> str:
        """
        Generate full URL for a file path.
        
        Args:
            file_path: The relative file path
            base_url: The base URL of the application
            
        Returns:
            Full URL to the file
        """
        if not file_path:
            return ""
        return f"{base_url.rstrip('/')}/{file_path}"
    
    async def _extract_text_from_file(self, content: bytes, content_type: str, filename: str) -> str:
        """
        Extract text from different file types.
        
        Args:
            content: The file content as bytes
            content_type: The MIME type of the file
            filename: The original filename
            
        Returns:
            Extracted text content
        """
        try:
            if content_type.startswith("text/"):
                # Handle text files
                try:
                    return content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        return content.decode('utf-8-sig')  # Try with BOM
                    except UnicodeDecodeError:
                        raise HTTPException(
                            status_code=400,
                            detail="File must be UTF-8 encoded"
                        )
            
            elif content_type == "application/pdf":
                # Handle PDF files
                try:
                    pdf_reader = PdfReader(io.BytesIO(content))
                    text_content = ""
                    for page in pdf_reader.pages:
                        text_content += page.extract_text() + "\n\n\n"
                    return text_content.strip()
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to extract text from PDF file"
                    )
            
            elif content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
                # Handle Word documents
                try:
                    doc = Document(io.BytesIO(content))
                    text_content = ""
                    for paragraph in doc.paragraphs:
                        if paragraph.text.strip():
                            text_content += paragraph.text + "\n"
                    return text_content.strip()
                except Exception as e:
                    logger.error(f"Error extracting text from Word document: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail="Failed to extract text from Word document"
                    )
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unsupported file type"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error extracting text from file {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to extract text from file"
            )
    
    async def process_bulk_text_upload(self, content: bytes, filename: str) -> list:
        """
        Process bulk text upload for pages. Supports .txt, .md, .pdf, .doc, and .docx files.
        
        Args:
            content: The file content as bytes
            filename: The original filename
            
        Returns:
            List of page data dictionaries with 'text' key
        """
        try:
            # Validate file size
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                )
            
            # Determine content type from filename
            content_type = self._get_content_type_from_filename(filename)
            
            # Extract text based on file type
            text_content = await self._extract_text_from_file(content, content_type, filename)
            
            # Split into pages (assuming pages are separated by triple newlines or page breaks)
            pages = []
            page_texts = text_content.split('\n\n\n')  # Triple newline as page separator
            
            for page_text in page_texts:
                cleaned_text = page_text.strip()
                if cleaned_text:  # Only add non-empty pages
                    pages.append({
                        'text': cleaned_text
                    })
            
            return pages
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing bulk text upload: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process file"
            )
    
    def _get_content_type_from_filename(self, filename: str) -> str:
        """
        Determine content type from filename extension.
        
        Args:
            filename: The filename
            
        Returns:
            MIME content type
        """
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        
        content_types = {
            'txt': 'text/plain',
            'md': 'text/markdown',
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        return content_types.get(extension, 'text/plain')

# Global instance
file_service = FileService()