# Security boundaries

## Required trust boundary

Submitted Python code must never execute in the API container or the worker process. Only the Sandbox Manager creates ephemeral containers, and it is the only service that receives the Docker socket.

```text
API     no Docker socket, no code execution
Worker  no Docker socket, no code execution
Sandbox Manager  Docker socket, fixed image allowlist, isolated runs
```

## Worker safeguards

- The worker sends an HTTP request to the Sandbox Manager with a bearer token.
- The worker does not import, eval, exec, or subprocess submitted code.
- The worker includes CPU, memory, PID, and wall-clock limits in every run request.
- The worker passes stderr, exit code, duration, timeout, and OOM flags to `EvaluationStore.save_results`; Student 2 owns persistence.

## Sandbox controls expected from Student 3/5

- Fixed non-root Python image based on `python:3.12-slim`.
- Container user `65534:65534`.
- `cap_drop=ALL`.
- `security_opt=no-new-privileges`.
- `network_mode=none`.
- `read_only=True` with `tmpfs=/tmp`.
- No host bind mounts.
- `nano_cpus`, `mem_limit`, `pids_limit`, and ulimits for `NOFILE`, `FSIZE`, and `CPU`.
- Hard wall-clock timeout with kill and container removal.
- Shared-secret or mTLS authentication on `POST /runs`.
- Image allowlist; submitted code cannot select an arbitrary image.

## Data handling

- Hidden test cases live in PostgreSQL, loaded from the private problems repo.
- Hidden tests are never returned by `/api/v1/problems` or `/api/v1/submissions/{id}`.
- Only test-case ids, statuses, actual stdout, stderr, exit codes, and durations are stored in `test_results`.
- Keep secrets in environment variables and out of the repository.
