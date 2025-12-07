from fastapi import APIRouter, Depends, HTTPException, status
from app.models.remediation import RemediationCreate, Remediation
from app.models.claim import VulnerableClaim
from app.services.neo4j_client import neo4j_client
from app.utils.auth import get_current_user, require_role
from app.models.user import TokenData
from uuid import UUID
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/triage", tags=["triage"])

# In-memory remediation storage (in production, use PostgreSQL)
remediations_db = {}


@router.get("/queue", response_model=List[VulnerableClaim], dependencies=[Depends(get_current_user)])
async def get_triage_queue(limit: int = 50, offset: int = 0):
    """
    Get the prioritized remediation queue

    Returns vulnerable claims sorted by vulnerability score (highest first)
    """
    if limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100"
        )

    vulnerable_claims = await neo4j_client.get_vulnerable_claims(limit=limit, offset=offset)

    return vulnerable_claims


@router.post("/action", response_model=Remediation)
async def record_remediation_action(
    action: RemediationCreate,
    current_user: TokenData = Depends(require_role("editor"))
):
    """
    Record a remediation action on a claim

    Requires editor or admin role

    Actions:
    - verified: Claim verified as accurate
    - updated: Claim text updated with corrections
    - flagged: Claim flagged for further review
    - dismissed: Contradictions dismissed as false positives
    """
    # Check if claim exists
    claim = await neo4j_client.get_claim_by_id(action.claim_id)

    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Claim {action.claim_id} not found"
        )

    # Create remediation record
    from uuid import uuid4

    remediation = Remediation(
        id=uuid4(),
        claim_id=action.claim_id,
        user_id=UUID(current_user.user_id),
        action=action.action,
        previous_text=action.previous_text,
        new_text=action.new_text,
        timestamp=datetime.utcnow()
    )

    # Store remediation
    remediations_db[str(remediation.id)] = remediation

    # If action is "updated", update the claim in Neo4j
    # if action.action == "updated" and action.new_text:
    #     await neo4j_client.update_claim_text(action.claim_id, action.new_text)

    return remediation


@router.get("/remediation/{remediation_id}", response_model=Remediation, dependencies=[Depends(get_current_user)])
async def get_remediation(remediation_id: UUID):
    """Get details of a specific remediation"""

    remediation = remediations_db.get(str(remediation_id))

    if not remediation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Remediation {remediation_id} not found"
        )

    return remediation


@router.get("/claim/{claim_id}/history", response_model=List[Remediation], dependencies=[Depends(get_current_user)])
async def get_claim_remediation_history(claim_id: UUID):
    """Get remediation history for a specific claim"""

    history = [
        r for r in remediations_db.values()
        if r.claim_id == claim_id
    ]

    # Sort by timestamp, newest first
    history.sort(key=lambda r: r.timestamp, reverse=True)

    return history


@router.get("/stats", dependencies=[Depends(get_current_user)])
async def get_triage_stats():
    """Get triage and remediation statistics"""

    total_remediations = len(remediations_db)

    # Count by action type
    action_counts = {}
    for remediation in remediations_db.values():
        action = remediation.action
        action_counts[action] = action_counts.get(action, 0) + 1

    # Get vulnerable claims count
    vulnerable_claims = await neo4j_client.get_vulnerable_claims(limit=1000)

    return {
        "total_remediations": total_remediations,
        "remediations_by_action": action_counts,
        "vulnerable_claims_count": len(vulnerable_claims),
        "timestamp": datetime.utcnow().isoformat()
    }
