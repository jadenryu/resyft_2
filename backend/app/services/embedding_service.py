import cohere
from typing import List, Union
from app.config import settings


class EmbeddingService:
    """Service for generating multilingual embeddings using Cohere"""

    def __init__(self):
        self.api_key = settings.COHERE_API_KEY
        self.model = settings.COHERE_MODEL
        self.client = cohere.AsyncClient(api_key=self.api_key)

    async def embed_text(self, text: str, input_type: str = "search_document") -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: The text to embed
            input_type: Either "search_document" or "search_query"

        Returns:
            1024-dimensional embedding vector
        """
        response = await self.client.embed(
            texts=[text],
            model=self.model,
            input_type=input_type,
            embedding_types=["float"]
        )

        return response.embeddings.float[0]

    async def embed_batch(
        self,
        texts: List[str],
        input_type: str = "search_document"
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch

        Args:
            texts: List of texts to embed
            input_type: Either "search_document" or "search_query"

        Returns:
            List of 1024-dimensional embedding vectors
        """
        # Cohere has a batch limit of 96 texts per request
        batch_size = 96
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            response = await self.client.embed(
                texts=batch,
                model=self.model,
                input_type=input_type,
                embedding_types=["float"]
            )

            all_embeddings.extend(response.embeddings.float)

        return all_embeddings

    async def embed_claim(self, claim_text: str) -> List[float]:
        """
        Generate embedding specifically for a claim (uses search_document type)

        Args:
            claim_text: The claim text

        Returns:
            Embedding vector
        """
        return await self.embed_text(claim_text, input_type="search_document")

    async def embed_query(self, query_text: str) -> List[float]:
        """
        Generate embedding for a search query (uses search_query type)

        Args:
            query_text: The search query

        Returns:
            Embedding vector
        """
        return await self.embed_text(query_text, input_type="search_query")

    async def close(self):
        """Close the Cohere client"""
        await self.client.close()


# Singleton instance
embedding_service = EmbeddingService()
