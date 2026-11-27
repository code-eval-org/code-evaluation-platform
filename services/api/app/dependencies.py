from fastapi import FastAPI, HTTPException, Request, status

from shared.store_contracts import SubmissionStore


def configure_submission_store(app: FastAPI, store: SubmissionStore) -> None:
    app.state.submission_store = store


def get_submission_store(request: Request) -> SubmissionStore:
    store = getattr(request.app.state, "submission_store", None)
    if store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Submission store adapter is not configured",
        )
    return store
