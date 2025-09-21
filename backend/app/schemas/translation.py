from pydantic import BaseModel, Field
from typing import Literal, Optional

class TranslationRequest(BaseModel):
    page_id: int = Field(..., description="The ID of the page to translate")
    target_language: Literal["en", "id"] = Field(..., description="Target language: 'en' for English, 'id' for Indonesian")
    use_image: bool = Field(False, description="Use image processing instead of stored text")

class TranslationResponse(BaseModel):
    page_id: int = Field(..., description="The ID of the translated page")
    original_text: str = Field(..., description="The original Arabic text")
    translated_text: str = Field(..., description="The translated text")
    target_language: str = Field(..., description="The target language")
    stored_in_db: bool = Field(..., description="Whether translation was stored in database")
    used_image: bool = Field(False, description="Whether image processing was used")
    success: bool = Field(True, description="Translation success status")