from uuid import uuid4

from services.worker.worker.comparator import (
    compare_output,
    determine_final_status,
    evaluate_run,
    normalize_output,
)
from shared.contracts import SandboxRunResponse, TestResultDraft as ResultDraft
from shared.enums import OutputMode, SubmissionStatus, TestResultStatus as ResultStatus


def test_normalize_output_removes_line_endings_and_trailing_whitespace():
    value = "hello  \r\nworld\t\n\n"
    assert normalize_output(value) == "hello\nworld"


def test_compare_output_respects_mode():
    assert compare_output("hello \n", "hello\n", OutputMode.NORMALIZED)
    assert not compare_output("hello \n", "hello\n", OutputMode.EXACT)


def test_evaluate_run_passes_matching_output():
    response = SandboxRunResponse(stdout="42\n", exit_code=0, duration_ms=12)
    result = evaluate_run(response, "42", OutputMode.NORMALIZED, uuid4())
    assert result.status is ResultStatus.PASSED
    assert result.duration_ms == 12


def test_evaluate_run_prioritizes_timeout_over_output_mismatch():
    response = SandboxRunResponse(
        stdout="wrong", exit_code=None, duration_ms=5000, timed_out=True
    )
    result = evaluate_run(response, "right", OutputMode.EXACT, uuid4())
    assert result.status is ResultStatus.TIMED_OUT


def test_evaluate_run_maps_nonzero_exit_to_error():
    response = SandboxRunResponse(stdout="", stderr="traceback", exit_code=1)
    result = evaluate_run(response, "", OutputMode.EXACT)
    assert result.status is ResultStatus.ERROR
    assert result.stderr == "traceback"


def test_determine_final_status_uses_worst_result():
    results = [
        ResultDraft(test_case_id=uuid4(), status=ResultStatus.PASSED),
        ResultDraft(test_case_id=uuid4(), status=ResultStatus.FAILED),
    ]
    assert determine_final_status(results) is SubmissionStatus.FAILED

    results.append(
        ResultDraft(test_case_id=uuid4(), status=ResultStatus.TIMED_OUT)
    )
    assert determine_final_status(results) is SubmissionStatus.TIMED_OUT


def test_determine_final_status_without_results_is_error():
    assert determine_final_status([]) is SubmissionStatus.ERROR
