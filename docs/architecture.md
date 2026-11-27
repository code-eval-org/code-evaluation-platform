# Architecture notes

## Services

| Service | Owner | Responsibility |
| --- | --- | --- |
| API | Student 1 | Validate submissions, call `SubmissionStore`, enqueue Celery tasks, serve results and health. |
| Worker | Student 1 | Claim jobs through `EvaluationStore`, call Sandbox Manager, compare output, save results, requeue stale jobs. |
| Sandbox Manager | Student 3/5 | Run fixed-image isolated containers with strict limits; owns Docker socket. |
| PostgreSQL | Student 2 | Schema, models, migrations, seed data, store adapters, stale-job queries. |
| Redis | Student 3/4 | Celery broker and result backend. |
| Monitoring | Student 5 | Queue depth, duration, pass/fail/error counts, timeouts, worker health. |

## Submission flow

```text
POST /api/v1/submissions
  -> API validates and calls SubmissionStore.create(row, status=queued)
  -> API enqueues task keyed by submission_id and returns 202
  -> Worker calls EvaluationStore.claim_job(worker_id) and gets status=running
  -> Worker loads hidden test cases through EvaluationStore
  -> Worker calls Sandbox Manager POST /runs per test case
  -> Sandbox Manager runs isolated Python container and removes it
  -> Worker compares stdout with expected output
  -> Worker calls EvaluationStore.save_results(final status, result records)
  -> Client polls GET /api/v1/submissions/{id}
```

The Student 1 services do not know table names, columns, SQL, or ORM models. Student 2 implements the store protocols in `db/adapters.py` and owns the schema described in `db/README.md`.

## Explicit non-goals for Student 1

- No Docker socket access.
- No untrusted code execution in API or worker processes.
- No database schema, SQLAlchemy models, migrations, seed data, or persistence adapters.
- No Dockerfiles, Compose, Kubernetes, Jenkins, Prometheus, or Grafana configuration.
- No real Sandbox Manager implementation.
