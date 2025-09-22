import os
import google.generativeai as genai
from PIL import Image
import io
import requests

class OCRService:
    def __init__(self):
        self.model = None
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required")

        genai.configure(api_key=api_key)
        model_name = os.getenv("OCR_MODEL", "gemini-2.0-flash-exp")
        self.model = genai.GenerativeModel(model_name)
        self._initialized = True

    async def extract_text_from_image(self, image_path_or_url: str) -> str:
        """
        Extract text from image using Gemini vision model
        """
        self._initialize()

        try:
            # Check if it's a URL or local file path
            if image_path_or_url.startswith(('http://', 'https://')):
                # Download image from URL
                response = requests.get(image_path_or_url)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            else:
                # Open local image file
                image = Image.open(image_path_or_url)

            prompt = """
Extract ALL text from this image while preserving the EXACT visual layout and formatting.

CRITICAL LAYOUT PRESERVATION REQUIREMENTS:
1. Extract ONLY the text that is visible in the image - do not add any interpretations
2. Preserve the EXACT spatial arrangement as it appears in the image:
   - Maintain all line breaks exactly as shown
   - Preserve spacing between words and paragraphs
   - Keep indentation and margins
   - Maintain vertical spacing between lines
3. For Arabic text: Extract character by character with perfect accuracy including:
   - All diacritics and vowel marks
   - Proper right-to-left text direction
   - Correct word spacing and punctuation
4. Preserve document structure:
   - Headers, titles, and subtitles with their positioning
   - Page numbers and footnotes in their original locations
   - Multiple columns as separate sections
   - Bullet points, numbered lists with proper formatting
5. Spacing and alignment:
   - Use appropriate whitespace to match the visual layout
   - Preserve paragraph breaks and section separations
   - Maintain text alignment (centered, justified, etc.)
6. Special formatting:
   - Preserve any emphasis (spacing for bold/italic appearance)
   - Keep table-like structures with appropriate spacing
   - Maintain any special character arrangements
7. If text is partially cut off or unclear, extract only what you can clearly see
8. Do not guess, interpret, or complete incomplete words
9. Do not add any commentary, explanations, or metadata

OUTPUT FORMAT: Provide ONLY the extracted text with exact visual formatting preserved using appropriate spacing, line breaks, and layout structure to match the original image as closely as possible.
"""

            # Generate content with image
            response = self.model.generate_content([prompt, image])
            extracted_text = response.text.strip()

            return extracted_text

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

    async def extract_text_from_pil_image(self, pil_image: Image.Image) -> str:
        """
        Extract text from PIL Image object using Gemini vision model
        """
        self._initialize()

        try:
            prompt = """
Extract ALL text from this image while preserving the EXACT visual layout and formatting.

CRITICAL LAYOUT PRESERVATION REQUIREMENTS:
1. Extract ONLY the text that is visible in the image - do not add any interpretations
2. Preserve the EXACT spatial arrangement as it appears in the image:
   - Maintain all line breaks exactly as shown
   - Preserve spacing between words and paragraphs
   - Keep indentation and margins
   - Maintain vertical spacing between lines
3. For Arabic text: Extract character by character with perfect accuracy including:
   - All diacritics and vowel marks
   - Proper right-to-left text direction
   - Correct word spacing and punctuation
4. Preserve document structure:
   - Headers, titles, and subtitles with their positioning
   - Page numbers and footnotes in their original locations
   - Multiple columns as separate sections
   - Bullet points, numbered lists with proper formatting
5. Spacing and alignment:
   - Use appropriate whitespace to match the visual layout
   - Preserve paragraph breaks and section separations
   - Maintain text alignment (centered, justified, etc.)
6. Special formatting:
   - Preserve any emphasis (spacing for bold/italic appearance)
   - Keep table-like structures with appropriate spacing
   - Maintain any special character arrangements
7. If text is partially cut off or unclear, extract only what you can clearly see
8. Do not guess, interpret, or complete incomplete words
9. Do not add any commentary, explanations, or metadata

OUTPUT FORMAT: Provide ONLY the extracted text with exact visual formatting preserved using appropriate spacing, line breaks, and layout structure to match the original image as closely as possible.
"""

            # Generate content with image
            response = self.model.generate_content([prompt, pil_image])
            extracted_text = response.text

            # Preserve original formatting - don't strip leading/trailing whitespace completely
            # Only remove excessive whitespace while preserving intentional spacing
            if extracted_text:
                # Remove only the outermost leading/trailing whitespace but preserve internal formatting
                lines = extracted_text.split('\n')
                # Remove completely empty lines at the start and end only
                while lines and not lines[0].strip():
                    lines.pop(0)
                while lines and not lines[-1].strip():
                    lines.pop()
                extracted_text = '\n'.join(lines)

            return extracted_text

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

ocr_service = OCRService()