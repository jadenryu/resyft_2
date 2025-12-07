from typing import List, Dict, Any, Optional
from uuid import UUID
from app.services.embedding_service import embedding_service
from app.services.qdrant_client import qdrant_service
from app.services.neo4j_client import neo4j_client
from app.models.claim import ContradictingSource
from datetime import datetime


class AdversarialRetriever:
    """
    Service for adversarial retrieval - finding contradicting sources across languages
    """

    def __init__(self):
        self.default_target_languages = ["en", "es", "fr", "de", "zh", "ar", "ru", "ja"]
        self.similarity_threshold = 0.75
        self.max_results = 20

    async def find_contradicting_sources(
        self,
        claim_id: UUID,
        claim_text: str,
        target_languages: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[ContradictingSource]:
        """
        Find potentially contradicting sources for a claim across multiple languages

        Args:
            claim_id: ID of the claim to check
            claim_text: Text of the claim
            target_languages: Languages to search in (defaults to major languages)
            max_results: Maximum number of contradicting sources to return

        Returns:
            List of ContradictingSource objects
        """
        if target_languages is None:
            target_languages = self.default_target_languages

        # Generate embedding for the claim
        claim_embedding = await embedding_service.embed_claim(claim_text)

        # Search for semantically similar claims in vector database
        similar_claims = await qdrant_service.search_contradicting_claims(
            query_vector=claim_embedding,
            original_claim_id=claim_id,
            target_languages=target_languages,
            limit=self.max_results,
            score_threshold=self.similarity_threshold
        )

        # For each similar claim, assess if it actually contradicts
        contradicting_sources = []

        for similar_claim in similar_claims:
            # Get the full claim data from Neo4j
            similar_claim_data = await neo4j_client.get_claim_by_id(
                UUID(similar_claim["claim_id"])
            )

            if not similar_claim_data:
                continue

            # Check if claims contradict (simplified - in production use LLM)
            is_contradicting = await self._assess_contradiction(
                claim_text,
                similar_claim_data.text
            )

            if is_contradicting:
                contradicting_source = ContradictingSource(
                    url=similar_claim_data.source_url,
                    text=similar_claim_data.text,
                    language=similar_claim_data.language,
                    confidence_score=similar_claim["score"],
                    retrieved_at=datetime.utcnow()
                )
                contradicting_sources.append(contradicting_source)

                if len(contradicting_sources) >= max_results:
                    break

        # Update contradiction count in Neo4j if contradictions found
        if contradicting_sources:
            for _ in range(len(contradicting_sources)):
                await neo4j_client.increment_contradiction_count(claim_id)

        return contradicting_sources

    async def _assess_contradiction(
        self,
        claim1: str,
        claim2: str
    ) -> bool:
        """
        Assess if two claims contradict each other

        This is a simplified implementation. In production, use an LLM
        or fine-tuned NLI (Natural Language Inference) model.

        Args:
            claim1: First claim text
            claim2: Second claim text

        Returns:
            True if claims contradict, False otherwise
        """
        # Simplified heuristic approach
        # In production, use Grok or a dedicated NLI model

        # Check for negation patterns
        negation_words = ["not", "no", "never", "false", "incorrect", "untrue", "disproven"]

        claim1_lower = claim1.lower()
        claim2_lower = claim2.lower()

        # Simple check: if claims share keywords but one has negation
        claim1_has_negation = any(neg in claim1_lower for neg in negation_words)
        claim2_has_negation = any(neg in claim2_lower for neg in negation_words)

        # If one has negation and other doesn't, likely contradicting
        if claim1_has_negation != claim2_has_negation:
            # Check if they share significant keywords
            words1 = set(claim1_lower.split())
            words2 = set(claim2_lower.split())
            common_words = words1.intersection(words2)

            # Filter out common stop words
            stop_words = {"the", "a", "an", "is", "was", "are", "were", "in", "on", "at", "to", "for"}
            significant_common = common_words - stop_words

            if len(significant_common) >= 2:
                return True

        # For a production system, use this approach instead:
        # from app.services.grok_client import grok_client
        # result = await grok_client.assess_contradiction(claim1, claim2)
        # return result["contradicts"]

        return False

    async def search_similar_claims(
        self,
        query_text: str,
        language: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar claims to a query

        Args:
            query_text: The search query
            language: Optional language filter
            max_results: Maximum number of results

        Returns:
            List of similar claims with metadata
        """
        # Generate embedding for query
        query_embedding = await embedding_service.embed_query(query_text)

        # Search in vector database
        similar_claims = await qdrant_service.search_similar_claims(
            query_vector=query_embedding,
            limit=max_results,
            language=language,
            score_threshold=0.7
        )

        # Enrich with full claim data from Neo4j
        enriched_results = []
        for result in similar_claims:
            claim_data = await neo4j_client.get_claim_by_id(UUID(result["claim_id"]))
            if claim_data:
                enriched_results.append({
                    "claim": claim_data,
                    "similarity_score": result["score"],
                    "matched_payload": result["payload"]
                })

        return enriched_results


# Singleton instance
adversarial_retriever = AdversarialRetriever()
