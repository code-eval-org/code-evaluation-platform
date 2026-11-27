# Student 2 database handoff

Owner: Student 2 — Database and Storage Engineer.

Student 1 does not own database schema, ORM models, migrations, seed data, or persistence adapters. This directory is the predefined implementation area for Student 2. Student 1 only supplies the data contracts in `shared/store_contracts.py` and `shared/contracts.py`.

## What Student 1 provides

| Contract | File | Purpose |
| --- | --- | --- |
| `SubmissionStore` | `shared/store_contracts.py` | API-side data access interface |
| `EvaluationStore` | `shared/store_contracts.py` | Worker-side claim/result/stale-job interface |
| `SubmissionRecord`, `SubmissionDetail`, `ProblemRecord`, `TestResultRecord` | `shared/store_contracts.py` | Data records returned by store adapters |
| `EvaluationJob` | `shared/store_contracts.py` | Job data loaded by the worker |
| `TestResultDraft` | `shared/contracts.py` | Result row to persist after comparison |
| `SubmissionResponse`, `ProblemResponse`, `TestCaseContract` | `shared/contracts.py` | API/DTO shapes |

Student 1 code calls these interfaces only. It never imports SQLAlchemy models or table definitions.

## What Student 2 implements

Create these files/modules:

```text
db/
  README.md
  requirements.txt
  .env.example
  models.py
  adapters.py
  migrations/
    README.md
    alembic.ini
    env.py
    versions/
  seed/
    README.md
    seed.py
```

`models.py` and migrations define the schema below. `adapters.py` implements `SubmissionStore` and `EvaluationStore` from `shared/store_contracts.py`.

Wiring expected from deployment/infra:

```python
from services.api.app.dependencies import configure_submission_store
from services.worker.worker.store import configure_evaluation_store
from db.adapters import SqlAlchemySubmissionStore, SqlAlchemyEvaluationStore

configure_submission_store(app, SqlAlchemySubmissionStore())
configure_evaluation_store(SqlAlchemyEvaluationStore())
```

Student 1 does not add this wiring to API/worker startup; Student 2 or the deployment owner should do it.

## Required adapter behavior

### `SubmissionStore`

- `ping()`: verify database connectivity; raise on failure.
- `create(problem_id, code, submission_id=None)`: insert a submission with status `queued`; if `submission_id` already exists, return that row unchanged for idempotency.
- `get(submission_id)`: return the submission and all of its result records.
- `list_problems()`: return public problem metadata only; never include hidden test cases.

### `EvaluationStore`

- `claim_job(submission_id, worker_id)`: return `None` if missing or terminal; otherwise mark the submission `running`, record claim time and worker id, and return problem limits plus all test cases.
- `save_results(submission_id, results, final_status, worker_id)`: delete any existing result rows for the submission and insert one complete result set in a single transaction; update submission status and finish time.
- `find_stale_running(threshold_seconds)`: return ids of submissions stuck in `running` past the threshold, reset them to `queued`, and clear claim/worker metadata; use row locking or an equivalent concurrency-safe approach.

## Predefined schema

### `problems`

| Column | Type | Nullable | Default / notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key |
| `title` | VARCHAR(200) | No | Public title |
| `description` | TEXT | No | Public statement |
| `time_limit_ms` | INTEGER | No | Per-test CPU/wall budget hint |
| `memory_limit_mb` | INTEGER | No | Per-test memory budget |
| `output_mode` | VARCHAR(16) | No | `exact` or `normalized` |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp |

### `test_cases`

| Column | Type | Nullable | Default / notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key |
| `problem_id` | UUID | No | FK to `problems.id`, `ON DELETE CASCADE` |
| `stdin` | TEXT | No | Default empty string |
| `expected_stdout` | TEXT | No | Hidden expected output |
| `is_hidden` | BOOLEAN | No | Default `true` |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp |

### `submissions`

| Column | Type | Nullable | Default / notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key; also Celery task id |
| `problem_id` | UUID | No | FK to `problems.id`, `ON DELETE RESTRICT` |
| `code` | TEXT | No | Submitted Python source |
| `status` | VARCHAR(32) | No | `queued`, `running`, `passed`, `failed`, `error`, `timed_out` |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp |
| `started_at` | TIMESTAMPTZ | Yes | Claim time used by `find_stale_running`; Student 2 owns this field |
| `finished_at` | TIMESTAMPTZ | Yes | UTC timestamp |
| `worker_id` | VARCHAR(128) | Yes | Worker identity that claimed the job |

### `test_results`

| Column | Type | Nullable | Default / notes |
| --- | --- | --- | --- |
| `id` | UUID | No | Primary key |
| `submission_id` | UUID | No | FK to `submissions.id`, `ON DELETE CASCADE` |
| `test_case_id` | UUID | Yes | FK to `test_cases.id`, `ON DELETE RESTRICT`; null for submission-level errors |
| `status` | VARCHAR(32) | No | `passed`, `failed`, `error`, `timed_out`, `oom_killed` |
| `actual_stdout` | TEXT | No | Default empty string |
| `stderr` | TEXT | No | Default empty string |
| `exit_code` | INTEGER | Yes | Sandbox exit code |
| `duration_ms` | INTEGER | No | Default `0` |
| `created_at` | TIMESTAMPTZ | No | UTC timestamp |

### Indexes and constraints

- `ix_test_case_problem_id` on `test_cases.problem_id`.
- `ix_submission_status` on `submissions.status`.
- `ix_submission_created_at` on `submissions.created_at`.
- `ix_test_result_submission_id` on `test_results.submission_id`.
- Unique constraint `uq_test_result_submission_case` on `(submission_id, test_case_id)`. PostgreSQL permits multiple rows with null `test_case_id`, which covers submission-level errors.
- One submission has many results; one problem has many test cases.

## Acceptance criteria

1. `alembic upgrade head` creates all four tables, indexes, and constraints.
2. Seed script loads problems and hidden tests into PostgreSQL from the private problems repo.
3. `SqlAlchemySubmissionStore` and `SqlAlchemyEvaluationStore` satisfy the protocols in `shared/store_contracts.py`.
4. Result writes are idempotent: repeating a task does not duplicate or partially overwrite results.
5. Stale jobs are requeued safely and terminal submissions are never reclaimed.
6. API and worker tests continue to pass with fake stores; real-store integration tests are added by Student 2.
