from app.workers.celery_app import celery_app
from app.services.grok_client import grok_client
from app.services.neo4j_client import neo4j_client
from app.services.qdrant_client import qdrant_service
from app.services.embedding_service import embedding_service
from app.models.claim import ClaimNode
from typing import Dict, Any
import asyncio


@celery_app.task(bind=True, name="extract_claims_from_article")
def extract_claims_task(self, article_data: Dict[str, Any], job_id: str):
    """
    Celery task to extract claims from an article

    Args:
        article_data: Dictionary containing article_id, title, content, source_urls
        job_id: Job ID for status tracking
    """
    return asyncio.run(extract_claims_async(self, article_data, job_id))


async def extract_claims_async(task, article_data: Dict[str, Any], job_id: str):
    """Async implementation of claim extraction"""

    try:
        # Update job status to processing
        task.update_state(state="PROGRESS", meta={"progress": 0, "status": "Starting extraction"})

        # Extract claims using Grok API
        task.update_state(state="PROGRESS", meta={"progress": 10, "status": "Extracting claims with Grok"})

        claims = await grok_client.extract_claims(
            article_text=article_data["content"],
            article_id=article_data["article_id"],
            source_urls=article_data.get("source_urls", [])
        )

        task.update_state(state="PROGRESS", meta={"progress": 40, "status": f"Extracted {len(claims)} claims"})

        # Create claim nodes in Neo4j
        claim_nodes = []
        for i, claim_create in enumerate(claims):
            # Create ClaimNode
            claim_node = ClaimNode(
                text=claim_create.text,
                source_url=claim_create.source_url,
                article_id=claim_create.article_id,
                is_immutable=claim_create.is_immutable,
                language=claim_create.language
            )

            # Store in Neo4j
            await neo4j_client.create_claim_node(claim_node)
            claim_nodes.append(claim_node)

            progress = 40 + int((i / len(claims)) * 30)
            task.update_state(
                state="PROGRESS",
                meta={"progress": progress, "status": f"Storing claims in graph ({i+1}/{len(claims)})"}
            )

        task.update_state(state="PROGRESS", meta={"progress": 70, "status": "Generating embeddings"})

        # Generate embeddings and store in Qdrant
        await qdrant_service.connect()

        for i, claim_node in enumerate(claim_nodes):
            # Generate embedding
            embedding = await embedding_service.embed_claim(claim_node.text)

            # Store in Qdrant
            await qdrant_service.upsert_claim_embedding(
                claim_id=claim_node.id,
                embedding=embedding,
                article_id=claim_node.article_id,
                language=claim_node.language,
                source_url=claim_node.source_url,
                extracted_at=claim_node.extracted_at
            )

            progress = 70 + int((i / len(claim_nodes)) * 20)
            task.update_state(
                state="PROGRESS",
                meta={"progress": progress, "status": f"Generating embeddings ({i+1}/{len(claim_nodes)})"}
            )

        await qdrant_service.close()

        task.update_state(state="PROGRESS", meta={"progress": 90, "status": "Finalizing"})

        # Return success
        return {
            "job_id": job_id,
            "status": "completed",
            "claims_extracted": len(claims),
            "claim_ids": [str(c.id) for c in claim_nodes]
        }

    except Exception as e:
        task.update_state(state="FAILURE", meta={"error": str(e)})
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }


@celery_app.task(name="batch_extract_claims")
def batch_extract_claims_task(articles: list[Dict[str, Any]]):
    """
    Extract claims from multiple articles in batch

    Args:
        articles: List of article dictionaries
    """
    results = []

    for article in articles:
        # Queue individual extraction tasks
        result = extract_claims_task.delay(article, f"batch_{article['article_id']}")
        results.append(result.id)

    return {
        "status": "queued",
        "tasks": results,
        "count": len(articles)
    }
