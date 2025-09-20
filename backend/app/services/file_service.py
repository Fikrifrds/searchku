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

    async def _extract_text_from_file(self, content: bytes, content_type: str, filename: str) -> str:
        """
        Extract text from different file types (non-PDF files).

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

    async def _process_pdf_with_smart_ocr(self, content: bytes, filename: str) -> list:
        """
        Process PDF with intelligent OCR detection per page.
        Uses text extraction for readable pages and OCR for image-only pages.

        Args:
            content: The PDF file content as bytes
            filename: The original filename

        Returns:
            List of page data dictionaries with 'text' and 'extraction_method' keys
        """
        try:
            logger.info(f"Starting intelligent PDF processing for: {filename}")
            pages = []

            # Open PDF with PyMuPDF for better page handling
            pdf_document = fitz.open(stream=content, filetype="pdf")
            logger.info(f"PDF opened with {pdf_document.page_count} pages")

            # Check if PDF is encrypted
            if pdf_document.needs_pass:
                logger.warning("PDF is encrypted, attempting to decrypt...")
                try:
                    pdf_document.authenticate("")  # Try with empty password
                except Exception as decrypt_error:
                    logger.error(f"Failed to decrypt PDF: {str(decrypt_error)}")
                    pdf_document.close()
                    raise HTTPException(
                        status_code=400,
                        detail="PDF is password protected and cannot be processed"
                    )

            # Process each page individually
            for page_num in range(pdf_document.page_count):
                try:
                    logger.info(f"Processing page {page_num + 1}/{pdf_document.page_count}")
                    page = pdf_document[page_num]

                    # First, try to extract text using PyMuPDF
                    page_text = page.get_text()
                    text_length = len(page_text.strip()) if page_text else 0

                    # Determine if the page has meaningful text
                    # Consider a page to have text if it has more than 50 characters of non-whitespace content
                    has_meaningful_text = text_length > 50

                    # Also check for common non-text content indicators
                    if has_meaningful_text:
                        # Remove common PDF artifacts and see if substantial text remains
                        cleaned_text = page_text.strip()
                        # Remove page numbers, headers, footers (very short lines)
                        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
                        substantial_lines = [line for line in lines if len(line) > 10]

                        # If most lines are very short, it might be metadata/artifacts
                        if len(substantial_lines) < len(lines) * 0.3:
                            has_meaningful_text = False
                        else:
                            # Check for actual content
                            text_sample = ' '.join(substantial_lines[:5])
                            if len(text_sample) < 30:
                                has_meaningful_text = False

                    if has_meaningful_text:
                        # Use extracted text
                        logger.info(f"Page {page_num + 1}: Using text extraction ({text_length} characters)")
                        cleaned_text = page_text.strip()
                        if cleaned_text:
                            pages.append({
                                'text': cleaned_text,
                                'extraction_method': 'text_extraction',
                                'page_number': page_num + 1
                            })

                    else:
                        # Page appears to be image-only, use OCR
                        logger.info(f"Page {page_num + 1}: No meaningful text found, using OCR")

                        try:
                            # Get page as image for OCR
                            pix = page.get_pixmap(dpi=400)
                            img_data = pix.tobytes("png")

                            # Convert to PIL Image and enhance for OCR
                            from PIL import Image, ImageEnhance, ImageFilter
                            img = Image.open(io.BytesIO(img_data))

                            if img.mode != 'L':
                                img = img.convert('L')

                            # Enhance image
                            enhancer = ImageEnhance.Contrast(img)
                            img = enhancer.enhance(1.2)
                            enhancer = ImageEnhance.Sharpness(img)
                            img = enhancer.enhance(1.5)
                            img = img.filter(ImageFilter.MedianFilter(size=3))

                            # Resize if needed
                            width, height = img.size
                            if width < 1000 or height < 1000:
                                scale_factor = max(1000/width, 1000/height)
                                new_width = int(width * scale_factor)
                                new_height = int(height * scale_factor)
                                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                            # Try multiple OCR configurations
                            ocr_configs = [
                                (r'--oem 3 --psm 6 -l ara -c preserve_interword_spaces=1', "PSM 6"),
                                (r'--oem 3 --psm 1 -l ara -c preserve_interword_spaces=1', "PSM 1"),
                                (r'--oem 3 --psm 7 -l ara -c preserve_interword_spaces=1', "PSM 7"),
                            ]

                            best_text = ""
                            best_length = 0

                            for config, desc in ocr_configs:
                                try:
                                    text_result = pytesseract.image_to_string(img, config=config)
                                    if len(text_result.strip()) > best_length:
                                        best_text = text_result
                                        best_length = len(text_result.strip())
                                        if best_length > 100:
                                            break
                                except Exception:
                                    continue

                            ocr_text = best_text.strip()
                            if ocr_text:
                                ocr_text = self._clean_arabic_ocr_text(ocr_text)

                            if ocr_text and len(ocr_text) > 10:
                                logger.info(f"Page {page_num + 1}: OCR extracted {len(ocr_text)} characters")
                                pages.append({
                                    'text': ocr_text,
                                    'extraction_method': 'ocr',
                                    'page_number': page_num + 1
                                })
                            else:
                                logger.warning(f"Page {page_num + 1}: OCR produced no meaningful text")

                        except Exception as ocr_error:
                            logger.error(f"OCR failed for page {page_num + 1}: {str(ocr_error)}")

                except Exception as page_error:
                    logger.error(f"Error processing page {page_num + 1}: {str(page_error)}")

            pdf_document.close()

            # Filter out empty pages
            valid_pages = [p for p in pages if p.get('text', '').strip()]
            logger.info(f"PDF processing completed: {len(valid_pages)} valid pages out of {len(pages)} total pages")

            # Log extraction method summary
            text_extraction_count = len([p for p in valid_pages if p.get('extraction_method') == 'text_extraction'])
            ocr_count = len([p for p in valid_pages if p.get('extraction_method') == 'ocr'])
            logger.info(f"Extraction methods used - Text extraction: {text_extraction_count}, OCR: {ocr_count}")

            return valid_pages

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in smart PDF processing: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process PDF file: {str(e)}"
            )

    async def process_bulk_text_upload(self, content: bytes, filename: str) -> list:
        """
        Process bulk text upload for pages. Supports .txt, .md, .pdf, .doc, and .docx files.
        Automatically detects which pages need OCR and which can use direct text extraction.

        Args:
            content: The file content as bytes
            filename: The original filename

        Returns:
            List of page data dictionaries with 'text' key and 'extraction_method' info
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
            
            # Extract text based on file type with intelligent OCR detection
            if content_type == "application/pdf":
                # Use intelligent PDF processing that detects OCR needs per page
                pages = await self._process_pdf_with_smart_ocr(content, filename)
                logger.info(f"PDF processing completed: {len(pages)} pages")
                return pages
            else:
                # For non-PDF files, use regular text extraction
                text_content = await self._extract_text_from_file(content, content_type, filename)
                logger.info(f"Extracted text length: {len(text_content)} characters")
            
            # Split into pages based on file type (for non-PDF files)
            pages = []

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
                        'text': cleaned_text,
                        'extraction_method': 'text_extraction'
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