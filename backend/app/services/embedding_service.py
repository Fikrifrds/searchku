import openai
import os
from typing import List, Optional, Literal
from dotenv import load_dotenv
import logging

# Import Google GenAI only when needed to avoid conflicts
try:
    import google.generativeai as genai_client
    GENAI_AVAILABLE = True
except ImportError as e:
    GENAI_AVAILABLE = False
    genai_client = None
    print(f"Warning: google-generativeai import failed: {e}")

load_dotenv()

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = os.getenv("EMBEDDING_PROVIDER", "openai")
        self.dimension = int(os.getenv("EMBEDDING_DIMENSION", 1536))
        self._initialized = False

        # Set model based on provider using provider-specific environment variables
        if self.provider == "openai":
            self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        elif self.provider == "gemini":
            self.model = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
        else:
            self.model = "text-embedding-3-large"  # Default fallback

        # Provider-specific clients
        self.openai_client = None

    def _initialize(self):
        if self._initialized:
            return

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")

            self.openai_client = openai.OpenAI(api_key=api_key)

            # Use reduced dimensions for text-embedding-3-large to maintain pgvector compatibility
            if self.model == "text-embedding-3-large" and self.dimension > 2000:
                self.dimension = 1536  # Reduce to 1536 for pgvector compatibility
                logger.info(f"Reducing {self.model} dimensions from {os.getenv('EMBEDDING_DIMENSION', 1536)} to {self.dimension} for pgvector compatibility")

        elif self.provider == "gemini":
            if not GENAI_AVAILABLE:
                raise ValueError("google-generativeai library is required for Gemini provider")

            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")

            genai_client.configure(api_key=api_key)

        else:
            raise ValueError(f"Unsupported embedding provider: {self.provider}")

        self._initialized = True
        logger.info(f"Embedding service initialized: provider={self.provider}, model={self.model}, dimensions={self.dimension}")

    async def generate_embedding(self, text: str, task_type: Optional[str] = None) -> Optional[List[float]]:
        """
        Generate embedding for a given text.

        Args:
            text: The text to generate embedding for
            task_type: Task type for Gemini embeddings (SEMANTIC_SIMILARITY, CLASSIFICATION, etc.)

        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        self._initialize()

        try:
            # Clean and prepare text
            cleaned_text = text.strip().replace("\n", " ")

            if not cleaned_text:
                logger.warning("Empty text provided for embedding generation")
                return None

            if self.provider == "openai":
                return await self._generate_openai_embedding(cleaned_text)
            elif self.provider == "gemini":
                return await self._generate_gemini_embedding(cleaned_text, task_type)

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None

    async def _generate_openai_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding using OpenAI API."""
        try:
            # Generate embedding with specific dimensions if supported
            embedding_params = {
                "model": self.model,
                "input": text,
                "encoding_format": "float"
            }

            # Add dimensions parameter for models that support it
            if self.model in ["text-embedding-3-large", "text-embedding-3-small"]:
                embedding_params["dimensions"] = self.dimension

            response = self.openai_client.embeddings.create(**embedding_params)
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
                logger.debug(f"OpenAI embedding conversion successful: {len(embedding)} floats")
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to convert embedding elements to floats: {str(e)}")
                return None

            return embedding

        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            return None

    async def _generate_gemini_embedding(self, text: str, task_type: Optional[str] = None) -> Optional[List[float]]:
        """Generate embedding using Gemini API."""
        try:
            # Default task type if not specified
            if task_type is None:
                task_type = "RETRIEVAL_DOCUMENT"

            # Use the traditional google-generativeai API
            # Note: output_dimensionality is not supported in this version
            result = genai_client.embed_content(
                model=self.model,
                content=text,
                task_type=task_type
            )

            # Extract embedding values
            embedding = result['embedding']

            # Convert to list if needed
            if not isinstance(embedding, list):
                embedding = list(embedding)

            # Ensure all elements are floats
            embedding = [float(x) for x in embedding]

            # Handle dimension mismatch
            if len(embedding) != self.dimension:
                logger.warning(f"Gemini embedding dimension ({len(embedding)}) differs from expected ({self.dimension})")

                if len(embedding) < self.dimension:
                    # Pad with zeros if embedding is smaller
                    padding = [0.0] * (self.dimension - len(embedding))
                    embedding.extend(padding)
                    logger.info(f"Padded Gemini embedding from {len(embedding) - len(padding)} to {len(embedding)} dimensions")
                else:
                    # Truncate if embedding is larger
                    embedding = embedding[:self.dimension]
                    logger.info(f"Truncated Gemini embedding to {self.dimension} dimensions")

            logger.debug(f"Gemini embedding conversion successful: {len(embedding)} floats")
            return embedding

        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {str(e)}")
            return None

    async def generate_embeddings_batch(self, texts: List[str], task_type: Optional[str] = None) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of texts to generate embeddings for
            task_type: Task type for Gemini embeddings

        Returns:
            List of embedding vectors (or None for failed generations)
        """
        self._initialize()

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

            if self.provider == "openai":
                return await self._generate_openai_embeddings_batch(texts, valid_texts, valid_indices)
            elif self.provider == "gemini":
                return await self._generate_gemini_embeddings_batch(texts, valid_texts, valid_indices, task_type)

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            return [None] * len(texts)

    async def _generate_openai_embeddings_batch(self, texts: List[str], valid_texts: List[str], valid_indices: List[int]) -> List[Optional[List[float]]]:
        """Generate batch embeddings using OpenAI API."""
        try:
            # Generate embeddings for valid texts
            embedding_params = {
                "model": self.model,
                "input": valid_texts,
                "encoding_format": "float"
            }

            # Add dimensions parameter for models that support it
            if self.model in ["text-embedding-3-large", "text-embedding-3-small"]:
                embedding_params["dimensions"] = self.dimension

            response = self.openai_client.embeddings.create(**embedding_params)

            # Prepare result list
            results = [None] * len(texts)

            # Fill in the embeddings for valid texts
            for i, embedding_data in enumerate(response.data):
                original_index = valid_indices[i]
                embedding = embedding_data.embedding

                # Validate embedding dimension
                if len(embedding) == self.dimension:
                    results[original_index] = [float(x) for x in embedding]
                else:
                    logger.error(f"Unexpected embedding dimension for text {original_index}: {len(embedding)}")

            return results

        except Exception as e:
            logger.error(f"Error generating OpenAI batch embeddings: {str(e)}")
            return [None] * len(texts)

    async def _generate_gemini_embeddings_batch(self, texts: List[str], valid_texts: List[str], valid_indices: List[int], task_type: Optional[str] = None) -> List[Optional[List[float]]]:
        """Generate batch embeddings using Gemini API."""
        try:
            # Default task type if not specified
            if task_type is None:
                task_type = "RETRIEVAL_DOCUMENT"

            # Prepare result list
            results = [None] * len(texts)

            # Generate embeddings one by one for Gemini (batch not supported in traditional API)
            for i, text in enumerate(valid_texts):
                try:
                    result = genai_client.embed_content(
                        model=self.model,
                        content=text,
                        task_type=task_type
                    )

                    original_index = valid_indices[i]
                    embedding = result['embedding']

                    # Convert to list if needed
                    if not isinstance(embedding, list):
                        embedding = list(embedding)

                    # Ensure all elements are floats
                    embedding = [float(x) for x in embedding]

                    # Handle dimension mismatch
                    if len(embedding) != self.dimension:
                        if len(embedding) < self.dimension:
                            # Pad with zeros if embedding is smaller
                            padding = [0.0] * (self.dimension - len(embedding))
                            embedding.extend(padding)
                        else:
                            # Truncate if embedding is larger
                            embedding = embedding[:self.dimension]

                    results[original_index] = embedding

                except Exception as embed_error:
                    logger.error(f"Error generating Gemini embedding for text {valid_indices[i]}: {str(embed_error)}")

            return results

        except Exception as e:
            logger.error(f"Error generating Gemini batch embeddings: {str(e)}")
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
            "provider": self.provider.upper()
        }

# Global instance
embedding_service = EmbeddingService()