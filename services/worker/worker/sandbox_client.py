import httpx
from pydantic import ValidationError

from services.auth.service_auth import sandbox_headers
from shared.config import settings
from shared.contracts import SandboxRunRequest, SandboxRunResponse


class SandboxUnavailable(RuntimeError):
    pass


class SandboxRejected(RuntimeError):
    pass


class SandboxClient:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout: float | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._token = token
        self._client = httpx.Client(
            base_url=(base_url or settings.sandbox_manager_url).rstrip("/"),
            timeout=timeout or settings.sandbox_timeout_s,
            transport=transport,
        )

    def run(self, request: SandboxRunRequest) -> SandboxRunResponse:
        try:
            response = self._client.post(
                "/runs",
                json=request.model_dump(mode="json"),
                headers=sandbox_headers(self._token),
            )
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            raise SandboxUnavailable("sandbox manager is unreachable") from exc

        if response.status_code >= 500:
            raise SandboxUnavailable(f"sandbox manager returned {response.status_code}")
        if response.status_code >= 400:
            raise SandboxRejected(f"sandbox manager returned {response.status_code}")

        try:
            return SandboxRunResponse.model_validate(response.json())
        except (ValidationError, ValueError) as exc:
            raise SandboxRejected("sandbox manager returned an invalid response") from exc

    def close(self) -> None:
        self._client.close()
