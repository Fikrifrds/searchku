import os
import google.generativeai as genai
from typing import Literal

class TranslationService:
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
        self.model = genai.GenerativeModel('gemini-1.5-pro')
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
Provide only the translation without any additional explanations or notes.

Arabic text:
{text}

{target_lang_name} translation:
"""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Translation failed: {str(e)}")

translation_service = TranslationService()