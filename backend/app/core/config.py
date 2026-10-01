from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FinRecon API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Intelligent Multi-Source Financial & Blockchain Reconciliation Engine"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database Configuration (PostgreSQL by default, fallback to SQLite for local development)
    DATABASE_URL: str = "sqlite:///./finrecon.db"
    
    # Nova AI Configuration (FIN-26 Hackathon AI Provider)
    NOVA_API_KEY: Union[str, None] = None
    NOVA_API_BASE_URL: str = "https://www.aczen.in/nova-api/v1"
    NOVA_TIMEOUT_SECONDS: float = 15.0

    # OpenAI / ChatGPT Configuration
    OPENAI_API_KEY: Union[str, None] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: Union[str, None] = None
    OPENAI_TIMEOUT_SECONDS: float = 30.0

    # Authentication & Security Configuration
    JWT_SECRET: str = "finrecon-enterprise-sha256-auth-jwt-secret-key-2026-production-ready"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # CORS Configuration
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    def get_cors_origins(self) -> List[str]:
        if isinstance(self.CORS_ORIGINS, list):
            return self.CORS_ORIGINS
        if isinstance(self.CORS_ORIGINS, str):
            try:
                import json
                parsed = json.loads(self.CORS_ORIGINS)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
