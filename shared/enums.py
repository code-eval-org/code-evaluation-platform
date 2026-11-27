from enum import Enum


class SubmissionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMED_OUT = "timed_out"


class TestResultStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    TIMED_OUT = "timed_out"
    OOM_KILLED = "oom_killed"


class OutputMode(str, Enum):
    EXACT = "exact"
    NORMALIZED = "normalized"


TERMINAL_STATUSES = frozenset(
    {
        SubmissionStatus.PASSED,
        SubmissionStatus.FAILED,
        SubmissionStatus.ERROR,
        SubmissionStatus.TIMED_OUT,
    }
)
