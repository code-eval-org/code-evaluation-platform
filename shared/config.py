from dataclasses import dataclass
import os


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


@dataclass(frozen=True)
class Settings:
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    sandbox_manager_url: str = os.getenv(
        "SANDBOX_MANAGER_URL", "http://sandbox-manager:8000"
    )
    sandbox_manager_token: str = os.getenv(
        "SANDBOX_MANAGER_TOKEN", "dev-only-sandbox-token"
    )
    sandbox_image: str = os.getenv("SANDBOX_IMAGE", "code-eval-python:3.12-slim")
    max_code_bytes: int = _int("MAX_CODE_BYTES", 65536)
    default_time_limit_ms: int = _int("DEFAULT_TIME_LIMIT_MS", 5000)
    default_memory_limit_mb: int = _int("DEFAULT_MEMORY_LIMIT_MB", 256)
    sandbox_cpu_nanos: int = _int("SANDBOX_CPU_NANOS", 250_000_000)
    sandbox_pids_limit: int = _int("SANDBOX_PIDS_LIMIT", 64)
    sandbox_timeout_s: float = _float("SANDBOX_TIMEOUT_S", 15.0)
    stale_grace_s: int = _int("STALE_GRACE_S", 60)
    task_time_limit_s: int = _int("TASK_TIME_LIMIT_S", 30)
    task_soft_time_limit_s: int = _int("TASK_SOFT_TIME_LIMIT_S", 25)


settings = Settings()
