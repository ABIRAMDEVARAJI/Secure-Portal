from fastapi import FastAPI
from sqlalchemy import text

from app.database.database import engine
from app.models.user import User
from app.models.content import Content

app = FastAPI(
    title="Secure Content Portal API",
    version="1.0.0"
)


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

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }