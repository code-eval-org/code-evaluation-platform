import json

import httpx

from services.worker.worker.sandbox_client import (
    SandboxClient,
    SandboxRejected,
    SandboxUnavailable,
)
from shared.contracts import SandboxLimits, SandboxRunRequest


def _request() -> SandboxRunRequest:
    return SandboxRunRequest(
        run_id="run-1",
        image="code-eval-python:3.12-slim",
        code="print(1)",
        stdin="",
        limits=SandboxLimits(
            time_limit_ms=1000,
            memory_limit_mb=128,
            wall_timeout_ms=2000,
        ),
    )


def test_run_posts_sandbox_contract_with_auth_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/runs"
        assert request.headers["Authorization"] == "Bearer sandbox-token"
        assert request.headers["X-Caller-Service"] == "worker"
        body = json.loads(request.content)
        assert body["run_id"] == "run-1"
        assert body["code"] == "print(1)"
        return httpx.Response(
            200,
            json={"stdout": "1\n", "exit_code": 0, "duration_ms": 7},
        )

    client = SandboxClient(
        base_url="http://sandbox.test",
        token="sandbox-token",
        transport=httpx.MockTransport(handler),
    )
    result = client.run(_request())
    assert result.stdout == "1\n"
    assert result.exit_code == 0
    client.close()


def test_run_raises_unavailable_for_server_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "busy"})

    client = SandboxClient(
        base_url="http://sandbox.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        client.run(_request())
    except SandboxUnavailable:
        pass
    else:
        raise AssertionError("expected SandboxUnavailable")
    finally:
        client.close()


def test_run_raises_rejected_for_bad_request():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "bad image"})

    client = SandboxClient(
        base_url="http://sandbox.test",
        transport=httpx.MockTransport(handler),
    )
    try:
        client.run(_request())
    except SandboxRejected:
        pass
    else:
        raise AssertionError("expected SandboxRejected")
    finally:
        client.close()
