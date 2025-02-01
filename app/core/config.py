from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Bank Code Risk POC", alias="APP_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/code_risk",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    github_webhook_secret: str = Field(
        default="change-this-secret",
        alias="GITHUB_WEBHOOK_SECRET",
    )
    llm_provider: Literal["mock", "openai", "azure_openai"] = Field(
        default="mock",
        alias="LLM_PROVIDER",
    )
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_MODEL")
    azure_openai_api_key: str = Field(default="", alias="AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: str = Field(default="", alias="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_version: str = Field(
        default="2024-10-21",
        alias="AZURE_OPENAI_API_VERSION",
    )
    azure_openai_deployment: str = Field(default="", alias="AZURE_OPENAI_DEPLOYMENT")
    max_diff_chars: int = Field(default=60000, alias="MAX_DIFF_CHARS")
    allowed_repositories: str = Field(default="", alias="ALLOWED_REPOSITORIES")

    @field_validator("llm_provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def validate_provider_credentials(self) -> "Settings":
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "azure_openai":
            missing = [
                name
                for name, value in (
                    ("AZURE_OPENAI_API_KEY", self.azure_openai_api_key),
                    ("AZURE_OPENAI_ENDPOINT", self.azure_openai_endpoint),
                    ("AZURE_OPENAI_DEPLOYMENT", self.azure_openai_deployment),
                )
                if not value
            ]
            if missing:
                raise ValueError(
                    "Missing Azure OpenAI settings when LLM_PROVIDER=azure_openai: "
                    + ", ".join(missing)
                )
        return self

    @property
    def allowed_repository_set(self) -> set[str]:
        if not self.allowed_repositories.strip():
            return set()
        return {
            item.strip()
            for item in self.allowed_repositories.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
