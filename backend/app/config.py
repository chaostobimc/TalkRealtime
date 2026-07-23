from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_local_env() -> None:
    """Load a small .env file without adding a runtime dependency.

    Real environment variables always win. This intentionally supports only the
    KEY=value format needed for local development.
    """
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("DATABASE_PATH", "./talkrealtime.db")
    deepseek_auth_token: str | None = os.getenv("DEEPSEEK_AUTH_TOKEN") or None
    demo_translator: bool = os.getenv("DEMO_TRANSLATOR", "false").lower() == "true"
    cors_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "").split(",")
        if origin.strip()
    )
    max_message_length: int = 4_000
    history_limit: int = 80
    max_parallel_translations: int = 8


settings = Settings()
