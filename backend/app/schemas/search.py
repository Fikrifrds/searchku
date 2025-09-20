from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7
    query_language: Optional[str] = None  # 'en', 'id', 'ar', or None for auto-detection

class SearchResult(BaseModel):
    page_id: int
    book_id: int
    page_number: int
    original_text: str
    en_translation: Optional[str] = None
    id_translation: Optional[str] = None
    similarity_score: float
    snippet: str
    book_title: str
    book_author: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int
    query_embedding_model: Optional[str] = None