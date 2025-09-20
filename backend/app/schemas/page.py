from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PageBase(BaseModel):
    page_number: int
    original_text: str

class PageCreate(PageBase):
    pass

class PageUpdate(BaseModel):
    en_translation: Optional[str] = None
    id_translation: Optional[str] = None

class PageResponse(PageBase):
    id: int
    book_id: int
    embedding_model: str
    en_translation: Optional[str] = None
    id_translation: Optional[str] = None
    page_image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True