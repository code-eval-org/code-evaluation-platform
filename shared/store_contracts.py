from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from shared.contracts import TestCaseContract, TestResultDraft
from shared.enums import OutputMode, SubmissionStatus, TestResultStatus


@dataclass(frozen=True)
class TestResultRecord:
    id: UUID
    test_case_id: UUID | None
    status: TestResultStatus
    actual_stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int


@dataclass(frozen=True)
class SubmissionRecord:
    id: UUID
    problem_id: UUID
    code: str
    status: SubmissionStatus
    created_at: datetime
    finished_at: datetime | None


@dataclass(frozen=True)
class SubmissionDetail:
    submission: SubmissionRecord
    results: tuple[TestResultRecord, ...]


@dataclass(frozen=True)
class ProblemRecord:
    id: UUID
    title: str
    description: str
    time_limit_ms: int
    memory_limit_mb: int
    output_mode: OutputMode


@dataclass(frozen=True)
class EvaluationJob:
    submission_id: UUID
    code: str
    time_limit_ms: int
    memory_limit_mb: int
    output_mode: OutputMode
    tests: tuple[TestCaseContract, ...]


class SubmissionStore(Protocol):
    def ping(self) -> None: ...

    def create(
        self,
        problem_id: UUID,
        code: str,
        submission_id: UUID | None = None,
    ) -> SubmissionDetail: ...

    def get(self, submission_id: UUID) -> SubmissionDetail | None: ...

    def list_problems(self) -> tuple[ProblemRecord, ...]: ...


class EvaluationStore(Protocol):
    def claim_job(
        self,
        submission_id: UUID,
        worker_id: str,
    ) -> EvaluationJob | None: ...

    def save_results(
        self,
        submission_id: UUID,
        results: tuple[TestResultDraft, ...],
        final_status: SubmissionStatus,
        worker_id: str,
    ) -> None: ...

    def find_stale_running(self, threshold_seconds: float) -> tuple[UUID, ...]: ...
