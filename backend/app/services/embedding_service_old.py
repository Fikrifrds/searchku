import openai
import os
from typing import List, Optional
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

        # Use reduced dimensions for text-embedding-3-large to maintain pgvector compatibility
        env_dimension = int(os.getenv("EMBEDDING_DIMENSION", 1536))
        if self.model == "text-embedding-3-large" and env_dimension > 2000:
            self.dimension = 1536  # Reduce to 1536 for pgvector compatibility
            logger.info(f"Reducing {self.model} dimensions from {env_dimension} to {self.dimension} for pgvector compatibility")
        else:
            self.dimension = env_dimension

        logger.info(f"Embedding service initialized: model={self.model}, dimensions={self.dimension}")
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a given text using OpenAI API.
        
        Args:
            text: The text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        try:
            # Clean and prepare text
            cleaned_text = text.strip().replace("\n", " ")
            
            if not cleaned_text:
                logger.warning("Empty text provided for embedding generation")
                return None
            
            # Generate embedding with specific dimensions if supported
            embedding_params = {
                "model": self.model,
                "input": cleaned_text,
                "encoding_format": "float"
            }

            # Add dimensions parameter for models that support it
            if self.model in ["text-embedding-3-large", "text-embedding-3-small"]:
                embedding_params["dimensions"] = self.dimension

            response = self.client.embeddings.create(**embedding_params)
            
            embedding = response.data[0].embedding

            # Ensure embedding is a proper list of floats
            if isinstance(embedding, str):
                logger.error(f"Received string embedding instead of list: {embedding[:100]}...")
                try:
                    import json
                    embedding = json.loads(embedding)
                    logger.info("Successfully parsed string embedding to list")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse string embedding: {str(e)}")
                    return None

            # Convert to list if it's not already
            if not isinstance(embedding, list):
                try:
                    embedding = list(embedding)
                    logger.info(f"Converted embedding from {type(response.data[0].embedding)} to list")
                except Exception as e:
                    logger.error(f"Failed to convert embedding to list: {str(e)}")
                    return None

            # Validate embedding dimension
            if len(embedding) != self.dimension:
                logger.error(f"Unexpected embedding dimension: {len(embedding)}, expected: {self.dimension}")
                return None

            # Ensure all elements are floats
            try:
                embedding = [float(x) for x in embedding]
                logger.debug(f"Embedding conversion successful: {len(embedding)} floats")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert embedding elements to floats: {str(e)}")
                return None

            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors (or None for failed generations)
        """
        try:
            # Clean texts
            cleaned_texts = [text.strip().replace("\n", " ") for text in texts]
            
            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(cleaned_texts):
                if text:
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning("No valid texts provided for batch embedding generation")
                return [None] * len(texts)
            
            # Generate embeddings for valid texts
            response = self.client.embeddings.create(
                model=self.model,
                input=valid_texts,
                encoding_format="float"
            )
            
            # Prepare result list
            results = [None] * len(texts)
            
            # Fill in the embeddings for valid texts
            for i, embedding_data in enumerate(response.data):
                original_index = valid_indices[i]
                embedding = embedding_data.embedding
                
                # Validate embedding dimension
                if len(embedding) == self.dimension:
                    results[original_index] = embedding
                else:
                    logger.error(f"Unexpected embedding dimension for text {original_index}: {len(embedding)}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [None] * len(texts)
    
    def get_model_info(self) -> dict:
        """
        Get information about the embedding model being used.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model": self.model,
            "dimension": self.dimension,
            "provider": "OpenAI"
        }

# Global instance
embedding_service = EmbeddingService()