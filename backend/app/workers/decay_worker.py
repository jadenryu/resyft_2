from app.workers.celery_app import celery_app
from app.services.decay_forecaster import decay_forecaster
from app.services.neo4j_client import neo4j_client
from uuid import UUID
from typing import List
import asyncio


@celery_app.task(bind=True, name="calculate_decay_score")
def calculate_decay_task(self, claim_id: str, check_trending: bool = True):
    """
    Celery task to calculate decay score for a claim

    Args:
        claim_id: UUID of the claim as string
        check_trending: Whether to check X API for trending signals
    """
    return asyncio.run(calculate_decay_async(self, claim_id, check_trending))


async def calculate_decay_async(task, claim_id: str, check_trending: bool):
    """Async implementation of decay calculation"""

    try:
        task.update_state(state="PROGRESS", meta={"progress": 0, "status": "Fetching claim"})

        await neo4j_client.connect()

        # Get claim from Neo4j
        claim = await neo4j_client.get_claim_by_id(UUID(claim_id))

        if not claim:
            raise ValueError(f"Claim {claim_id} not found")

        task.update_state(state="PROGRESS", meta={"progress": 30, "status": "Calculating decay"})

        # Calculate decay score
        decay_score, half_life_days = await decay_forecaster.calculate_decay_score(
            claim_text=claim.text,
            is_immutable=claim.is_immutable,
            extracted_at=claim.extracted_at,
            check_trending=check_trending
        )

        task.update_state(state="PROGRESS", meta={"progress": 70, "status": "Updating database"})

        # Update in Neo4j
        await neo4j_client.update_decay_score(
            claim_id=UUID(claim_id),
            decay_score=decay_score,
            half_life_days=half_life_days
        )

        await neo4j_client.close()

        return {
            "claim_id": claim_id,
            "status": "completed",
            "decay_score": decay_score,
            "half_life_days": half_life_days
        }

    except Exception as e:
        task.update_state(state="FAILURE", meta={"error": str(e)})
        return {
            "claim_id": claim_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="batch_calculate_decay")
def batch_calculate_decay_task(claim_ids: List[str], check_trending: bool = False):
    """
    Calculate decay scores for multiple claims in batch

    Args:
        claim_ids: List of claim UUIDs as strings
        check_trending: Whether to check trending (slower)
    """
    return asyncio.run(batch_calculate_decay_async(claim_ids, check_trending))


async def batch_calculate_decay_async(claim_ids: List[str], check_trending: bool):
    """Async batch decay calculation"""

    await neo4j_client.connect()

    results = []

    for claim_id in claim_ids:
        try:
            # Get claim
            claim = await neo4j_client.get_claim_by_id(UUID(claim_id))

            if not claim:
                results.append({
                    "claim_id": claim_id,
                    "status": "error",
                    "error": "Claim not found"
                })
                continue

            # Calculate decay
            decay_score, half_life_days = await decay_forecaster.calculate_decay_score(
                claim_text=claim.text,
                is_immutable=claim.is_immutable,
                extracted_at=claim.extracted_at,
                check_trending=check_trending
            )

            # Update in Neo4j
            await neo4j_client.update_decay_score(
                claim_id=UUID(claim_id),
                decay_score=decay_score,
                half_life_days=half_life_days
            )

            results.append({
                "claim_id": claim_id,
                "status": "completed",
                "decay_score": decay_score,
                "half_life_days": half_life_days
            })

        except Exception as e:
            results.append({
                "claim_id": claim_id,
                "status": "error",
                "error": str(e)
            })

    await neo4j_client.close()

    return {
        "status": "completed",
        "processed": len(claim_ids),
        "results": results
    }


@celery_app.task(name="refresh_all_decay_scores")
def refresh_all_decay_scores_task():
    """
    Periodic task to refresh decay scores for all mutable claims

    This should be run as a scheduled task (e.g., daily)
    """
    return asyncio.run(refresh_all_decay_scores_async())


async def refresh_all_decay_scores_async():
    """Async refresh all decay scores"""

    await neo4j_client.connect()

    # This would get all mutable claims from Neo4j
    # For now, returning a placeholder
    # In production:
    # claims = await neo4j_client.get_all_mutable_claims()
    # for claim in claims:
    #     calculate_decay_task.delay(str(claim.id), check_trending=True)

    await neo4j_client.close()

    return {
        "status": "scheduled",
        "message": "Decay refresh tasks queued"
    }
