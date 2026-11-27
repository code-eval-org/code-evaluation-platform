from uuid import UUID

from celery import Celery

from shared.config import settings

celery_app = Celery(
    "code-evaluation",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_default_queue="evaluation",
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.task_soft_time_limit_s,
    task_time_limit=settings.task_time_limit_s,
    broker_connection_retry_on_startup=True,
)

EVALUATION_TASK = "worker.tasks.evaluate_submission"


def enqueue_submission(submission_id: UUID | str):
    return celery_app.send_task(
        EVALUATION_TASK,
        args=[str(submission_id)],
        task_id=str(submission_id),
        queue="evaluation",
    )
