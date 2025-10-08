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

        # Prepare request parameters
        request_params = {
            "model": model_name,
            "messages": [
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
            ]
        }

        # Add model-specific parameters
        if model_name.startswith(('gpt-5', 'gpt-5-mini')):
            request_params["max_completion_tokens"] = 4000
        else:
            request_params["max_tokens"] = 4000

        response = self.openai_client.chat.completions.create(**request_params)

        return response.choices[0].message.content.strip()

    def _get_ocr_prompt(self) -> str:
        """Get the OCR prompt for text extraction"""
        return """
Extract ALL text from this image with intelligent formatting that preserves good structure while correcting scanning/layout errors.

INTELLIGENT TEXT EXTRACTION RULES:

1. ACCURATE TEXT EXTRACTION:
   - Extract every visible character EXACTLY as it appears - no additions or modifications
   - If text has Arabic diacritics/harakat (َ ِ ُ ْ ّ ً ٌ ٍ), extract them exactly as shown
   - If text has NO diacritics/harakat, do NOT add any - extract only what is visible
   - Maintain proper Arabic right-to-left text direction
   - Preserve exact punctuation and symbols as they appear
   - NEVER add, remove, or modify any characters - be 100% faithful to the original

2. SMART FORMATTING DECISIONS:
   PRESERVE these good formatting elements:
   - Proper paragraph breaks and sections
   - Numbered lists and bullet points with correct indentation
   - Headers and titles with appropriate spacing
   - Meaningful line breaks between different topics
   - Table-like structures with logical spacing

   CORRECT these formatting issues:
   - Text that appears misplaced due to scanning errors
   - Awkward line breaks in the middle of sentences
   - Inconsistent spacing that disrupts readability
   - Text fragments that should be connected
   - Layout artifacts from scanning/printing

3. CONTENT ORGANIZATION:
   - Group related text together logically
   - Ensure sentences flow naturally
   - Place page numbers and footnotes appropriately
   - Maintain logical reading order for Arabic text
   - Preserve meaningful structural elements (headings, lists, etc.)

4. QUALITY STANDARDS:
   - Text should be readable and well-formatted
   - No broken sentences due to layout preservation
   - Consistent spacing and indentation
   - Natural flow while maintaining document structure
   - Clear separation between different sections/topics

5. OUTPUT FORMAT:
   - Clean, readable Arabic text with proper formatting
   - Use appropriate line breaks and spacing for readability
   - Maintain document hierarchy and structure
   - No commentary, explanations, or metadata

GOAL: Produce clean, accurately formatted Arabic text that preserves the document's logical structure while correcting scanning/layout artifacts for optimal readability. CRITICAL: Extract text exactly as written - do not add harakat where none exist, do not remove harakat that are present. Be completely faithful to the original text content.
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