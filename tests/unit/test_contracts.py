import pytest
from pydantic import ValidationError

from shared.contracts import SandboxLimits, SandboxRunResponse, SubmissionCreate


def test_submission_create_rejects_empty_code():
    with pytest.raises(ValidationError):
        SubmissionCreate(code="   ", problem_id="00000000-0000-0000-0000-000000000001")


def test_submission_create_accepts_python_source():
    payload = SubmissionCreate(
        code="print('hi')\n",
        problem_id="00000000-0000-0000-0000-000000000001",
    )
    assert payload.code == "print('hi')\n"
    assert payload.submission_id is None


def test_sandbox_limits_require_wall_timeout_to_cover_time_limit():
    with pytest.raises(ValidationError):
        SandboxLimits(
            time_limit_ms=5000,
            memory_limit_mb=128,
            wall_timeout_ms=1000,
        )


def test_sandbox_run_response_defaults():
    response = SandboxRunResponse(exit_code=0)
    assert response.stdout == ""
    assert response.duration_ms == 0
    assert response.timed_out is False
