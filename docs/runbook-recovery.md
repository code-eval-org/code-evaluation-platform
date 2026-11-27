# Worker recovery runbook

## Idempotency model

- The API uses the client-provided `submission_id` as the idempotency key and Celery task id. Student 2 owns how that key is stored.
- The worker calls `EvaluationStore.claim_job(submission_id, worker_id)`. Terminal jobs return `None`; non-terminal jobs move to `running` through the Student 2 adapter.
- The worker calls `EvaluationStore.save_results(...)`. The Student 2 adapter must replace any existing result set in one transaction.
- Student 1 code does not know table names, columns, or SQL used to implement these behaviors.

## Celery settings

```text
task_acks_late=True
task_reject_on_worker_lost=True
worker_prefetch_multiplier=1
task_track_started=True
task_soft_time_limit=25
task_time_limit=30
```

These settings allow a lost worker to redeliver an unacknowledged task instead of silently dropping it.

## Stale-job sweeper

Task: `worker.tasks.requeue_stale_submissions`

It calls `EvaluationStore.find_stale_running(threshold_seconds)` with `DEFAULT_TIME_LIMIT_MS / 1000 + STALE_GRACE_S`. The Student 2 adapter owns the query and reset behavior. Student 1 enqueues the returned ids again with the same `submission_id`.

Run manually:

```bash
export PYTHONPATH=.
celery -A services.worker.worker.tasks:celery_app call worker.tasks.requeue_stale_submissions
```

Student 4/5 should schedule this with Celery Beat, Jenkins, or Kubernetes CronJob.

## Failure demonstration

1. Submit a job and wait until `GET /api/v1/submissions/{id}` reports `running`.
2. Kill the worker container or process mid-task.
3. Confirm Celery redelivers the unacknowledged task, or run the stale-job sweeper.
4. Start a replacement worker.
5. Confirm the submission eventually reaches a terminal status.
6. Ask Student 2 to verify the persisted submission and result records using the adapter/schema.
7. Query `/api/v1/submissions/{id}` and compare the API response with the persisted records.

## Orphan cleanup

The Sandbox Manager owner should remove containers left behind by a killed worker. Student 1 does not access the Docker socket or perform cleanup directly.
