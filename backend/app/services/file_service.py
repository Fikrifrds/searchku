import os
import uuid
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import Optional
from pathlib import Path
import logging
from PIL import Image
import io

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
    
    async def process_bulk_text_upload(self, file: UploadFile) -> list:
        """
        Process bulk text upload for pages.
        
        Args:
            file: The uploaded text file
            
        Returns:
            List of page texts
        """
        try:
            # Validate file type
            if not file.content_type.startswith("text/"):
                raise HTTPException(
                    status_code=400,
                    detail="File must be a text file"
                )
            
            # Read file content
            content = await file.read()
            
            # Validate file size
            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
                )
            
            # Decode content
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    text_content = content.decode('utf-8-sig')  # Try with BOM
                except UnicodeDecodeError:
                    raise HTTPException(
                        status_code=400,
                        detail="File must be UTF-8 encoded"
                    )
            
            # Split into pages (assuming pages are separated by double newlines or page breaks)
            pages = []
            page_texts = text_content.split('\n\n\n')  # Triple newline as page separator
            
            for i, page_text in enumerate(page_texts, 1):
                cleaned_text = page_text.strip()
                if cleaned_text:  # Only add non-empty pages
                    pages.append({
                        'page_number': i,
                        'original_text': cleaned_text
                    })
            
            return pages
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing bulk text upload: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to process text file"
            )

# Global instance
file_service = FileService()