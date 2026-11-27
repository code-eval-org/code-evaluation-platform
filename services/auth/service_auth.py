from shared.config import settings


def sandbox_headers(token: str | None = None) -> dict[str, str]:
    resolved = token if token is not None else settings.sandbox_manager_token
    return {
        "Authorization": f"Bearer {resolved}",
        "X-Caller-Service": "worker",
        "Accept": "application/json",
    }
