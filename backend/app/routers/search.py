from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.search import SearchRequest, SearchResponse
from ..services.search_service import search_service

router = APIRouter(tags=["search"])

@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform semantic search across book pages using vector embeddings.
    """
    try:
        print(f"ROUTER: Semantic search called with query: {request.query}")
        # Use the search service for semantic search
        results = await search_service.semantic_search(
            db=db,
            query=request.query,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold
        )
        print(f"ROUTER: Semantic search returned {len(results)} results")
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")

@router.post("/text", response_model=SearchResponse)
async def text_search(
    request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Perform simple text-based search as fallback.
    """
    try:
        print(f"ROUTER: Text search called with query: {request.query}")
        results = await search_service.text_search(
            db=db,
            query=request.query,
            limit=request.limit
        )
        print(f"ROUTER: Search service returned {len(results)} results")
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text search failed: {str(e)}")

@router.get("/similar/{page_id}", response_model=SearchResponse)
async def get_similar_pages(
    page_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Find pages similar to a given page.
    """
    try:
        results = await search_service.get_similar_pages(
            db=db,
            page_id=page_id,
            limit=limit
        )
        
        return SearchResponse(
            query=f"Similar to page {page_id}",
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar pages search failed: {str(e)}")

@router.get("/health")
async def search_health():
    """Health check for search service."""
    return {"status": "healthy", "service": "search"}