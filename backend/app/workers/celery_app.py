from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "antibody_workers",
    broker=settings.CELERY_BROKER,
    backend=settings.CELERY_BACKEND,
    include=[
        "app.workers.extraction_worker",
        "app.workers.retrieval_worker",
        "app.workers.decay_worker"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Task routing (optional - for advanced setups with multiple queues)
celery_app.conf.task_routes = {
    "app.workers.extraction_worker.*": {"queue": "extraction"},
    "app.workers.retrieval_worker.*": {"queue": "retrieval"},
    "app.workers.decay_worker.*": {"queue": "decay"}
}


if __name__ == "__main__":
    celery_app.start()
