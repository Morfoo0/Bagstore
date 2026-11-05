from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "BagStore API"
    app_version: str = "0.1.0"
    api_description: str = "API de catálogo de BagStore."
    environment: str = "development"
    debug: bool = False
    database_url: str = (
        "postgresql+psycopg://bagstore:bagstore@localhost:5432/bagstore"
    )
    database_echo: bool = False
    session_ttl_minutes: int = Field(default=1440, gt=0)
    admin_email: str = "admin@bagstore.com"
    admin_password: str | None = None
    api_prefix: str = "/api"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
    ]
    cors_allow_headers: list[str] = [
        "Accept",
        "Authorization",
        "Content-Type",
    ]

    @field_validator("api_prefix")
    @classmethod
    def _normalizar_prefijo(cls, value: str) -> str:
        prefijo = value.strip()
        if not prefijo.startswith("/"):
            prefijo = f"/{prefijo}"
        return prefijo.rstrip("/") or "/"

    @field_validator("cors_origins")
    @classmethod
    def _normalizar_origenes(cls, value: list[str]) -> list[str]:
        origenes = [origen.strip().rstrip("/") for origen in value if origen.strip()]
        return list(dict.fromkeys(origenes))

    @field_validator("cors_allow_methods")
    @classmethod
    def _normalizar_metodos(cls, value: list[str]) -> list[str]:
        metodos = [metodo.strip().upper() for metodo in value if metodo.strip()]
        return list(dict.fromkeys(metodos))

    @field_validator("cors_allow_headers")
    @classmethod
    def _normalizar_cabeceras(cls, value: list[str]) -> list[str]:
        cabeceras = [cabecera.strip() for cabecera in value if cabecera.strip()]
        return list(dict.fromkeys(cabeceras))

    @model_validator(mode="after")
    def _validar_cors(self) -> "Settings":
        if self.cors_allow_credentials and "*" in self.cors_origins:
            raise ValueError(
                "CORS_ORIGINS no puede contener '*' cuando CORS_ALLOW_CREDENTIALS es true."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
