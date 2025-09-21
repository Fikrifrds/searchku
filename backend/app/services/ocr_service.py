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
Extract ALL text from this image with ABSOLUTE ACCURACY.

CRITICAL OCR REQUIREMENTS:
1. Extract ONLY the text that is visible in the image - do not add any interpretations
2. Preserve the EXACT formatting, line breaks, and spacing as shown in the image
3. If the text is in Arabic, extract it character by character with perfect accuracy
4. Include page numbers, titles, headers, and all visible text elements
5. Maintain the original structure and layout
6. If text is partially cut off or unclear, extract only what you can clearly see
7. Do not guess, interpret, or complete incomplete words
8. Do not add any commentary or explanations
9. If there are multiple columns, preserve the column structure
10. Include punctuation marks and diacritics exactly as shown

Provide ONLY the extracted text with exact formatting:
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
Extract ALL text from this image with ABSOLUTE ACCURACY.

CRITICAL OCR REQUIREMENTS:
1. Extract ONLY the text that is visible in the image - do not add any interpretations
2. Preserve the EXACT formatting, line breaks, and spacing as shown in the image
3. If the text is in Arabic, extract it character by character with perfect accuracy
4. Include page numbers, titles, headers, and all visible text elements
5. Maintain the original structure and layout
6. If text is partially cut off or unclear, extract only what you can clearly see
7. Do not guess, interpret, or complete incomplete words
8. Do not add any commentary or explanations
9. If there are multiple columns, preserve the column structure
10. Include punctuation marks and diacritics exactly as shown

Provide ONLY the extracted text with exact formatting:
"""

            # Generate content with image
            response = self.model.generate_content([prompt, pil_image])
            extracted_text = response.text.strip()

            return extracted_text

        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")

ocr_service = OCRService()