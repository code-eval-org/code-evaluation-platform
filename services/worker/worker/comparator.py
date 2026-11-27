from uuid import UUID

from shared.contracts import SandboxRunResponse, TestResultDraft
from shared.enums import OutputMode, SubmissionStatus, TestResultStatus


def normalize_output(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in normalized.split("\n")).rstrip("\n")


def compare_output(actual: str, expected: str, output_mode: OutputMode | str) -> bool:
    mode = OutputMode(output_mode)
    if mode is OutputMode.EXACT:
        return actual == expected
    return normalize_output(actual) == normalize_output(expected)


def evaluate_run(
    response: SandboxRunResponse,
    expected_stdout: str,
    output_mode: OutputMode | str,
    test_case_id: UUID | None = None,
) -> TestResultDraft:
    if response.timed_out:
        status = TestResultStatus.TIMED_OUT
    elif response.oom_killed:
        status = TestResultStatus.OOM_KILLED
    elif response.exit_code is None or response.exit_code != 0:
        status = TestResultStatus.ERROR
    elif compare_output(response.stdout, expected_stdout, output_mode):
        status = TestResultStatus.PASSED
    else:
        status = TestResultStatus.FAILED

    return TestResultDraft(
        test_case_id=test_case_id,
        status=status,
        actual_stdout=response.stdout,
        stderr=response.stderr,
        exit_code=response.exit_code,
        duration_ms=response.duration_ms,
    )


def determine_final_status(results: list[TestResultDraft]) -> SubmissionStatus:
    if not results:
        return SubmissionStatus.ERROR
    statuses = {result.status for result in results}
    if statuses & {TestResultStatus.ERROR, TestResultStatus.OOM_KILLED}:
        return SubmissionStatus.ERROR
    if TestResultStatus.TIMED_OUT in statuses:
        return SubmissionStatus.TIMED_OUT
    if statuses == {TestResultStatus.PASSED}:
        return SubmissionStatus.PASSED
    return SubmissionStatus.FAILED
