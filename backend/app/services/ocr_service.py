import os
import google.generativeai as genai
from PIL import Image
import io
import requests
import base64
from openai import OpenAI

class OCRService:
    def __init__(self):
        self.provider = os.getenv("OCR_PROVIDER", "gemini").lower()
        self.gemini_model = None
        self.openai_client = None
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return

        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini OCR")

            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_OCR_MODEL", "gemini-2.0-flash-exp")
            self.gemini_model = genai.GenerativeModel(model_name)

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI OCR")

            self.openai_client = OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unsupported OCR provider: {self.provider}. Supported providers: gemini, openai")

        self._initialized = True

    async def extract_text_from_image(self, image_path_or_url: str) -> str:
        """
        Extract text from image using the configured OCR provider (Gemini or OpenAI)
        """
        self._initialize()

        try:
            # Load image
            image = self._load_image(image_path_or_url)

            if self.provider == "gemini":
                return await self._extract_with_gemini(image)
            elif self.provider == "openai":
                return await self._extract_with_openai(image)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            raise Exception(f"OCR extraction failed with {self.provider}: {str(e)}")

    def _load_image(self, image_path_or_url: str) -> Image.Image:
        """Load image from URL or local path"""
        if image_path_or_url.startswith(('http://', 'https://')):
            # Download image from URL
            response = requests.get(image_path_or_url)
            response.raise_for_status()
            return Image.open(io.BytesIO(response.content))
        else:
            # Open local image file
            return Image.open(image_path_or_url)

    async def _extract_with_gemini(self, image: Image.Image) -> str:
        """Extract text using Gemini vision model"""
        prompt = self._get_ocr_prompt()
        response = self.gemini_model.generate_content([prompt, image])
        return response.text.strip()

    async def _extract_with_openai(self, image: Image.Image) -> str:
        """Extract text using OpenAI vision model"""
        # Convert PIL image to base64
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        model_name = os.getenv("OPENAI_OCR_MODEL", "gpt-4o-mini")

        response = self.openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._get_ocr_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=4000
        )

        return response.choices[0].message.content.strip()

    def _get_ocr_prompt(self) -> str:
        """Get the OCR prompt for text extraction"""
        return """
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

    async def extract_text_from_pil_image(self, pil_image: Image.Image) -> str:
        """
        Extract text from PIL Image object using the configured OCR provider (Gemini or OpenAI)
        """
        self._initialize()

        try:
            if self.provider == "gemini":
                extracted_text = await self._extract_with_gemini(pil_image)
            elif self.provider == "openai":
                extracted_text = await self._extract_with_openai(pil_image)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

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
            raise Exception(f"OCR extraction failed with {self.provider}: {str(e)}")

ocr_service = OCRService()