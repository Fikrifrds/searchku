from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from ..models.page import Page
from ..models.book import Book
from ..schemas.search import SearchResult
from .embedding_service import embedding_service
import logging

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        self.default_similarity_threshold = 0.7
        self.default_limit = 10
    
    async def semantic_search(
        self,
        db: Session,
        query: str,
        limit: Optional[int] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[SearchResult]:
        """
        Perform semantic search using vector similarity.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            
        Returns:
            List of search results ordered by similarity score
        """
        try:
            # Set defaults
            limit = limit or self.default_limit
            similarity_threshold = similarity_threshold or self.default_similarity_threshold

            print(f"SEMANTIC SEARCH: Query: '{query}', limit: {limit}, threshold: {similarity_threshold}")
            logger.info(f"Performing semantic search for query: '{query}' with limit: {limit}, threshold: {similarity_threshold}")

            # Generate embedding for the query
            query_embedding = await embedding_service.generate_embedding(query)
            print(f"SEMANTIC SEARCH: Generated embedding: {len(query_embedding) if query_embedding else 0} dimensions")
            logger.info(f"Generated query embedding: {len(query_embedding) if query_embedding else 0} dimensions")
            
            if not query_embedding:
                logger.error("Failed to generate embedding for search query")
                return []
            
            # Perform vector similarity search using pgvector
            # Using cosine similarity (1 - cosine_distance)
            # Cast the query embedding to vector type for pgvector compatibility
            sql_query = text("""
                SELECT
                    p.id,
                    p.book_id,
                    p.page_number,
                    p.original_text,
                    p.en_translation,
                    p.id_translation,
                    p.embedding_model,
                    b.title as book_title,
                    b.author as book_author,
                    1 - (p.embedding_vector <=> CAST(:query_embedding AS vector)) as similarity_score
                FROM pages p
                JOIN books b ON p.book_id = b.id
                WHERE p.embedding_vector IS NOT NULL
                    AND 1 - (p.embedding_vector <=> CAST(:query_embedding AS vector)) >= :similarity_threshold
                ORDER BY p.embedding_vector <=> CAST(:query_embedding AS vector)
                LIMIT :limit
            """)
            
            result = db.execute(
                sql_query,
                {
                    "query_embedding": query_embedding,
                    "similarity_threshold": similarity_threshold,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            print(f"SEMANTIC SEARCH: Database query returned {len(rows)} rows")
            logger.info(f"Semantic search database query returned {len(rows)} rows")

            # Convert to SearchResult objects
            search_results = []
            for row in rows:
                # Generate snippet
                snippet = self._generate_snippet(row.original_text, query)
                
                search_result = SearchResult(
                    page_id=row.id,
                    book_id=row.book_id,
                    page_number=row.page_number,
                    original_text=row.original_text,
                    en_translation=row.en_translation,
                    id_translation=row.id_translation,
                    similarity_score=float(row.similarity_score),
                    snippet=snippet,
                    book_title=row.book_title,
                    book_author=row.book_author
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing semantic search: {str(e)}")
            return []
    
    async def text_search(
        self,
        db: Session,
        query: str,
        limit: Optional[int] = None
    ) -> List[SearchResult]:
        """
        Perform simple text-based search as fallback.
        
        Args:
            db: Database session
            query: Search query text
            limit: Maximum number of results to return
            
        Returns:
            List of search results
        """
        try:
            limit = limit or self.default_limit
            print(f"TEXT SEARCH: Performing text search for query: '{query}' with limit: {limit}")
            logger.info(f"Performing text search for query: '{query}' with limit: {limit}")

            # Simple text search using ILIKE
            pages = db.query(Page, Book).join(Book).filter(
                Page.original_text.ilike(f"%{query}%")
            ).limit(limit).all()

            print(f"TEXT SEARCH: Found {len(pages)} results")
            logger.info(f"Text search found {len(pages)} results")
            
            search_results = []
            for page, book in pages:
                snippet = self._generate_snippet(page.original_text, query)
                
                search_result = SearchResult(
                    page_id=page.id,
                    book_id=page.book_id,
                    page_number=page.page_number,
                    original_text=page.original_text,
                    en_translation=page.en_translation,
                    id_translation=page.id_translation,
                    similarity_score=0.5,  # Default score for text search
                    snippet=snippet,
                    book_title=book.title,
                    book_author=book.author
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error performing text search: {str(e)}")
            return []
    
    def _generate_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """
        Generate a snippet from text highlighting the query terms.
        
        Args:
            text: The full text
            query: The search query
            max_length: Maximum length of the snippet
            
        Returns:
            Text snippet with query context
        """
        try:
            # Simple snippet generation
            if len(text) <= max_length:
                return text
            
            # Try to find query terms in text
            query_lower = query.lower()
            text_lower = text.lower()
            
            # Find the position of the query in the text
            query_pos = text_lower.find(query_lower)
            
            if query_pos == -1:
                # Query not found, return beginning of text
                return text[:max_length] + "..."
            
            # Calculate snippet boundaries
            start_pos = max(0, query_pos - max_length // 3)
            end_pos = min(len(text), start_pos + max_length)
            
            snippet = text[start_pos:end_pos]
            
            # Add ellipsis if needed
            if start_pos > 0:
                snippet = "..." + snippet
            if end_pos < len(text):
                snippet = snippet + "..."
            
            return snippet
            
        except Exception as e:
            logger.error(f"Error generating snippet: {str(e)}")
            return text[:max_length] + "..." if len(text) > max_length else text
    
    async def get_similar_pages(
        self,
        db: Session,
        page_id: str,
        limit: Optional[int] = 5
    ) -> List[SearchResult]:
        """
        Find pages similar to a given page using its embedding.
        
        Args:
            db: Database session
            page_id: ID of the reference page
            limit: Maximum number of similar pages to return
            
        Returns:
            List of similar pages
        """
        try:
            # Get the reference page
            ref_page = db.query(Page).filter(Page.id == page_id).first()
            if not ref_page or not ref_page.embedding_vector:
                return []
            
            # Find similar pages using vector similarity
            sql_query = text("""
                SELECT 
                    p.id,
                    p.book_id,
                    p.page_number,
                    p.original_text,
                    p.en_translation,
                    p.id_translation,
                    b.title as book_title,
                    b.author as book_author,
                    1 - (p.embedding_vector <=> :ref_embedding) as similarity_score
                FROM pages p
                JOIN books b ON p.book_id = b.id
                WHERE p.embedding_vector IS NOT NULL
                    AND p.id != :page_id
                ORDER BY p.embedding_vector <=> :ref_embedding
                LIMIT :limit
            """)
            
            result = db.execute(
                sql_query,
                {
                    "ref_embedding": ref_page.embedding_vector,
                    "page_id": page_id,
                    "limit": limit
                }
            )
            
            rows = result.fetchall()
            
            search_results = []
            for row in rows:
                snippet = self._generate_snippet(row.original_text, "", 150)
                
                search_result = SearchResult(
                    page_id=row.id,
                    book_id=row.book_id,
                    page_number=row.page_number,
                    original_text=row.original_text,
                    en_translation=row.en_translation,
                    id_translation=row.id_translation,
                    similarity_score=float(row.similarity_score),
                    snippet=snippet,
                    book_title=row.book_title,
                    book_author=row.book_author
                )
                search_results.append(search_result)
            
            return search_results
            
        except Exception as e:
            logger.error(f"Error finding similar pages: {str(e)}")
            return []

# Global instance
search_service = SearchService()