from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from app.schemas.translation import TranslationRequest, TranslationResponse
from app.services.translation_service import translation_service
from app.database import get_db
from app.models.page import Page
from pydantic import BaseModel

class PageTranslationsResponse(BaseModel):
    page_id: int
    original_text: str
    en_translation: Optional[str]
    id_translation: Optional[str]

router = APIRouter(prefix="/translation", tags=["translation"])

@router.post("/", response_model=TranslationResponse)
async def translate_page(request: TranslationRequest, db: Session = Depends(get_db)):
    """
    Translate a page's Arabic text to English or Indonesian using Google Gemini
    and store the translation in the database
    """
    try:
        # Fetch the page from database
        page = db.query(Page).filter(Page.id == request.page_id).first()
        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page with ID {request.page_id} not found"
            )

        # Translate using image or text
        if request.use_image and page.page_image_url:
            translated_text = await translation_service.translate_from_image(
                image_url=page.page_image_url,
                target_language=request.target_language
            )
            used_image = True
        else:
            translated_text = await translation_service.translate_text(
                text=page.original_text,
                target_language=request.target_language
            )
            used_image = False

        # Store translation in appropriate database field
        if request.target_language == "en":
            page.en_translation = translated_text
        else:  # "id"
            page.id_translation = translated_text

        # Commit the changes
        db.commit()
        db.refresh(page)

        return TranslationResponse(
            page_id=page.id,
            original_text=page.original_text,
            translated_text=translated_text,
            target_language=request.target_language,
            stored_in_db=True,
            used_image=used_image,
            success=True
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Translation failed: {str(e)}"
        )

@router.get("/{page_id}", response_model=PageTranslationsResponse)
async def get_page_translations(page_id: int, db: Session = Depends(get_db)):
    """
    Get existing translations for a page
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(
            status_code=404,
            detail=f"Page with ID {page_id} not found"
        )

    return PageTranslationsResponse(
        page_id=page.id,
        original_text=page.original_text,
        en_translation=page.en_translation,
        id_translation=page.id_translation
    )