from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ApiSettings:
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    workers: int = int(os.getenv("API_WORKERS", "1"))


api_settings = ApiSettings()
