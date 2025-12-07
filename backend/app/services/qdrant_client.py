from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from typing import List, Optional, Dict, Any
from app.config import settings
from uuid import UUID
from datetime import datetime


class QdrantService:
    """Client for Qdrant vector database operations"""

    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.api_key = settings.QDRANT_API_KEY
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.client: Optional[AsyncQdrantClient] = None
        self.vector_size = 1024  # Cohere embed-multilingual-v3 dimension

    async def connect(self):
        """Initialize connection to Qdrant"""
        self.client = AsyncQdrantClient(
            host=self.host,
            port=self.port,
            api_key=self.api_key,
        )

    async def close(self):
        """Close Qdrant connection"""
        if self.client:
            await self.client.close()

    async def create_collection(self, collection_name: Optional[str] = None):
        """Create a new collection for claim embeddings"""
        collection_name = collection_name or self.collection_name

        await self.client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=self.vector_size,
                distance=Distance.COSINE
            )
        )

    async def collection_exists(self, collection_name: Optional[str] = None) -> bool:
        """Check if collection exists"""
        collection_name = collection_name or self.collection_name
        collections = await self.client.get_collections()
        return any(c.name == collection_name for c in collections.collections)

    async def upsert_claim_embedding(
        self,
        claim_id: UUID,
        embedding: List[float],
        article_id: str,
        language: str,
        source_url: str,
        extracted_at: datetime
    ):
        """Insert or update a claim embedding"""
        point = PointStruct(
            id=str(claim_id),
            vector=embedding,
            payload={
                "claimId": str(claim_id),
                "articleId": article_id,
                "language": language,
                "sourceUrl": source_url,
                "extractedAt": extracted_at.isoformat()
            }
        )

        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

    async def search_similar_claims(
        self,
        query_vector: List[float],
        limit: int = 10,
        language: Optional[str] = None,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar claims

        Args:
            query_vector: The embedding vector to search for
            limit: Maximum number of results
            language: Optional language filter
            score_threshold: Minimum similarity score (0-1)

        Returns:
            List of similar claims with scores
        """
        search_filter = None
        if language:
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="language",
                        match=MatchValue(value=language)
                    )
                ]
            )

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter
        )

        return [
            {
                "claim_id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            for result in results
        ]

    async def search_contradicting_claims(
        self,
        query_vector: List[float],
        original_claim_id: UUID,
        target_languages: Optional[List[str]] = None,
        limit: int = 20,
        score_threshold: float = 0.75
    ) -> List[Dict[str, Any]]:
        """
        Search for potentially contradicting claims in specified languages

        This searches for semantically similar claims which may contradict
        the original claim. Further processing is needed to determine
        actual contradiction.

        Args:
            query_vector: Embedding of the claim to check
            original_claim_id: ID of the original claim (to exclude from results)
            target_languages: Languages to search in
            limit: Maximum number of results
            score_threshold: Minimum similarity score

        Returns:
            List of potentially contradicting claims
        """
        # Build filter to exclude the original claim
        must_not = [
            FieldCondition(
                key="claimId",
                match=MatchValue(value=str(original_claim_id))
            )
        ]

        # Add language filter if specified
        must = []
        if target_languages:
            # Qdrant doesn't support OR in filters easily, so we'll search without language filter
            # and filter in post-processing if needed
            pass

        search_filter = Filter(must_not=must_not)

        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter
        )

        # Post-process to filter by language if needed
        filtered_results = results
        if target_languages:
            filtered_results = [
                r for r in results
                if r.payload.get("language") in target_languages
            ]

        return [
            {
                "claim_id": result.id,
                "score": result.score,
                "language": result.payload.get("language"),
                "source_url": result.payload.get("sourceUrl"),
                "extracted_at": result.payload.get("extractedAt")
            }
            for result in filtered_results
        ]

    async def delete_claim(self, claim_id: UUID):
        """Delete a claim embedding from the collection"""
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=[str(claim_id)]
        )

    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        info = await self.client.get_collection(collection_name=self.collection_name)
        return {
            "name": info.config.params.vectors.name,
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance.name,
            "points_count": info.points_count
        }


# Singleton instance
qdrant_service = QdrantService()
