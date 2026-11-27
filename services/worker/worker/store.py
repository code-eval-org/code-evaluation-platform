from shared.store_contracts import EvaluationStore

_evaluation_store: EvaluationStore | None = None


def configure_evaluation_store(store: EvaluationStore) -> None:
    global _evaluation_store
    _evaluation_store = store


def get_evaluation_store() -> EvaluationStore:
    if _evaluation_store is None:
        raise RuntimeError(
            "EvaluationStore adapter is not configured; Student 2 must wire it at startup"
        )
    return _evaluation_store
