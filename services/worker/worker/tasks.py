from uuid import UUID

from celery import Task

from services.worker.worker.comparator import determine_final_status, evaluate_run
from services.worker.worker.config import worker_settings
from services.worker.worker.sandbox_client import SandboxClient, SandboxUnavailable
from services.worker.worker.store import get_evaluation_store
from shared.celery import celery_app, enqueue_submission
from shared.config import settings
from shared.contracts import (
    SandboxLimits,
    SandboxRunRequest,
    TestCaseContract,
    TestResultDraft,
)
from shared.enums import SubmissionStatus, TestResultStatus
from shared.store_contracts import EvaluationJob


def build_run_request(
    job: EvaluationJob,
    test_case: TestCaseContract,
) -> SandboxRunRequest:
    wall_timeout_ms = int(settings.sandbox_timeout_s * 1000)
    wall_timeout_ms = max(wall_timeout_ms, job.time_limit_ms + 1000)
    limits = SandboxLimits(
        time_limit_ms=job.time_limit_ms,
        memory_limit_mb=job.memory_limit_mb,
        wall_timeout_ms=wall_timeout_ms,
        pids_limit=settings.sandbox_pids_limit,
        cpu_nanos=settings.sandbox_cpu_nanos,
    )
    return SandboxRunRequest(
        run_id=f"{job.submission_id}:{test_case.id}",
        image=settings.sandbox_image,
        code=job.code,
        stdin=test_case.stdin,
        limits=limits,
    )


@celery_app.task(bind=True, name="worker.tasks.evaluate_submission")
def evaluate_submission(self: Task, submission_id: str) -> dict[str, str]:
    resolved_id = UUID(str(submission_id))
    store = get_evaluation_store()
    job = store.claim_job(resolved_id, worker_settings.worker_id)
    if job is None:
        return {"submission_id": str(resolved_id), "status": "skipped"}

    client = SandboxClient()
    drafts: list[TestResultDraft] = []
    try:
        for test_case in job.tests:
            response = client.run(build_run_request(job, test_case))
            drafts.append(
                evaluate_run(
                    response,
                    test_case.expected_stdout,
                    job.output_mode,
                    test_case.id,
                )
            )
    except SandboxUnavailable as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=3) from exc
    except Exception as exc:
        error_result = TestResultDraft(
            test_case_id=None,
            status=TestResultStatus.ERROR,
            stderr=str(exc),
        )
        store.save_results(
            resolved_id,
            (error_result,),
            SubmissionStatus.ERROR,
            worker_settings.worker_id,
        )
        return {"submission_id": str(resolved_id), "status": "error"}
    finally:
        client.close()

    final_status = determine_final_status(drafts)
    store.save_results(
        resolved_id,
        tuple(drafts),
        final_status,
        worker_settings.worker_id,
    )
    return {"submission_id": str(resolved_id), "status": final_status.value}


@celery_app.task(name="worker.tasks.requeue_stale_submissions")
def requeue_stale_submissions() -> dict[str, object]:
    threshold_seconds = (settings.default_time_limit_ms / 1000) + settings.stale_grace_s
    stale_ids = get_evaluation_store().find_stale_running(threshold_seconds)
    for submission_id in stale_ids:
        enqueue_submission(submission_id)
    return {
        "requeued": len(stale_ids),
        "submission_ids": [str(submission_id) for submission_id in stale_ids],
    }


@celery_app.task(name="worker.tasks.worker_identity")
def worker_identity() -> dict[str, str]:
    return {"worker_id": worker_settings.worker_id}
