from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.models.claim import ContradictingSource
from app.services.adversarial_retriever import adversarial_retriever
from app.services.neo4j_client import neo4j_client
from app.utils.auth import get_current_user
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/retrieve", tags=["retrieval"])


class AdversarialRetrievalRequest(BaseModel):
    """Request model for adversarial retrieval"""
    claim_id: UUID
    target_languages: Optional[List[str]] = None
    max_results: int = 10


class SimilarSearchRequest(BaseModel):
    """Request model for similarity search"""
    query: str
    language: Optional[str] = None
    max_results: int = 10


@router.post("/adversarial", response_model=List[ContradictingSource], dependencies=[Depends(get_current_user)])
async def run_adversarial_retrieval(request: AdversarialRetrievalRequest):
    """
    Run adversarial retrieval to find contradicting sources for a claim

    This searches across multiple languages for sources that may contradict the given claim
    """
    # Get the claim
    claim = await neo4j_client.get_claim_by_id(request.claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {request.claim_id} not found"
        )

    # Run adversarial retrieval
    contradicting_sources = await adversarial_retriever.find_contradicting_sources(
        claim_id=request.claim_id,
        claim_text=claim.text,
        target_languages=request.target_languages,
        max_results=request.max_results
    )

    return contradicting_sources


@router.post("/similar", dependencies=[Depends(get_current_user)])
async def search_similar_claims(request: SimilarSearchRequest):
    """
    Search for semantically similar claims

    Useful for finding related claims or duplicates
    """
    results = await adversarial_retriever.search_similar_claims(
        query_text=request.query,
        language=request.language,
        max_results=request.max_results
    )

    return {
        "query": request.query,
        "results_count": len(results),
        "results": results
    }


@router.get("/stats", dependencies=[Depends(get_current_user)])
async def get_retrieval_stats():
    """Get statistics about the retrieval system"""

    # In production, get actual stats from Qdrant and Neo4j
    from app.services.qdrant_client import qdrant_service

    try:
        collection_info = await qdrant_service.get_collection_info()

        return {
            "vector_database": collection_info,
            "status": "operational"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
