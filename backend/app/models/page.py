from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from ..database import Base

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    embedding_vector = Column(Vector(1536), nullable=True)  # OpenAI text-embedding-3-small dimension
    embedding_model = Column(String(100), nullable=False, default="text-embedding-3-small", index=True)
    en_translation = Column(Text, nullable=True)
    id_translation = Column(Text, nullable=True)
    page_image_url = Column(String(500), nullable=True, index=True)  # AWS S3 URL for page image
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship with book
    book = relationship("Book", back_populates="pages")
    
    # Unique constraint for book_id and page_number
    __table_args__ = (UniqueConstraint('book_id', 'page_number', name='_book_page_uc'),)
    
    def __repr__(self):
        return f"<Page(id={self.id}, book_id={self.book_id}, page_number={self.page_number})>"