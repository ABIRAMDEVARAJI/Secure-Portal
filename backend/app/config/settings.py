from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    DATABASE_URL: str
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"
    SESSION_SECRET: str = "development-only-change-me"
    SESSION_COOKIE_NAME: str = "scp_session"
    SESSION_MAX_AGE_SECONDS: int = 28800
    COOKIE_SECURE: bool = False
    COOKIE_SAMESITE: str = "lax"
    ADMIN_EMAILS: str = ""
    STORAGE_BACKEND: str = "local"
    STORAGE_ENDPOINT: str = ""
    STORAGE_BUCKET: str = ""
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_REGION: str = "us-east-1"
    LOCAL_STORAGE_PATH: str = ".private_storage"
    MAX_VIDEO_SIZE_MB: int = 100
    MAX_PDF_SIZE_MB: int = 20
    MAX_HTML_SIZE_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        extra="ignore",
    )


settings = Settings()