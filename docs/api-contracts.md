# API and service contracts

## Public API

### POST `/api/v1/submissions`

Request body:

```json
{
  "submission_id": "00000000-0000-0000-0000-000000000001",
  "problem_id": "00000000-0000-0000-0000-000000000002",
  "code": "print(2)\n"
}
```

`submission_id` is optional but should be supplied by clients that retry. The API uses it as the idempotency key and as the Celery task id.

Response: `202 Accepted` with a submission object whose status is `queued`.

### GET `/api/v1/submissions/{submission_id}`

Returns the submission with its current status and result records from `SubmissionStore`.

Statuses:

- `queued`
- `running`
- `passed`
- `failed`
- `error`
- `timed_out`

### GET `/api/v1/problems`

Returns problem metadata through `SubmissionStore.list_problems()`. Hidden test cases are never returned by this endpoint.

### GET `/health/live`

Process liveness check.

### GET `/health/ready`

Checks PostgreSQL through `SubmissionStore.ping()` and Redis/Celery backend connectivity.

## API to Celery

Task name: `worker.tasks.evaluate_submission`

Arguments: `[submission_id]`

The task id equals `submission_id`, which prevents duplicate queue entries for the same submission.

## Worker to Sandbox Manager

Endpoint: `POST /runs`

Headers:

```text
Authorization: Bearer <SANDBOX_MANAGER_TOKEN>
X-Caller-Service: worker
Accept: application/json
```

Request body:

```json
{
  "run_id": "<submission_id>:<test_case_id>",
  "image": "code-eval-python:3.12-slim",
  "code": "...",
  "stdin": "...",
  "limits": {
    "time_limit_ms": 5000,
    "memory_limit_mb": 256,
    "wall_timeout_ms": 15000,
    "pids_limit": 64,
    "cpu_nanos": 250000000
  }
}
```

Response body:

```json
{
  "stdout": "2\n",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 12,
  "timed_out": false,
  "oom_killed": false
}
```

The Sandbox Manager owns the Docker socket. The API and worker only use this HTTP contract and never mount the socket.

## Output comparison

Problem metadata includes `output_mode`, which selects the comparison rule:

- `exact`: raw stdout must match expected stdout exactly.
- `normalized`: line endings, trailing whitespace per line, and trailing blank lines are ignored.

Final submission status is selected from the worst test result: `error`/`oom_killed` become `error`, then `timed_out`, then `failed`, otherwise `passed`.
