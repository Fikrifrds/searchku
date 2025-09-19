from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    similarity_threshold: Optional[float] = 0.7

class SearchResult(BaseModel):
    page_id: UUID
    book_id: UUID
    page_number: int
    original_text: str
    en_translation: Optional[str] = None
    id_translation: Optional[str] = None
    similarity_score: float
    snippet: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    query: str
    total_results: int
    query_embedding_model: str