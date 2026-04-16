from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = "NLConsulting Auditor de Documentos com IA"
    app_version: str = "1.0.0"
    prompt_version: str = "2026-04-16-v1"
    upload_root: Path = field(
        default_factory=lambda: Path(os.getenv("UPLOAD_ROOT", "storage/jobs")).resolve()
    )
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "30"))
    max_files_per_job: int = int(os.getenv("MAX_FILES_PER_JOB", "1500"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip()
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    ai_provider_label: str = os.getenv("AI_PROVIDER_LABEL", "OpenAI Compatible API").strip()
    ai_required: bool = _env_bool("AI_REQUIRED", False)
    llm_timeout_seconds: int = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
    llm_max_retries: int = int(os.getenv("LLM_MAX_RETRIES", "3"))
    llm_concurrency: int = int(os.getenv("LLM_CONCURRENCY", "4"))

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
settings.upload_root.mkdir(parents=True, exist_ok=True)
