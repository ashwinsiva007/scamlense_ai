from typing import List, Literal, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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
    GEMMA_MODEL: str = Field(
        default="google/gemma-4-9b-it",
        description="Gemma 4 model identifier read from environment",
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

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


settings = Settings()
