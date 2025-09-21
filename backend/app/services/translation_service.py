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
Translate the following Arabic text to {target_lang_name}.

CRITICAL TRANSLATION AND FORMATTING RULES:
1. Translate ONLY what is written in the provided text - do not add any external content
2. If text appears to be cut off or incomplete, translate only what is visible - do not complete or guess the missing parts
3. Do not add explanations, context, or any text that is not in the original

EXACT FORMATTING REQUIREMENTS:
4. Preserve the EXACT line breaks and blank lines as shown in the original Arabic text
5. If there are page numbers (like "- ١١ -"), translate them but keep them on separate lines with the same spacing
6. Each hadith should be separated by blank lines just like in the original
7. Hadith titles (like "الحديث الثالث عشر") should be on separate lines with proper spacing before and after
8. Keep the chain of narration (إسناد) on separate lines as in the original
9. Keep hadith text on separate lines maintaining the original line breaks
10. Keep references (like "رواه البخاري") on separate lines with proper spacing
11. Do not combine multiple lines into paragraphs - each line should remain separate
12. Maintain the visual structure so it looks identical to the Arabic version when rendered

Provide ONLY the direct translation preserving the exact visual layout and spacing of the Arabic text.

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
Look at this image containing Arabic text and translate all the Arabic text you see to {target_lang_name}.

CRITICAL TRANSLATION AND FORMATTING RULES:
1. Translate ONLY the Arabic text that is visible in the image - do not add any external content
2. If text appears to be cut off at the edges or partially visible, translate only what you can clearly see - do not complete or guess the missing parts
3. Do not add any explanations, context, interpretations, or text that is not actually written in the image

EXACT FORMATTING REQUIREMENTS:
4. Preserve the EXACT line breaks and blank lines as shown in the original Arabic text
5. If there are page numbers (like "- ١١ -"), translate them but keep them on separate lines with the same spacing
6. Each hadith should be separated by blank lines just like in the original
7. Hadith titles (like "الحديث الثالث عشر") should be on separate lines with proper spacing before and after
8. Keep the chain of narration (إسناد) on separate lines as in the original
9. Keep hadith text on separate lines maintaining the original line breaks
10. Keep references (like "رواه البخاري") on separate lines with proper spacing
11. Do not combine multiple lines into paragraphs - each line should remain separate
12. Maintain the visual structure so it looks identical to the Arabic version when rendered

Provide ONLY the direct translation preserving the exact visual layout and spacing of the Arabic text.

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