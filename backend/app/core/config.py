import secrets
import warnings

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "RepoMind AI"
    DATABASE_URL: str = "postgresql://localhost:5432/repomind"
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_DB_PATH: str = "./data/chroma_db"
    REPOS_PATH: str = "./data/repos"
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    CORS_ALLOW_ORIGINS: str = ""
    ENVIRONMENT: str = "development"

    @property
    def allowed_origins(self) -> list[str]:
        origins = [self.FRONTEND_ORIGIN, *(item.strip() for item in self.CORS_ALLOW_ORIGINS.split(","))]
        return list(dict.fromkeys(origin for origin in origins if origin))


settings = Settings()
if not settings.JWT_SECRET_KEY:
    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError("JWT_SECRET_KEY must be configured with a high-entropy secret in production.")
    settings.JWT_SECRET_KEY = secrets.token_urlsafe(48)
    warnings.warn("JWT_SECRET_KEY is unset; using an ephemeral development-only key. Configure a persistent key for local deployments.", RuntimeWarning)
if settings.ENVIRONMENT.lower() == "production" and len(settings.JWT_SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY must contain at least 32 bytes in production.")
if "*" in settings.allowed_origins:
    raise RuntimeError("Wildcard CORS origins are not allowed when credentialed requests are enabled.")
