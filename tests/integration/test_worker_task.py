from uuid import uuid4

from services.worker.worker import tasks
from shared.contracts import SandboxRunResponse, TestCaseContract as CaseContract
from shared.enums import OutputMode, SubmissionStatus
from shared.store_contracts import EvaluationJob


class FakeEvaluationStore:
    def __init__(self, job: EvaluationJob):
        self.job = job
        self.saved = None

    def claim_job(self, submission_id, worker_id):
        return self.job

    def save_results(self, submission_id, results, final_status, worker_id):
        self.saved = {
            "submission_id": submission_id,
            "results": results,
            "status": final_status,
            "worker_id": worker_id,
        }

    def find_stale_running(self, threshold_seconds):
        return ()


def make_job() -> EvaluationJob:
    return EvaluationJob(
        submission_id=uuid4(),
        code="print('ok')",
        time_limit_ms=1000,
        memory_limit_mb=128,
        output_mode=OutputMode.NORMALIZED,
        tests=(
            CaseContract(
                id=uuid4(),
                problem_id=uuid4(),
                stdin="",
                expected_stdout="ok",
                is_hidden=True,
            ),
        ),
    )


def test_evaluate_submission_writes_final_result(monkeypatch):
    job = make_job()
    store = FakeEvaluationStore(job)
    monkeypatch.setattr(tasks, "get_evaluation_store", lambda: store)

    class FakeSandboxClient:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, request):
            assert request.code == "print('ok')"
            assert request.limits.memory_limit_mb == 128
            return SandboxRunResponse(stdout="ok\n", exit_code=0, duration_ms=3)

        def close(self):
            pass

    monkeypatch.setattr(tasks, "SandboxClient", FakeSandboxClient)

    result = tasks.evaluate_submission.run(str(job.submission_id))

    assert result == {"submission_id": str(job.submission_id), "status": "passed"}
    assert store.saved["status"] is SubmissionStatus.PASSED
    assert store.saved["results"][0].duration_ms == 3


def test_requeue_stale_submissions_enqueues_each_id(monkeypatch):
    class StaleStore(FakeEvaluationStore):
        def find_stale_running(self, threshold_seconds):
            assert threshold_seconds > 0
            return (uuid4(),)

    store = StaleStore(make_job())
    enqueued = []
    monkeypatch.setattr(tasks, "get_evaluation_store", lambda: store)
    monkeypatch.setattr(tasks, "enqueue_submission", lambda submission_id: enqueued.append(submission_id))

    result = tasks.requeue_stale_submissions.run()

    assert result["requeued"] == 1
    assert len(enqueued) == 1
