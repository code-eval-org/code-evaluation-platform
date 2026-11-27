from shared.contracts import ProblemResponse, SubmissionResponse, TestResultResponse
from shared.store_contracts import ProblemRecord, SubmissionDetail


def to_submission_response(detail: SubmissionDetail) -> SubmissionResponse:
    results = sorted(
        detail.results,
        key=lambda result: (str(result.test_case_id), str(result.id)),
    )
    return SubmissionResponse(
        id=detail.submission.id,
        problem_id=detail.submission.problem_id,
        status=detail.submission.status,
        created_at=detail.submission.created_at,
        finished_at=detail.submission.finished_at,
        results=[
            TestResultResponse(
                id=result.id,
                test_case_id=result.test_case_id,
                status=result.status,
                actual_stdout=result.actual_stdout,
                stderr=result.stderr,
                exit_code=result.exit_code,
                duration_ms=result.duration_ms,
            )
            for result in results
        ],
    )


def to_problem_response(problem: ProblemRecord) -> ProblemResponse:
    return ProblemResponse(
        id=problem.id,
        title=problem.title,
        description=problem.description,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        output_mode=problem.output_mode,
    )
