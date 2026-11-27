from dataclasses import dataclass
import os
import socket


@dataclass(frozen=True)
class WorkerSettings:
    worker_id: str = os.getenv("WORKER_ID", socket.gethostname())
    queue_name: str = os.getenv("CELERY_QUEUE", "evaluation")


worker_settings = WorkerSettings()
