from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import text

from app.config.settings import settings
from app.database.database import engine
from app.middleware.security import SecurityHeadersMiddleware
from app.models.user import User
from app.models.content import Content
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.content import router as content_router

app = FastAPI(
    title="Secure Content Portal API",
    version="1.0.0"
)
logger = logging.getLogger(__name__)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Range"],
)
app.include_router(auth_router)
app.include_router(content_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "message": "Secure Content Portal API is running"
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception:
        logger.exception("Database health check failed")
        return {
            "status": "unhealthy",
            "database": "disconnected",
        }