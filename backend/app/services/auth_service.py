from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config.settings import settings
from app.models.user import User, UserRole, UserSession
from app.utils.security import create_session_token, hash_session_token


def admin_email_set() -> set[str]:
    return {email.strip().lower() for email in settings.ADMIN_EMAILS.split(",") if email.strip()}


def upsert_google_user(db: Session, profile: dict) -> User:
    google_id = str(profile["sub"])
    email = str(profile["email"]).strip().lower()
    user = db.scalar(select(User).where(User.google_id == google_id))
    if user is None:
        user = db.scalar(select(User).where(User.email == email))
    role = UserRole.ADMIN if email in admin_email_set() else UserRole.VIEWER
    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            name=str(profile.get("name") or email),
            profile_picture=profile.get("picture"),
            role=role,
        )
        db.add(user)
    else:
        user.google_id = google_id
        user.email = email
        user.name = str(profile.get("name") or user.name)
        user.profile_picture = profile.get("picture")
        if email in admin_email_set():
            user.role = UserRole.ADMIN
    db.commit()
    db.refresh(user)
    return user


def create_user_session(db: Session, user: User) -> str:
    token = create_session_token()
    db.add(UserSession(
        user_id=user.id,
        token_hash=hash_session_token(token),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.SESSION_MAX_AGE_SECONDS),
    ))
    db.commit()
    return token


def delete_user_session(db: Session, token: str | None) -> None:
    if token:
        db.execute(delete(UserSession).where(UserSession.token_hash == hash_session_token(token)))
        db.commit()