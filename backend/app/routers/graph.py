from fastapi import APIRouter, Depends, HTTPException, status
from app.models.claim import ClaimWithDependencies, ClaimImpact, VulnerableClaim
from app.services.neo4j_client import neo4j_client
from app.utils.auth import get_current_user
from uuid import UUID
from typing import List

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/claim/{claim_id}", response_model=ClaimWithDependencies, dependencies=[Depends(get_current_user)])
async def get_claim_with_dependencies(claim_id: UUID):
    """
    Get a claim with its immediate dependencies and dependents

    Returns the claim node along with all claims it supports and all claims that support it
    """
    claim = await neo4j_client.get_claim_with_dependencies(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    return claim


@router.get("/impact/{claim_id}", response_model=ClaimImpact, dependencies=[Depends(get_current_user)])
async def get_claim_impact(claim_id: UUID):
    """
    Calculate the downstream impact of a claim

    Returns the impact score and list of all affected claims in the dependency chain
    """
    # First check if claim exists
    claim = await neo4j_client.get_claim_by_id(claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {claim_id} not found"
        )

    # Calculate impact
    impact = await neo4j_client.get_downstream_impact(claim_id)

    return impact


@router.get("/vulnerable", response_model=List[VulnerableClaim], dependencies=[Depends(get_current_user)])
async def get_vulnerable_claims(limit: int = 50, offset: int = 0):
    """
    Get the most vulnerable claims sorted by vulnerability score

    Vulnerability score is calculated as: decay_score × dependency_weight × (contradiction_count + 1)

    This is the primary endpoint for populating the triage queue
    """
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100"
        )

    vulnerable_claims = await neo4j_client.get_vulnerable_claims(limit=limit, offset=offset)

    return vulnerable_claims


@router.get("/article/{article_id}/claims", dependencies=[Depends(get_current_user)])
async def get_article_claims(article_id: str):
    """
    Get all claims extracted from a specific article

    Returns a list of claims with their health scores
    """
    # This would query Neo4j for all claims with matching articleId
    # For now, returning a placeholder
    # In production:
    # claims = await neo4j_client.get_claims_by_article(article_id)

    return {
        "article_id": article_id,
        "claims": [],
        "message": "Implementation pending"
    }
