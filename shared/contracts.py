from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from shared.config import settings
from shared.enums import OutputMode, SubmissionStatus, TestResultStatus


class SandboxLimits(BaseModel):
    time_limit_ms: int = Field(gt=0)
    memory_limit_mb: int = Field(gt=0)
    wall_timeout_ms: int = Field(gt=0)
    pids_limit: int = Field(default=64, gt=0)
    cpu_nanos: int = Field(default=250_000_000, gt=0)

    @model_validator(mode="after")
    def wall_timeout_covers_time_limit(self) -> "SandboxLimits":
        if self.wall_timeout_ms < self.time_limit_ms:
            raise ValueError("wall_timeout_ms must be at least time_limit_ms")
        return self


class SandboxRunRequest(BaseModel):
    run_id: str
    image: str
    code: str
    stdin: str = ""
    limits: SandboxLimits


class SandboxRunResponse(BaseModel):
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = Field(default=0, ge=0)
    timed_out: bool = False
    oom_killed: bool = False


class SubmissionCreate(BaseModel):
    submission_id: UUID | None = None
    problem_id: UUID
    code: str

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("code must not be empty")
        if len(value.encode("utf-8")) > settings.max_code_bytes:
            raise ValueError("code exceeds maximum allowed size")
        return value


class ProblemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str
    time_limit_ms: int
    memory_limit_mb: int
    output_mode: OutputMode = OutputMode.NORMALIZED


class TestCaseContract(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    problem_id: UUID
    stdin: str
    expected_stdout: str
    is_hidden: bool


class TestResultDraft(BaseModel):
    test_case_id: UUID | None
    status: TestResultStatus
    actual_stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration_ms: int = 0


class TestResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    test_case_id: UUID | None
    status: TestResultStatus
    actual_stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    problem_id: UUID
    status: SubmissionStatus
    created_at: datetime
    finished_at: datetime | None = None
    results: list[TestResultResponse] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
