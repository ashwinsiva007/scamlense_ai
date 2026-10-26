from pathlib import Path
import os
from typing import List, Literal, Union, Any, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Determine absolute paths relative to this config file
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
BACKEND_ENV = BACKEND_DIR / ".env"
ROOT_ENV = REPO_ROOT / ".env"

PLACEHOLDER_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your_key_here",
    "your_key",
    "changeme",
    "placeholder",
    "none",
    "null",
}


def clean_key(val: Optional[str]) -> str:
    """Strips quotes and whitespace, and filters out common placeholder values."""
    if not val:
        return ""
    clean = str(val).strip().strip("'\"")
    if clean.lower() in PLACEHOLDER_KEYS:
        return ""
    return clean


def extract_key_from_file(file_path: Path) -> str:
    """Safely extracts GEMINI_API_KEY or GOOGLE_API_KEY directly from an env file."""
    if not file_path.is_file():
        return ""
    try:
        with open(file_path, "r", encoding="utf-8-sig", errors="replace") as f:
            for line in f:
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                k, v = stripped.split("=", 1)
                k = k.strip()
                if k in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
                    clean = clean_key(v)
                    if clean:
                        return clean
    except Exception:
        pass
    return ""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(ROOT_ENV), str(BACKEND_ENV)),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Runtime Execution Mode
    MODE: Literal["cloud", "local", "mock"] = Field(
        default="mock",
        description="Operating mode: cloud (Gemini/Gemma), local (Ollama), or mock",
    )

    # Cloud Gemini / Gemma Model Configuration
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini / AI Studio API key for cloud model inference",
    )
    GOOGLE_API_KEY: Optional[str] = Field(
        default=None,
        description="Alias for GEMINI_API_KEY",
    )
    GEMMA_MODEL: str = Field(
        default="gemini-3-flash-preview",
        description="Gemini/Gemma cloud model identifier read from environment",
    )

    # Local Ollama Configuration
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama service",
    )
    OLLAMA_MODEL: str = Field(
        default="gemma4:latest",
        description="Ollama model tag for local inference",
    )

    # External Reputation & Threat Intelligence Keys
    SAFE_BROWSING_KEY: str = Field(
        default="",
        description="Google Safe Browsing v4 API key",
    )
    URLHAUS_KEY: str = Field(
        default="",
        description="Abuse.ch URLhaus API key",
    )

    # Security & Gateway Controls
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Allowed CORS origin origins list or comma-separated string",
    )
    MAX_UPLOAD_MB: int = Field(
        default=8,
        description="Maximum allowed upload payload size in megabytes",
    )
    RATE_LIMIT_PER_MIN: int = Field(
        default=20,
        description="Rate limit window max requests per minute per IP",
    )

    @model_validator(mode="before")
    @classmethod
    def resolve_and_clean_config(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Resolve GEMINI_API_KEY with priority:
            # 1. os.environ (GEMINI_API_KEY or GOOGLE_API_KEY)
            # 2. backend/.env (explicit file read)
            # 3. repo root .env (explicit file read)
            # 4. parsed dict fields from pydantic-settings
            raw_key = (
                clean_key(os.environ.get("GEMINI_API_KEY"))
                or clean_key(os.environ.get("GOOGLE_API_KEY"))
                or extract_key_from_file(BACKEND_ENV)
                or extract_key_from_file(ROOT_ENV)
                or clean_key(data.get("GEMINI_API_KEY"))
                or clean_key(data.get("GOOGLE_API_KEY"))
            )
            data["GEMINI_API_KEY"] = clean_key(raw_key)

            # Clean and strip all other string fields
            for field in [
                "MODE",
                "GEMMA_MODEL",
                "OLLAMA_BASE_URL",
                "OLLAMA_MODEL",
                "SAFE_BROWSING_KEY",
                "URLHAUS_KEY",
            ]:
                if field in data and isinstance(data[field], str):
                    data[field] = data[field].strip().strip("'\"")

        return data

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            value = value.strip().strip("'\"")
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()

