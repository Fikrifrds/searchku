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
import pytesseract
from pdf2image import convert_from_bytes
import fitz  # PyMuPDF

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
    
    async def _extract_text_with_ocr(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF using OCR (Optical Character Recognition).
        
        Args:
            pdf_content: The PDF file content as bytes
            
        Returns:
            Extracted text content from OCR
        """
        try:
            logger.info("Starting OCR text extraction...")
            
            # Convert PDF pages to images with higher DPI for better OCR
            images = convert_from_bytes(pdf_content, dpi=400, fmt='jpeg')
            logger.info(f"Converted PDF to {len(images)} images for OCR")
            
            text_content = ""
            
            # Process each page image with OCR
            for i, image in enumerate(images):
                try:
                    # Preprocess image for better OCR
                    # Convert to grayscale and enhance contrast
                    if image.mode != 'L':
                        image = image.convert('L')

                    # Enhance image for better OCR
                    from PIL import ImageEnhance, ImageFilter

                    # Enhance contrast
                    enhancer = ImageEnhance.Contrast(image)
                    image = enhancer.enhance(1.2)  # Moderate contrast enhancement

                    # Enhance sharpness for better character recognition
                    enhancer = ImageEnhance.Sharpness(image)
                    image = enhancer.enhance(1.5)

                    # Apply slight blur to reduce noise, then sharpen
                    image = image.filter(ImageFilter.MedianFilter(size=3))

                    # Resize image if it's too small (OCR works better on larger images)
                    width, height = image.size
                    if width < 1000 or height < 1000:
                        scale_factor = max(1000/width, 1000/height)
                        new_width = int(width * scale_factor)
                        new_height = int(height * scale_factor)
                        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                        logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

                    # Use pytesseract to extract text from image with Arabic language support
                    best_text = ""
                    best_length = 0

                    # Try multiple OCR configurations for Arabic text
                    ocr_configs = [
                        # Configuration 1: Single column with preserve_interword_spaces
                        (r'--oem 3 --psm 6 -l ara -c preserve_interword_spaces=1', "PSM 6 with spacing"),
                        # Configuration 2: Auto page segmentation with OSD
                        (r'--oem 3 --psm 1 -l ara -c preserve_interword_spaces=1', "PSM 1 with spacing"),
                        # Configuration 3: Treat as single text line
                        (r'--oem 3 --psm 7 -l ara -c preserve_interword_spaces=1', "PSM 7 single line"),
                        # Configuration 4: Single uniform block
                        (r'--oem 3 --psm 6 -l ara', "PSM 6 standard"),
                    ]

                    for config, desc in ocr_configs:
                        try:
                            logger.info(f"Trying OCR config for page {i+1}: {desc}")
                            page_text = pytesseract.image_to_string(image, config=config)
                            text_length = len(page_text.strip())
                            logger.info(f"{desc} extracted {text_length} characters")

                            # Keep the best result (most text extracted)
                            if text_length > best_length:
                                best_text = page_text
                                best_length = text_length
                                logger.info(f"New best result with {desc}: {text_length} characters")

                            # If we got substantial text, we can stop trying
                            if text_length > 100:
                                logger.info(f"Good result achieved with {desc}, stopping further attempts")
                                break

                        except Exception as e:
                            logger.warning(f"OCR config '{desc}' failed for page {i+1}: {str(e)}")
                            continue

                    page_text = best_text
                    logger.info(f"Final OCR page {i+1} result: {len(page_text)} characters")

                    # Log a sample of the text for debugging
                    if page_text.strip():
                        sample = page_text.strip()[:200]
                        logger.info(f"Page {i+1} sample text: {sample}...")

                        # Clean up common OCR issues in Arabic text
                        page_text = self._clean_arabic_ocr_text(page_text)
                    
                    if page_text.strip():
                        text_content += page_text + "\n\n\n"
                    else:
                        logger.warning(f"OCR page {i+1} has no extractable text")
                        
                except Exception as e:
                    logger.error(f"Error processing OCR for page {i+1}: {str(e)}")
                    continue
            
            logger.info(f"OCR completed. Total extracted text length: {len(text_content)}")
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"Error during OCR text extraction: {str(e)}")
            return ""

    def _clean_arabic_ocr_text(self, text: str) -> str:
        """
        Clean up common OCR issues in Arabic text.

        Args:
            text: Raw OCR text

        Returns:
            Cleaned Arabic text
        """
        if not text:
            return text

        try:
            import re

            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)

            # Fix common Arabic OCR character confusions
            # These are common misreadings by OCR engines
            corrections = {
                'ء': 'أ',  # Hamza corrections
                'ﻷ': 'لا',  # Lam-Alif
                'ﻻ': 'لا',  # Lam-Alif variants
                'ﻼ': 'لا',
                '،': '،',  # Arabic comma
                '؟': '؟',  # Arabic question mark
                '؛': '؛',  # Arabic semicolon
            }

            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)

            # Remove isolated diacritics that might have been misread
            text = re.sub(r'[\u064B-\u065F\u0670\u0640]', '', text)

            # Clean up line breaks - preserve paragraph structure
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
            text = re.sub(r'\n\s+', '\n', text)  # Remove spaces after newlines

            # Remove any remaining non-Arabic, non-ASCII characters that don't belong
            # Keep Arabic letters, numbers, punctuation, and basic ASCII
            text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\s\d\.,;:!?()\[\]{}"\'-]', '', text)

            return text.strip()

        except Exception as e:
            logger.warning(f"Error cleaning Arabic OCR text: {str(e)}")
            return text

    async def _extract_text_with_pymupdf(self, content: bytes) -> str:
        """
        Extract text from PDF using PyMuPDF, which often works better with Arabic text.

        Args:
            content: The PDF file content as bytes

        Returns:
            Extracted text content from PyMuPDF
        """
        try:
            logger.info("Starting PyMuPDF text extraction...")

            # Open PDF with PyMuPDF
            pdf_document = fitz.open(stream=content, filetype="pdf")
            logger.info(f"PyMuPDF opened PDF with {pdf_document.page_count} pages")

            text_content = ""

            # Extract text from each page
            for page_num in range(pdf_document.page_count):
                try:
                    page = pdf_document[page_num]
                    page_text = page.get_text()
                    logger.info(f"PyMuPDF page {page_num+1} extracted {len(page_text)} characters")

                    if page_text.strip():
                        text_content += page_text + "\n\n\n"
                        logger.info(f"PyMuPDF page {page_num+1} sample: {page_text[:100]}...")
                    else:
                        logger.warning(f"PyMuPDF page {page_num+1} has no extractable text")

                except Exception as e:
                    logger.error(f"PyMuPDF error processing page {page_num+1}: {str(e)}")
                    continue

            pdf_document.close()
            logger.info(f"PyMuPDF completed. Total extracted text length: {len(text_content)}")
            return text_content.strip()

        except Exception as e:
            logger.error(f"Error during PyMuPDF text extraction: {str(e)}")
            return ""

    async def _extract_text_from_file(self, content: bytes, content_type: str, filename: str, use_ocr: bool = False) -> str:
        """
        Extract text from different file types.

        Args:
            content: The file content as bytes
            content_type: The MIME type of the file
            filename: The original filename
            use_ocr: Whether to use OCR for scanned PDFs (default: False)

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
                # Handle PDF files with OCR fallback
                try:
                    logger.info("Starting PDF text extraction...")
                    pdf_bytes = io.BytesIO(content)
                    pdf_reader = PdfReader(pdf_bytes)
                    logger.info(f"PDF successfully loaded with {len(pdf_reader.pages)} pages")

                    # Check if PDF is encrypted
                    if pdf_reader.is_encrypted:
                        logger.warning("PDF is encrypted, attempting to decrypt...")
                        try:
                            pdf_reader.decrypt("")  # Try with empty password
                        except Exception as decrypt_error:
                            logger.error(f"Failed to decrypt PDF: {str(decrypt_error)}")
                            raise HTTPException(
                                status_code=400,
                                detail="PDF is password protected and cannot be processed"
                            )
                    text_content = ""

                    # First try PyPDF2 text extraction with better encoding handling
                    for i, page in enumerate(pdf_reader.pages):
                        try:
                            logger.info(f"Processing page {i+1}...")
                            page_text = page.extract_text()
                            logger.info(f"Raw page text length: {len(page_text) if page_text else 0}")

                            # Clean up potential encoding issues
                            if page_text:
                                # Try to handle potential encoding issues with Arabic text
                                page_text = page_text.encode('utf-8', errors='ignore').decode('utf-8')
                                logger.info(f"Page {i+1} after encoding cleanup: {len(page_text)} characters")
                                # Log first 100 characters for debugging
                                if page_text.strip():
                                    logger.info(f"Page {i+1} sample text: {page_text[:100]}...")

                            if page_text and page_text.strip():
                                text_content += page_text + "\n\n\n"
                                logger.info(f"Page {i+1} added to content")
                            else:
                                logger.warning(f"Page {i+1} has no extractable text")
                        except Exception as e:
                            logger.error(f"Error extracting text from page {i+1}: {str(e)}")
                            logger.error(f"Page {i+1} error type: {type(e).__name__}")
                            continue

                    logger.info(f"Total extracted text length with PyPDF2: {len(text_content)}")
                    if text_content.strip():
                        logger.info(f"Sample of extracted text: {text_content[:200]}...")

                    # If no text was extracted with PyPDF2, try PyMuPDF
                    if not text_content.strip():
                        logger.info("No text extracted with PyPDF2, trying PyMuPDF...")
                        text_content = await self._extract_text_with_pymupdf(content)
                        logger.info(f"PyMuPDF extracted text length: {len(text_content)}")

                    # If still no text and OCR is enabled, try OCR
                    if not text_content.strip() and use_ocr:
                        logger.info("No text extracted with PDF libraries, attempting OCR...")
                        text_content = await self._extract_text_with_ocr(content)
                        logger.info(f"OCR extracted text length: {len(text_content)}")

                    if not text_content.strip():
                        if use_ocr:
                            logger.error("No text could be extracted from PDF even with OCR")
                            raise HTTPException(
                                status_code=400,
                                detail="No text could be extracted from PDF. The file might be corrupted or contain no readable content."
                            )
                        else:
                            logger.error("No text could be extracted from PDF. Try enabling OCR for scanned documents.")
                            raise HTTPException(
                                status_code=400,
                                detail="No text could be extracted from PDF. This might be a scanned document - try enabling OCR option."
                            )

                    return text_content.strip()
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Error extracting text from PDF: {str(e)}")
                    logger.error(f"PDF extraction error type: {type(e).__name__}")
                    import traceback
                    logger.error(f"PDF extraction traceback: {traceback.format_exc()}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Failed to extract text from PDF file: {str(e)}"
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
    
    async def process_bulk_text_upload(self, content: bytes, filename: str, use_ocr: bool = False) -> list:
        """
        Process bulk text upload for pages. Supports .txt, .md, .pdf, .doc, and .docx files.

        Args:
            content: The file content as bytes
            filename: The original filename
            use_ocr: Whether to use OCR for scanned PDFs (default: False)

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
            logger.info(f"Processing file {filename} with content type: {content_type}")
            
            # Extract text based on file type
            text_content = await self._extract_text_from_file(content, content_type, filename, use_ocr)
            logger.info(f"Extracted text length: {len(text_content)} characters")
            
            # Split into pages based on file type
            pages = []
            
            if content_type == "application/pdf":
                # For PDFs, split by the triple newlines we added during extraction
                page_texts = text_content.split('\n\n\n')
                logger.info(f"PDF split into {len(page_texts)} potential pages")
            else:
                # For other text files, use different strategies
                if '\n\n\n' in text_content:
                    # If triple newlines exist, use them
                    page_texts = text_content.split('\n\n\n')
                elif '\f' in text_content:  # Form feed character (page break)
                    page_texts = text_content.split('\f')
                else:
                    # Split by double newlines or create chunks of reasonable size
                    if '\n\n' in text_content:
                        page_texts = text_content.split('\n\n')
                    else:
                        # Create chunks of ~1000 characters
                        chunk_size = 1000
                        page_texts = [text_content[i:i+chunk_size] for i in range(0, len(text_content), chunk_size)]
                
                logger.info(f"Text file split into {len(page_texts)} potential pages")
            
            # Process each page
            for i, page_text in enumerate(page_texts):
                cleaned_text = page_text.strip()
                if cleaned_text and len(cleaned_text) > 10:  # Only add pages with substantial content
                    pages.append({
                        'text': cleaned_text
                    })
                    logger.debug(f"Added page {i+1} with {len(cleaned_text)} characters")
                else:
                    logger.debug(f"Skipped page {i+1} - too short or empty")
            
            logger.info(f"Final result: {len(pages)} pages created from {filename}")
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