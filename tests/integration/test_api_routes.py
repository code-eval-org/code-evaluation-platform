from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi.testclient import TestClient as Client

from services.api.app import routes
from services.api.app.dependencies import configure_submission_store
from services.api.app.main import app
from shared.contracts import SubmissionResponse
from shared.enums import OutputMode, SubmissionStatus, TestResultStatus as ResultStatus
from shared.store_contracts import (
    ProblemRecord,
    SubmissionDetail,
    SubmissionRecord,
    TestResultRecord as ResultRecord,
)


def make_detail(submission_id: UUID, problem_id: UUID) -> SubmissionDetail:
    return SubmissionDetail(
        submission=SubmissionRecord(
            id=submission_id,
            problem_id=problem_id,
            code="print(2)\n",
            status=SubmissionStatus.QUEUED,
            created_at=datetime.now(timezone.utc),
            finished_at=None,
        ),
        results=(
            ResultRecord(
                id=uuid4(),
                test_case_id=uuid4(),
                status=ResultStatus.PASSED,
                actual_stdout="2\n",
                stderr="",
                exit_code=0,
                duration_ms=5,
            ),
        ),
    )


class FakeSubmissionStore:
    def __init__(self, detail: SubmissionDetail):
        self.detail = detail

    def ping(self) -> None:
        return None

    def create(self, problem_id, code, submission_id=None):
        return self.detail

    def get(self, submission_id):
        return self.detail

    def list_problems(self):
        return (
            ProblemRecord(
                id=self.detail.submission.problem_id,
                title="Double",
                description="Print twice the input number",
                time_limit_ms=1000,
                memory_limit_mb=128,
                output_mode=OutputMode.NORMALIZED,
            ),
        )


def test_submit_enqueues_and_returns_202(monkeypatch):
    submission_id = uuid4()
    problem_id = uuid4()
    configure_submission_store(app, FakeSubmissionStore(make_detail(submission_id, problem_id)))
    enqueued = []
    monkeypatch.setattr(routes, "enqueue_submission", lambda value: enqueued.append(value))

    client = Client(app)
    response = client.post(
        "/api/v1/submissions",
        json={
            "submission_id": str(submission_id),
            "problem_id": str(problem_id),
            "code": "print(2)\n",
        },
    )

    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert enqueued == [submission_id]


def test_read_submission_and_problems_use_store_contract():
    submission_id = uuid4()
    problem_id = uuid4()
    configure_submission_store(app, FakeSubmissionStore(make_detail(submission_id, problem_id)))
    client = Client(app)

    submission_response = client.get(f"/api/v1/submissions/{submission_id}")
    problem_response = client.get("/api/v1/problems")

    assert submission_response.status_code == 200
    parsed = SubmissionResponse.model_validate(submission_response.json())
    assert parsed.id == submission_id
    assert parsed.results[0].status is ResultStatus.PASSED

    assert problem_response.status_code == 200
    assert problem_response.json()[0]["title"] == "Double"
