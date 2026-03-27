from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="Medical Governance API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=True, alias="APP_DEBUG")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@db:5432/medical_governance",
        alias="DATABASE_URL",
    )

    jwt_issuer: str = Field(default="medical-governance-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="medical-governance-clients", alias="JWT_AUDIENCE")
    jwt_access_token_expire_minutes: int = Field(
        default=15, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    jwt_secret_key: str = Field(default="dev-secret-change-me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    encryption_key: str = Field(default="dev-encryption-key-change-me", alias="ENCRYPTION_KEY")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    default_sla_hours: int = Field(default=48, alias="DEFAULT_SLA_HOURS")
    reminder_lead_hours: int = Field(default=1, alias="REMINDER_LEAD_HOURS")
    enforce_https: bool = Field(default=True, alias="ENFORCE_HTTPS")
    trusted_proxy_headers: bool = Field(default=True, alias="TRUSTED_PROXY_HEADERS")
    trusted_proxies: list[str] = Field(
        default_factory=lambda: ["127.0.0.1", "::1"],
        alias="TRUSTED_PROXIES",
    )

    @field_validator("trusted_proxies", mode="before")
    @classmethod
    def parse_trusted_proxies(cls, value: object) -> list[str]:
        if value is None:
            return ["127.0.0.1", "::1"]
        if isinstance(value, str):
            proxies = [part.strip() for part in value.split(",") if part.strip() != ""]
            return proxies if len(proxies) > 0 else ["127.0.0.1", "::1"]
        if isinstance(value, list):
            proxies = [str(item).strip() for item in value if str(item).strip() != ""]
            return proxies if len(proxies) > 0 else ["127.0.0.1", "::1"]
        return ["127.0.0.1", "::1"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()

