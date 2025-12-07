from fastapi import APIRouter, Depends, HTTPException, status
from app.models.claim import ArticleIngestRequest, ArticleIngestResponse, JobStatus
from app.utils.auth import get_current_user
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])

# In-memory job storage (in production, use Redis or PostgreSQL)
jobs_db = {}


@router.post("/article", response_model=ArticleIngestResponse, dependencies=[Depends(get_current_user)])
async def ingest_article(article: ArticleIngestRequest):
    """
    Ingest a new article for claim extraction

    This endpoint queues the article for processing and returns a job ID
    """
    # Generate job ID
    job_id = str(uuid4())

    # Create job status record
    job = JobStatus(
        job_id=job_id,
        status="queued",
        progress=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    jobs_db[job_id] = job

    # Queue the article for processing
    # In production, this would use Celery:
    # from app.workers.extraction_worker import extract_claims_task
    # extract_claims_task.delay(article.model_dump(), job_id)

    return ArticleIngestResponse(
        job_id=job_id,
        status="queued",
        message=f"Article '{article.title}' queued for processing"
    )


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get the status of an ingestion job"""

    job = jobs_db.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return job


@router.get("/jobs", response_model=list[JobStatus], dependencies=[Depends(get_current_user)])
async def list_jobs(limit: int = 50, offset: int = 0):
    """List all ingestion jobs with pagination"""

    all_jobs = sorted(
        jobs_db.values(),
        key=lambda j: j.created_at,
        reverse=True
    )

    return all_jobs[offset:offset + limit]
