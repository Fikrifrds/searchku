import os
import google.generativeai as genai
from openai import OpenAI
from typing import Literal
import requests
from PIL import Image
import io

class TranslationService:
    def __init__(self):
        self.gemini_model = None
        self.openai_client = None
        self.provider = os.getenv("TRANSLATION_PROVIDER", "gemini")
        self._initialized = False

    def _initialize(self):
        if self._initialized:
            return

        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")

            genai.configure(api_key=api_key)
            model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
            self.gemini_model = genai.GenerativeModel(model_name)

        elif self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            self.openai_client = OpenAI(api_key=api_key)

        else:
            raise ValueError(f"Unsupported translation provider: {self.provider}")

        self._initialized = True

    async def translate_text(
        self,
        text: str,
        target_language: Literal["en", "id"]
    ) -> str:
        self._initialize()

        language_names = {
            "en": "English",
            "id": "Indonesian"
        }

        target_lang_name = language_names[target_language]

        prompt = f"""
You are translating Islamic scholarly text. This requires ABSOLUTE ACCURACY with no interpretations, opinions, or assumptions.

SCHOLARLY TRANSLATION REQUIREMENTS:
1. This is Islamic religious scholarship - accuracy is paramount
2. Translate ONLY the exact Arabic words provided - no additions, interpretations, or explanations
3. Use precise, literal translation without personal opinions or assumptions
4. If you are uncertain about any word or phrase, translate it as literally as possible
5. Do not add commentary, context, or explanatory text
6. Preserve all Islamic terminology accurately (names, places, religious terms)
7. If text appears incomplete, translate only what is visible - never guess or complete

EXACT FORMATTING REQUIREMENTS:
8. Preserve the EXACT line breaks and blank lines as shown in the original Arabic text
9. Keep page numbers (like "- ١١ -") on separate lines with identical spacing
10. Each hadith must be separated by blank lines exactly as in the original
11. Hadith titles (like "الحديث الثالث عشر") on separate lines with proper spacing
12. Keep chains of narration (إسناد) on separate lines as in the original
13. Maintain original line breaks within hadith text
14. Keep references (like "رواه البخاري") on separate lines with proper spacing
15. Do not combine lines into paragraphs - each line remains separate
16. The visual structure must be identical to the Arabic version

Provide ONLY the direct, literal, scholarly accurate translation with exact formatting.

Arabic text:
{text}

{target_lang_name} translation:
"""

        try:
            if self.provider == "gemini":
                response = self.gemini_model.generate_content(prompt)
                return response.text.strip()
            elif self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-4.1"),
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

    async def translate_from_image(
        self,
        image_url: str,
        target_language: Literal["en", "id"]
    ) -> str:
        self._initialize()

        language_names = {
            "en": "English",
            "id": "Indonesian"
        }

        target_lang_name = language_names[target_language]

        try:
            prompt = f"""
You are translating Islamic scholarly text from an image. This requires ABSOLUTE ACCURACY with no interpretations, opinions, or assumptions.

SCHOLARLY TRANSLATION REQUIREMENTS:
1. This is Islamic religious scholarship - accuracy is paramount
2. Translate ONLY the exact Arabic text visible in the image - no additions, interpretations, or explanations
3. Use precise, literal translation without personal opinions or assumptions
4. If you are uncertain about any word or phrase, translate it as literally as possible
5. Do not add commentary, context, or explanatory text that is not in the image
6. Preserve all Islamic terminology accurately (names of companions, places, religious terms)
7. If text appears cut off at edges, translate only what is clearly visible - never guess or complete
8. Do not interpret abbreviated words or references - translate exactly as written

EXACT FORMATTING REQUIREMENTS:
9. Preserve the EXACT line breaks and blank lines as shown in the original Arabic text
10. Keep page numbers (like "- ١١ -") on separate lines with identical spacing
11. Each hadith must be separated by blank lines exactly as in the original
12. Hadith titles (like "الحديث الثالث عشر") on separate lines with proper spacing
13. Keep chains of narration (إسناد) on separate lines as in the original
14. Maintain original line breaks within hadith text
15. Keep references (like "رواه البخاري") on separate lines with proper spacing
16. Do not combine lines into paragraphs - each line remains separate
17. The visual structure must be identical to the Arabic version

Provide ONLY the direct, literal, scholarly accurate translation with exact formatting.

Translate to {target_lang_name}:
"""

            if self.provider == "gemini":
                # Download image from URL
                response = requests.get(image_url)
                response.raise_for_status()

                # Convert to PIL Image
                image = Image.open(io.BytesIO(response.content))

                # Generate content with image
                response = self.gemini_model.generate_content([prompt, image])
                return response.text.strip()

            elif self.provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_TRANSLATION_MODEL", "gpt-4.1"),
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                },
                            },
                        ],
                    }]
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            raise Exception(f"Image translation failed: {str(e)}")

translation_service = TranslationService()