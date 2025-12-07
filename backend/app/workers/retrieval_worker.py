from app.workers.celery_app import celery_app
from app.services.adversarial_retriever import adversarial_retriever
from app.services.neo4j_client import neo4j_client
from uuid import UUID
from typing import List, Optional
import asyncio


@celery_app.task(bind=True, name="run_adversarial_retrieval")
def adversarial_retrieval_task(
    self,
    claim_id: str,
    claim_text: str,
    target_languages: Optional[List[str]] = None
):
    """
    Celery task to run adversarial retrieval for a claim

    Args:
        claim_id: UUID of the claim as string
        claim_text: Text of the claim
        target_languages: Optional list of target languages
    """
    return asyncio.run(adversarial_retrieval_async(self, claim_id, claim_text, target_languages))


async def adversarial_retrieval_async(
    task,
    claim_id: str,
    claim_text: str,
    target_languages: Optional[List[str]]
):
    """Async implementation of adversarial retrieval"""

    try:
        task.update_state(state="PROGRESS", meta={"progress": 0, "status": "Starting adversarial retrieval"})

        # Run adversarial retrieval
        contradicting_sources = await adversarial_retriever.find_contradicting_sources(
            claim_id=UUID(claim_id),
            claim_text=claim_text,
            target_languages=target_languages,
            max_results=20
        )

        task.update_state(
            state="PROGRESS",
            meta={"progress": 80, "status": f"Found {len(contradicting_sources)} contradictions"}
        )

        # Return results
        return {
            "claim_id": claim_id,
            "status": "completed",
            "contradictions_found": len(contradicting_sources),
            "contradicting_sources": [
                {
                    "url": src.url,
                    "text": src.text,
                    "language": src.language,
                    "confidence": src.confidence_score
                }
                for src in contradicting_sources
            ]
        }

    except Exception as e:
        task.update_state(state="FAILURE", meta={"error": str(e)})
        return {
            "claim_id": claim_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="batch_adversarial_retrieval")
def batch_adversarial_retrieval_task(claim_ids: List[str], target_languages: Optional[List[str]] = None):
    """
    Run adversarial retrieval for multiple claims

    Args:
        claim_ids: List of claim UUIDs as strings
        target_languages: Optional target languages
    """
    return asyncio.run(batch_adversarial_retrieval_async(claim_ids, target_languages))


async def batch_adversarial_retrieval_async(claim_ids: List[str], target_languages: Optional[List[str]]):
    """Async batch adversarial retrieval"""

    results = []

    await neo4j_client.connect()

    for claim_id in claim_ids:
        try:
            # Get claim text
            claim = await neo4j_client.get_claim_by_id(UUID(claim_id))

            if not claim:
                results.append({
                    "claim_id": claim_id,
                    "status": "error",
                    "error": "Claim not found"
                })
                continue

            # Run retrieval
            contradicting_sources = await adversarial_retriever.find_contradicting_sources(
                claim_id=UUID(claim_id),
                claim_text=claim.text,
                target_languages=target_languages,
                max_results=20
            )

            results.append({
                "claim_id": claim_id,
                "status": "completed",
                "contradictions_found": len(contradicting_sources)
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
