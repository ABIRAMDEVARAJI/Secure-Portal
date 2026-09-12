from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.database.database import get_db
from app.models.user import User, UserRole, UserSession
from app.utils.security import hash_session_token


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    session = db.scalar(select(UserSession).where(UserSession.token_hash == hash_session_token(token)))
    if session is None or session.expires_at <= datetime.now(timezone.utc):
        if session:
            db.execute(delete(UserSession).where(UserSession.id == session.id))
            db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrator access required")
    return user


def validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin.rstrip("/") != settings.FRONTEND_URL.rstrip("/"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid request origin")