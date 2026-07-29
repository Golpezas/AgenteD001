"""
Configuración de la aplicación — Pydantic BaseSettings.

Carga variables de entorno con validación y tipado.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # General
    app_name: str = "AgenteD"
    app_version: str = "0.1.0"
    environment: str = "development"

    # Base de datos
    database_url: str = "postgresql+asyncpg://agented:agented_pass@db:5432/agented"

    # Seguridad
    secret_key: str = "change-me-in-production"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # URL externa (para Render/Railway)
    render_external_url: str = "http://localhost:8000"

    @property
    def cors_origin_list(self) -> List[str]:
        """Retorna la lista de orígenes CORS permitidos."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
