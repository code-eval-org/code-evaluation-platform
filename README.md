# code-evaluation-platform

Main app monorepo for Project 4 — Distributed Code Evaluation Platform. It contains the Student 1 runtime services, shared contracts, tests, and documentation for the Python-only submission pipeline.

## Student 1 scope

Student 1 is the API/Worker developer. This repository contains only the Student 1 initial architecture:

- FastAPI submission API: validation, store-interface calls, Celery enqueue, status/results, health endpoints.
- Celery worker: task orchestration, sandbox HTTP client, output comparison, store-interface calls, stale-job requeue task.
- Shared contracts: Pydantic DTOs, store protocols, enums, Celery producer, settings.
- Internal auth helper: bearer-token headers for calls to the sandbox manager.
- Tests and docs for API contracts, security boundaries, and recovery.

Student 1 does **not** define or implement the database schema, SQLAlchemy models, migrations, seed data, persistence adapters, Docker images, Compose/Kubernetes manifests, monitoring, or the real sandbox manager.

## Architecture

```text
Client -> FastAPI API -> Redis/Celery -> Worker -> Sandbox Manager -> ephemeral Python container
             |                            |              |
             +------ SubmissionStore ------+              |
                      EvaluationStore -------------------+
                              |
                        PostgreSQL (Student 2)
```

The API never executes submitted code and never receives the Docker socket. The worker also never executes submitted code; it only calls the trusted Sandbox Manager over HTTP. The Sandbox Manager is the only service allowed to create short-lived isolated containers.

Student 1 code talks to PostgreSQL only through the `SubmissionStore` and `EvaluationStore` protocols in `shared/store_contracts.py`. Student 2 owns the schema, models, migrations, seed data, and adapter implementations.

## File map

```text
services/api/app/
  main.py          FastAPI application
  routes.py        submission, result, problem, and health endpoints
  dependencies.py  SubmissionStore injection hook for Student 2/deployment
  mappers.py       store-record to API-response conversion
  config.py        API runtime settings

services/worker/worker/
  tasks.py         Celery tasks and stale-job requeue
  comparator.py    output comparison and final-status selection
  sandbox_client.py HTTP contract for Sandbox Manager
  store.py         EvaluationStore injection hook for Student 2/deployment
  config.py        worker identity/settings

services/auth/
  service_auth.py  internal bearer-token header helper

shared/
  contracts.py       Pydantic request/response contracts
  store_contracts.py store protocols and storage-agnostic records
  enums.py           submission/test status and output mode
  celery.py          Celery app and enqueue helper
  config.py          shared runtime settings
  utils.py           UTC timestamp helper

db/                  Student 2 handoff READMEs; no Student 1 DB code
tests/unit/          pure logic tests
tests/integration/   API, sandbox client, and worker task tests with fakes
docs/                API, security, and recovery notes
```

## Database boundary

See `db/README.md` for the predefined schema and implementation instructions owned by Student 2.

Student 1 provides only the required behavior contracts:

- `SubmissionStore.ping/create/get/list_problems`
- `EvaluationStore.claim_job/save_results/find_stale_running`
- Storage-agnostic records: `SubmissionDetail`, `ProblemRecord`, `EvaluationJob`, `TestResultDraft`

Student 2 implements those protocols in `db/adapters.py`, owns Alembic revisions in `db/migrations/`, and loads hidden tests with `db/seed/seed.py` from the private `code-evaluation-problems` repo. Hidden tests must not be shipped in application images.

## Local install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Run tests:

```bash
pytest
```

Tests use fake stores, so they do not require PostgreSQL, Redis, or Docker.

## Dashboard frontend

The Next.js dashboard is a separate sibling project at `../code-evaluation-frontend`. It is intentionally outside this backend monorepo. It shows architecture flow, workstream status, role ownership, handoffs, and a submission console that calls the FastAPI service.

From `../code-evaluation-frontend`:

```bash
npm install
cp .env.example .env.local
npm run dev
```

Open `http://localhost:3000`. Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` if the API is not at `http://localhost:8000`. The API allows the Next.js dev origin through `FRONTEND_ORIGINS`.

## Running with the Student 2 adapter

After Student 2 provides `db/adapters.py`, deployment/infra wires the adapters:

```python
from services.api.app.dependencies import configure_submission_store
from services.worker.worker.store import configure_evaluation_store
from db.adapters import SqlAlchemySubmissionStore, SqlAlchemyEvaluationStore

configure_submission_store(app, SqlAlchemySubmissionStore())
configure_evaluation_store(SqlAlchemyEvaluationStore())
```

Then run:

```bash
export PYTHONPATH=.
pip install -r db/requirements.txt
uvicorn services.api.app.main:app --reload
celery -A services.worker.worker.tasks:celery_app worker --loglevel=INFO -Q evaluation
```

Run the stale-job sweeper on a schedule:

```bash
export PYTHONPATH=.
celery -A services.worker.worker.tasks:celery_app call worker.tasks.requeue_stale_submissions
```

## API examples

Submit:

```bash
curl -X POST http://localhost:8000/api/v1/submissions \
  -H 'Content-Type: application/json' \
  -d '{
    "problem_id": "00000000-0000-0000-0000-000000000001",
    "code": "n = int(input())\nprint(n * 2)\n"
  }'
```

Returns `202 Accepted` with a queued submission. Send the same `submission_id` on retry if you need idempotent resubmission.

Read result:

```bash
curl http://localhost:8000/api/v1/submissions/{submission_id}
```

Health:

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Team roles

| Role | Main contributions |
| --- | --- |
| Student 1 — API/Worker Developer | FastAPI endpoints, validation, Celery producer/consumer, store interfaces, sandbox client, output comparison, service auth, unit/integration tests. |
| Student 2 — Database Engineer | PostgreSQL schema, Alembic migrations, seed problems/test cases, SQLAlchemy models, store adapters, persistence details, stale-job queries, backup/restore notes. |
| Student 3 — Containerization Engineer | Dockerfiles for API/worker/sandbox manager, Compose networking, non-root images, resource limits, Docker socket isolation, volumes. |
| Student 4 — CI/CD Engineer | Jenkins pipeline, automated tests, lint/type checks, image build/tag/push, registry secrets, vulnerability scanning. |
| Student 5 — Kubernetes/Monitoring Engineer | Kubernetes manifests, scaling, health probes, recovery demo, Prometheus metrics, Grafana dashboard, alerts. |

For a four-person team, merge Student 5 into Student 4 as CI/CD + Kubernetes + Monitoring. Roles define primary responsibility, not exclusive ownership; all members review the complete workflow.

## Deferred to other owners

- Student 2: DB schema, SQLAlchemy models, store adapters, Alembic migrations, seed scripts, backup/restore. See `db/README.md`, `db/migrations/README.md`, and `db/seed/README.md`.
- Student 3/5: real Sandbox Manager implementation with Docker socket and isolation controls.
- Student 3: Dockerfiles, Compose networking, non-root images, volumes.
- Student 4: Jenkins pipeline and image registry flow.
- Student 5: Kubernetes manifests, Prometheus, Grafana, alerts.
