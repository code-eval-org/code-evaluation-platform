from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from services.api.app.dependencies import get_submission_store
from services.api.app.mappers import to_problem_response, to_submission_response
from shared.celery import celery_app, enqueue_submission
from shared.contracts import (
    HealthResponse,
    ProblemResponse,
    SubmissionCreate,
    SubmissionResponse,
)
from shared.store_contracts import SubmissionStore

router = APIRouter(prefix="/api/v1")
health_router = APIRouter()


@router.post(
    "/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_submission(
    payload: SubmissionCreate,
    store: SubmissionStore = Depends(get_submission_store),
) -> SubmissionResponse:
    detail = store.create(
        problem_id=payload.problem_id,
        code=payload.code,
        submission_id=payload.submission_id,
    )
    try:
        enqueue_submission(detail.submission.id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Queue unavailable; retry with the same submission_id",
        ) from exc
    return to_submission_response(detail)


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
def read_submission(
    submission_id: UUID,
    store: SubmissionStore = Depends(get_submission_store),
) -> SubmissionResponse:
    detail = store.get(submission_id)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return to_submission_response(detail)


@router.get("/problems", response_model=list[ProblemResponse])
def read_problems(
    store: SubmissionStore = Depends(get_submission_store),
) -> list[ProblemResponse]:
    return [to_problem_response(problem) for problem in store.list_problems()]


@health_router.get("/health/live", response_model=HealthResponse)
def live() -> HealthResponse:
    return HealthResponse(status="ok")


@health_router.get("/health/ready", response_model=HealthResponse)
def ready(store: SubmissionStore = Depends(get_submission_store)) -> HealthResponse:
    try:
        store.ping()
        celery_app.backend.client.ping()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dependency check failed",
        ) from exc
    return HealthResponse(status="ready")
