"""
Embedding Service for RAG System

Provides text embedding functionality using various models:
- Sentence Transformers (local, high quality)
- OpenAI Embeddings (API-based)
- Hugging Face models
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_gpu: bool = False):
        """
        Initialize embedding service

        Args:
            model_name: Name of the embedding model
            use_gpu: Whether to use GPU for embeddings
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer

            # Set device
            device = 'cuda' if self.use_gpu else 'cpu'

            # Initialize model
            self.model = SentenceTransformer(self.model_name, device=device)
            logger.info(f"Initialized SentenceTransformer model: {self.model_name} on {device}")

        except ImportError:
            logger.warning("sentence-transformers not installed. Install with: pip install sentence-transformers")
            self.model = None

    def encode_text(self, text: str) -> List[float]:
        """Encode a single text into embedding vector"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")

        if not text or not text.strip():
            return [0.0] * self.get_dimension()

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode multiple texts into embedding vectors"""
        if self.model is None:
            raise RuntimeError("Embedding model not initialized")

        # Filter out empty texts
        valid_texts = []
        indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                indices.append(i)

        if not valid_texts:
            dimension = self.get_dimension()
            return [[0.0] * dimension] * len(texts)

        # Encode in batches
        embeddings = []
        for i in range(0, len(valid_texts), batch_size):
            batch_texts = valid_texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch_texts, convert_to_numpy=True)
            embeddings.extend(batch_embeddings.tolist())

        # Reconstruct full list with zeros for empty texts
        result = [[0.0] * self.get_dimension()] * len(texts)
        for idx, embedding in zip(indices, embeddings):
            result[idx] = embedding

        return result

    def get_dimension(self) -> int:
        """Get the dimension of embedding vectors"""
        if self.model is None:
            return 384  # Default dimension for all-MiniLM-L6-v2
        return self.model.get_sentence_embedding_dimension()

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class OpenAIEmbeddingService:
    """OpenAI embeddings service"""

    def __init__(self, api_key: Optional[str] = None, model: str = "text-embedding-ada-002"):
        """
        Initialize OpenAI embedding service

        Args:
            api_key: OpenAI API key (if None, uses environment variable)
            model: OpenAI embedding model name
        """
        try:
            from openai import OpenAI

            self.api_key = api_key or os.getenv('OPENAI_API_KEY')
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")

            self.client = OpenAI(api_key=self.api_key)
            self.model = model
            logger.info(f"Initialized OpenAI embedding service with model: {model}")

        except ImportError:
            raise ImportError("OpenAI not installed. Install with: pip install openai")

    def encode_text(self, text: str) -> List[float]:
        """Encode text using OpenAI"""
        if not text or not text.strip():
            return [0.0] * 1536  # Ada-002 dimension

        response = self.client.embeddings.create(
            input=text,
            model=self.model
        )

        return response.data[0].embedding

    def encode_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Encode multiple texts using OpenAI"""
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [text for text in texts if text and text.strip()]

        if not valid_texts:
            return [[0.0] * 1536] * len(texts)

        # OpenAI has a limit on batch size
        all_embeddings = []
        for i in range(0, len(valid_texts), batch_size):
            batch_texts = valid_texts[i:i + batch_size]

            response = self.client.embeddings.create(
                input=batch_texts,
                model=self.model
            )

            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)

        # Reconstruct full list
        result = [[0.0] * 1536] * len(texts)
        embedding_idx = 0
        for i, text in enumerate(texts):
            if text and text.strip():
                result[i] = all_embeddings[embedding_idx]
                embedding_idx += 1

        return result

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return 1536  # Ada-002 dimension


def create_embedding_service(service_type: str = "sentence-transformers", **kwargs) -> EmbeddingService:
    """
    Factory function to create embedding service

    Args:
        service_type: Type of service ('sentence-transformers', 'openai')
        **kwargs: Additional arguments for service initialization
    """
    if service_type == "sentence-transformers":
        return EmbeddingService(**kwargs)
    elif service_type == "openai":
        return OpenAIEmbeddingService(**kwargs)
    else:
        raise ValueError(f"Unknown service type: {service_type}")